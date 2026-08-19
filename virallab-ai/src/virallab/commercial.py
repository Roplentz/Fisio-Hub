from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4


UsageKind = Literal["script", "image", "tts_minute", "render_minute"]
EventStatus = Literal["reserved", "completed", "refunded", "failed"]


@dataclass(frozen=True)
class Plan:
    plan_id: str
    name: str
    monthly_credits: int
    monthly_price_brl: Decimal
    max_projects: int
    commercial_use: bool
    priority_queue: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["monthly_price_brl"] = str(self.monthly_price_brl)
        return data


PLANS = {
    "free": Plan("free", "Explorar", 20, Decimal("0.00"), 3, False),
    "creator": Plan("creator", "Creator", 300, Decimal("97.00"), 30, True),
    "pro": Plan("pro", "Creator Pro", 1200, Decimal("297.00"), 200, True, True),
}


CREDIT_RATES: dict[UsageKind, Decimal] = {
    "script": Decimal("1"),
    "image": Decimal("4"),
    "tts_minute": Decimal("2"),
    "render_minute": Decimal("5"),
}


@dataclass(frozen=True)
class UsageEvent:
    event_id: str
    account_id: str
    project_id: str
    kind: UsageKind
    quantity: Decimal
    credits: int
    estimated_cost_brl: Decimal
    status: EventStatus
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["quantity"] = str(self.quantity)
        data["estimated_cost_brl"] = str(self.estimated_cost_brl)
        return data


class InsufficientCredits(RuntimeError):
    pass


class CommercialLedger:
    """Razão local transacional; não processa pagamentos nem guarda dados clínicos."""

    def __init__(self, database: str | Path) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def create_account(
        self,
        account_id: str,
        *,
        plan_id: str = "free",
        credits: int | None = None,
    ) -> None:
        plan = get_plan(plan_id)
        starting = plan.monthly_credits if credits is None else max(0, int(credits))
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO accounts(account_id, plan_id, credit_balance, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(account_id) DO NOTHING
                """,
                (account_id, plan_id, starting, _now()),
            )

    def balance(self, account_id: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT credit_balance FROM accounts WHERE account_id = ?",
                (account_id,),
            ).fetchone()
        if row is None:
            raise KeyError(account_id)
        return int(row[0])

    def reserve(
        self,
        account_id: str,
        *,
        project_id: str,
        kind: UsageKind,
        quantity: Decimal | int | float = Decimal("1"),
        estimated_cost_brl: Decimal | str = Decimal("0"),
    ) -> UsageEvent:
        amount = Decimal(str(quantity))
        if amount <= 0:
            raise ValueError("A quantidade deve ser positiva.")
        credits = estimate_credits(kind, amount)
        cost = Decimal(str(estimated_cost_brl)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        event = UsageEvent(
            event_id=f"usage_{uuid4().hex}",
            account_id=account_id,
            project_id=project_id,
            kind=kind,
            quantity=amount,
            credits=credits,
            estimated_cost_brl=cost,
            status="reserved",
            created_at=_now(),
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT credit_balance FROM accounts WHERE account_id = ?",
                (account_id,),
            ).fetchone()
            if row is None:
                raise KeyError(account_id)
            if int(row[0]) < credits:
                raise InsufficientCredits(
                    f"Saldo insuficiente: necessário {credits}, disponível {int(row[0])}."
                )
            connection.execute(
                "UPDATE accounts SET credit_balance = credit_balance - ? WHERE account_id = ?",
                (credits, account_id),
            )
            connection.execute(
                """
                INSERT INTO usage_events(
                    event_id, account_id, project_id, kind, quantity,
                    credits, estimated_cost_brl, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.account_id,
                    event.project_id,
                    event.kind,
                    str(event.quantity),
                    event.credits,
                    str(event.estimated_cost_brl),
                    event.status,
                    event.created_at,
                ),
            )
        return event

    def complete(self, event_id: str) -> None:
        self._transition(event_id, from_status="reserved", to_status="completed")

    def fail_and_refund(self, event_id: str) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT account_id, credits, status FROM usage_events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
            if row is None:
                raise KeyError(event_id)
            if row[2] != "reserved":
                raise ValueError("Somente reservas ativas podem ser reembolsadas.")
            connection.execute(
                "UPDATE usage_events SET status = 'refunded' WHERE event_id = ?",
                (event_id,),
            )
            connection.execute(
                "UPDATE accounts SET credit_balance = credit_balance + ? WHERE account_id = ?",
                (int(row[1]), str(row[0])),
            )

    def usage_history(self, account_id: str, *, limit: int = 100) -> list[UsageEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_id, account_id, project_id, kind, quantity, credits,
                       estimated_cost_brl, status, created_at
                FROM usage_events WHERE account_id = ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (account_id, min(max(limit, 1), 500)),
            ).fetchall()
        return [
            UsageEvent(
                event_id=row[0],
                account_id=row[1],
                project_id=row[2],
                kind=row[3],
                quantity=Decimal(row[4]),
                credits=int(row[5]),
                estimated_cost_brl=Decimal(row[6]),
                status=row[7],
                created_at=row[8],
            )
            for row in rows
        ]

    def admin_metrics(self) -> dict[str, Any]:
        with self._connect() as connection:
            accounts = connection.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
            events = connection.execute("SELECT COUNT(*) FROM usage_events").fetchone()[0]
            completed = connection.execute(
                "SELECT COUNT(*) FROM usage_events WHERE status = 'completed'"
            ).fetchone()[0]
            cost = connection.execute(
                "SELECT COALESCE(SUM(estimated_cost_brl), 0) FROM usage_events WHERE status = 'completed'"
            ).fetchone()[0]
            consumed = connection.execute(
                "SELECT COALESCE(SUM(credits), 0) FROM usage_events WHERE status = 'completed'"
            ).fetchone()[0]
        return {
            "accounts": int(accounts),
            "events": int(events),
            "completed_events": int(completed),
            "credits_consumed": int(consumed),
            "estimated_cost_brl": str(Decimal(str(cost)).quantize(Decimal("0.01"))),
        }

    def _transition(self, event_id: str, *, from_status: str, to_status: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE usage_events SET status = ? WHERE event_id = ? AND status = ?",
                (to_status, event_id, from_status),
            )
            if cursor.rowcount != 1:
                raise ValueError("Transição de uso inválida.")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=10)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS accounts(
                    account_id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    credit_balance INTEGER NOT NULL CHECK(credit_balance >= 0),
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS usage_events(
                    event_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL REFERENCES accounts(account_id),
                    project_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    quantity TEXT NOT NULL,
                    credits INTEGER NOT NULL CHECK(credits > 0),
                    estimated_cost_brl TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_usage_account_created
                ON usage_events(account_id, created_at DESC);
                """
            )


def get_plan(plan_id: str) -> Plan:
    try:
        return PLANS[plan_id]
    except KeyError as exc:
        raise ValueError(f"Plano desconhecido: {plan_id}") from exc


def estimate_credits(kind: UsageKind, quantity: Decimal | int | float) -> int:
    if kind not in CREDIT_RATES:
        raise ValueError(f"Tipo de uso desconhecido: {kind}")
    raw = CREDIT_RATES[kind] * Decimal(str(quantity))
    return max(1, int(raw.to_integral_value(rounding=ROUND_HALF_UP)))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
