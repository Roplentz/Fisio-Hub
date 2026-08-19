from __future__ import annotations

import pytest

from virallab.commercial import CommercialLedger
from virallab.web_app import WebAppService, _duration


def service(tmp_path):
    ledger = CommercialLedger(tmp_path / "commercial.db")
    ledger.create_account("web-demo", plan_id="creator")
    return WebAppService(ledger, tmp_path / "projects")


def test_health_returns_real_ledger_balance(tmp_path):
    payload = service(tmp_path).health()
    assert payload["status"] == "ok"
    assert payload["balance"] == 300


def test_generate_uses_real_generator_clinical_review_and_credit(tmp_path):
    payload = service(tmp_path).generate(
        {
            "theme": "Mobilidade cervical no trabalho",
            "audience": "adultos",
            "objective": "educar",
            "duration_seconds": 30,
            "provider": "local",
        }
    )
    assert payload["package"]["brief"]["theme"] == "Mobilidade cervical no trabalho"
    assert payload["package"]["metadata"]["script_provider"] == "local_rules"
    assert payload["safety"]["human_review_required"] is True
    assert payload["balance"] == 299
    assert payload["credits_used"] == 1


def test_render_preview_charges_real_composite_cost(tmp_path, monkeypatch):
    app = service(tmp_path)
    generated = app.generate(
        {
            "theme": "Mobilidade cervical",
            "duration_seconds": 30,
            "provider": "local",
        }
    )

    class FakeRenderer:
        def render(self, job):
            output = app.project_dir(generated["project_id"]) / "video-final.mp4"
            output.write_bytes(b"fake-mp4")
            job.state = "succeeded"
            job.output_file = str(output)
            return job

    monkeypatch.setattr("virallab.web_app.get_video_renderer", lambda: FakeRenderer())
    payload = app.render_preview(
        {
            "project_id": generated["project_id"],
            "duration_seconds": 30,
            "safety_status": "pass",
        }
    )
    assert payload["status"] == "video_ready"
    assert payload["credits_used"] == 8
    assert payload["balance"] == 291
    assert payload["video_url"].endswith("/video-final.mp4")


def test_blocked_content_cannot_reach_preview(tmp_path):
    with pytest.raises(ValueError, match="bloqueado"):
        service(tmp_path).render_preview(
            {
                "project_id": "web_" + "a" * 32,
                "duration_seconds": 30,
                "safety_status": "block",
            }
        )


@pytest.mark.parametrize("value", [0, 15, 90, "abc"])
def test_duration_rejects_unsupported_values(value):
    with pytest.raises(ValueError):
        _duration(value)
