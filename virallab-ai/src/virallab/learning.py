from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class FeedbackRecord:
    project_id: str
    theme: str
    rating: int
    approved: bool
    original_hook: str
    preferred_hook: str
    notes: str = ""
    preferred_style: str = ""
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at or datetime.now(timezone.utc).isoformat()
        return data


def save_feedback(record: FeedbackRecord, store_path: str | Path) -> Path:
    """Acrescenta feedback em JSONL sem sobrescrever aprendizados anteriores."""
    path = Path(store_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
    return path


def load_feedback(store_path: str | Path) -> list[dict[str, Any]]:
    path = Path(store_path)
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def summarize_preferences(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {
            "total_feedback": 0,
            "approval_rate": 0.0,
            "average_rating": 0.0,
            "preferred_styles": [],
        }

    approved = sum(bool(item.get("approved")) for item in records)
    ratings = [int(item.get("rating", 0)) for item in records if item.get("rating")]
    styles: dict[str, int] = {}
    for item in records:
        style = str(item.get("preferred_style", "")).strip()
        if style:
            styles[style] = styles.get(style, 0) + 1

    return {
        "total_feedback": len(records),
        "approval_rate": round(approved / len(records) * 100, 1),
        "average_rating": round(sum(ratings) / len(ratings), 1) if ratings else 0.0,
        "preferred_styles": sorted(styles, key=styles.get, reverse=True),
    }
