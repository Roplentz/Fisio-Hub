from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .commercial import CommercialLedger, UsageEvent


@dataclass
class UsageReservation:
    ledger: CommercialLedger
    event: UsageEvent
    finalized: bool = False

    def complete(self) -> None:
        if self.finalized:
            return
        self.ledger.complete(self.event.event_id)
        self.finalized = True

    def refund(self) -> None:
        if self.finalized:
            return
        self.ledger.fail_and_refund(self.event.event_id)
        self.finalized = True

    def __enter__(self) -> "UsageReservation":
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if exc_type is None:
            self.complete()
        else:
            self.refund()
        return False


def reserve_render(
    ledger: CommercialLedger,
    *,
    account_id: str,
    project_id: str,
    duration_seconds: float,
    estimated_cost_brl: Decimal | str = Decimal("0"),
) -> UsageReservation:
    minutes = max(Decimal("0.1"), Decimal(str(duration_seconds)) / Decimal("60"))
    event = ledger.reserve(
        account_id,
        project_id=project_id,
        kind="render_minute",
        quantity=minutes,
        estimated_cost_brl=estimated_cost_brl,
    )
    return UsageReservation(ledger, event)
