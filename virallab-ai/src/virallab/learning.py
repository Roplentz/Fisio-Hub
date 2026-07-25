from __future__ import annotations

import json
import math
import re
from collections import Counter
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


def build_learning_profile(
    records: list[dict[str, Any]],
    *,
    theme: str = "",
    max_examples: int = 5,
) -> dict[str, Any]:
    """Consolida feedbacks em um perfil editorial auditável e reversível.

    O mecanismo não treina um modelo ocultamente. Ele seleciona exemplos aprovados,
    resume preferências e injeta esse contexto na próxima geração.
    """
    usable = [item for item in records if _is_learning_signal(item)]
    if not usable:
        return {
            "version": "1.0",
            "examples_used": 0,
            "preferred_styles": [],
            "preferred_hooks": [],
            "guidelines": [],
            "source_project_ids": [],
        }

    ranked = sorted(
        usable,
        key=lambda item: _learning_weight(item, theme),
        reverse=True,
    )[:max_examples]

    style_scores: Counter[str] = Counter()
    guidelines: list[str] = []
    hooks: list[str] = []
    source_ids: list[str] = []

    for item in ranked:
        weight = max(1, round(_learning_weight(item, theme) * 10))
        style = str(item.get("preferred_style", "")).strip()
        if style:
            style_scores[style] += weight

        preferred_hook = str(item.get("preferred_hook", "")).strip()
        original_hook = str(item.get("original_hook", "")).strip()
        if preferred_hook and preferred_hook != original_hook and preferred_hook not in hooks:
            hooks.append(preferred_hook)

        note = _clean_instruction(str(item.get("notes", "")))
        if note and note not in guidelines:
            guidelines.append(note)

        project_id = str(item.get("project_id", "")).strip()
        if project_id and project_id not in source_ids:
            source_ids.append(project_id)

    return {
        "version": "1.0",
        "examples_used": len(ranked),
        "preferred_styles": [name for name, _ in style_scores.most_common(3)],
        "preferred_hooks": hooks[:3],
        "guidelines": guidelines[:6],
        "source_project_ids": source_ids,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def learning_prompt(profile: dict[str, Any]) -> str:
    """Transforma o perfil em instruções curtas para o gerador."""
    if not profile or not profile.get("examples_used"):
        return "Nenhum aprendizado editorial consolidado ainda."

    lines = [
        f"Use {profile['examples_used']} exemplos editoriais aprovados como referência de estilo, nunca como texto para copiar.",
    ]
    styles = profile.get("preferred_styles") or []
    if styles:
        lines.append("Direções mais aprovadas: " + ", ".join(styles) + ".")
    guidelines = profile.get("guidelines") or []
    if guidelines:
        lines.append("Regras aprendidas: " + " | ".join(guidelines) + ".")
    hooks = profile.get("preferred_hooks") or []
    if hooks:
        lines.append("Padrões de hook aprovados, apenas para abstrair ritmo e intensidade: " + " | ".join(hooks) + ".")
    return "\n".join(lines)


def _is_learning_signal(item: dict[str, Any]) -> bool:
    rating = int(item.get("rating", 0) or 0)
    return bool(item.get("approved")) or rating >= 8


def _learning_weight(item: dict[str, Any], theme: str) -> float:
    rating = max(1, min(10, int(item.get("rating", 0) or 1))) / 10
    approval = 1.0 if item.get("approved") else 0.65
    relevance = _text_similarity(theme, str(item.get("theme", ""))) if theme else 0.5
    recency = _recency_score(str(item.get("created_at", "")))
    return rating * 0.45 + approval * 0.25 + relevance * 0.2 + recency * 0.1


def _text_similarity(left: str, right: str) -> float:
    a = set(_tokens(left))
    b = set(_tokens(right))
    if not a or not b:
        return 0.0
    return len(a & b) / math.sqrt(len(a) * len(b))


def _tokens(value: str) -> list[str]:
    stopwords = {"a", "o", "e", "de", "da", "do", "das", "dos", "em", "na", "no", "para", "com", "um", "uma"}
    return [token for token in re.findall(r"[a-záàâãéêíóôõúç0-9]+", value.lower()) if token not in stopwords and len(token) > 2]


def _recency_score(value: str) -> float:
    if not value:
        return 0.5
    try:
        created = datetime.fromisoformat(value.replace("Z", "+00:00"))
        age_days = max(0, (datetime.now(timezone.utc) - created.astimezone(timezone.utc)).days)
    except (ValueError, TypeError):
        return 0.5
    return max(0.1, 1.0 - min(age_days, 365) / 365)


def _clean_instruction(value: str) -> str:
    text = " ".join(value.split()).strip(" .")
    return text[:240]
