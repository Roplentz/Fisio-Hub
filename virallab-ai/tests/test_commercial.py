from __future__ import annotations

from decimal import Decimal

import pytest

from virallab.commercial import (
    CommercialLedger,
    InsufficientCredits,
    estimate_credits,
    get_plan,
)
from virallab.commercial_gate import reserve_render


def test_plan_catalog_has_clear_limits():
    free = get_plan("free")
    pro = get_plan("pro")

    assert free.commercial_use is False
    assert pro.commercial_use is True
    assert pro.priority_queue is True


def test_reservation_is_atomic_and_completable(tmp_path):
    ledger = CommercialLedger(tmp_path / "commercial.db")
    ledger.create_account("user-1", plan_id="creator", credits=20)

    event = ledger.reserve(
        "user-1",
        project_id="project-1",
        kind="image",
        estimated_cost_brl="0.25",
    )
    assert ledger.balance("user-1") == 16

    ledger.complete(event.event_id)
    history = ledger.usage_history("user-1")
    assert history[0].status == "completed"


def test_failed_operation_refunds_credits(tmp_path):
    ledger = CommercialLedger(tmp_path / "commercial.db")
    ledger.create_account("user-1", credits=20)
    event = ledger.reserve(
        "user-1",
        project_id="project-1",
        kind="render_minute",
        quantity=2,
    )

    assert ledger.balance("user-1") == 10
    ledger.fail_and_refund(event.event_id)
    assert ledger.balance("user-1") == 20
    assert ledger.usage_history("user-1")[0].status == "refunded"


def test_insufficient_balance_does_not_create_event(tmp_path):
    ledger = CommercialLedger(tmp_path / "commercial.db")
    ledger.create_account("user-1", credits=1)

    with pytest.raises(InsufficientCredits):
        ledger.reserve("user-1", project_id="p", kind="image")

    assert ledger.balance("user-1") == 1
    assert ledger.usage_history("user-1") == []


def test_render_context_completes_or_refunds(tmp_path):
    ledger = CommercialLedger(tmp_path / "commercial.db")
    ledger.create_account("user-1", credits=100)

    with reserve_render(
        ledger,
        account_id="user-1",
        project_id="project-1",
        duration_seconds=120,
        estimated_cost_brl=Decimal("1.50"),
    ):
        pass

    assert ledger.usage_history("user-1")[0].status == "completed"

    with pytest.raises(RuntimeError):
        with reserve_render(
            ledger,
            account_id="user-1",
            project_id="project-2",
            duration_seconds=60,
        ):
            raise RuntimeError("render failed")

    history = ledger.usage_history("user-1")
    assert history[0].status == "refunded"


def test_admin_metrics_are_aggregated_without_clinical_data(tmp_path):
    ledger = CommercialLedger(tmp_path / "commercial.db")
    ledger.create_account("user-1", credits=20)
    event = ledger.reserve(
        "user-1",
        project_id="anonymous-project",
        kind="script",
        estimated_cost_brl="0.10",
    )
    ledger.complete(event.event_id)

    metrics = ledger.admin_metrics()

    assert metrics == {
        "accounts": 1,
        "events": 1,
        "completed_events": 1,
        "credits_consumed": 1,
        "estimated_cost_brl": "0.10",
    }


def test_credit_estimation_rounds_consistently():
    assert estimate_credits("render_minute", Decimal("1.5")) == 8
