from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class PronunciationEntry:
    term: str
    spoken_as: str
    locale: str = "pt-BR"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class PronunciationDictionary:
    """Dicionário explícito para TTS; nunca altera o roteiro exibido."""

    def __init__(self, entries: list[PronunciationEntry] | None = None) -> None:
        self.entries = list(entries or [])

    def add(self, term: str, spoken_as: str, *, locale: str = "pt-BR") -> None:
        clean_term = " ".join(term.split()).strip()
        clean_spoken = " ".join(spoken_as.split()).strip()
        if not clean_term or not clean_spoken:
            raise ValueError("Termo e pronúncia são obrigatórios.")
        if len(clean_term) > 120 or len(clean_spoken) > 240:
            raise ValueError("Entrada de pronúncia excede o limite.")
        self.entries = [
            item for item in self.entries
            if not (item.term.casefold() == clean_term.casefold() and item.locale == locale)
        ]
        self.entries.append(PronunciationEntry(clean_term, clean_spoken, locale))

    def apply(self, text: str, *, locale: str = "pt-BR") -> str:
        result = text
        matching = [item for item in self.entries if item.locale == locale]
        for item in sorted(matching, key=lambda value: len(value.term), reverse=True):
            result = re.sub(
                rf"\b{re.escape(item.term)}\b",
                item.spoken_as,
                result,
                flags=re.IGNORECASE,
            )
        return result

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {"version": "1.0", "entries": [item.to_dict() for item in self.entries]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return target

    @classmethod
    def load(cls, path: str | Path) -> "PronunciationDictionary":
        target = Path(path)
        if not target.is_file():
            return cls()
        try:
            payload = json.loads(target.read_text(encoding="utf-8"))
            return cls([PronunciationEntry(**item) for item in payload.get("entries", [])])
        except (json.JSONDecodeError, TypeError, ValueError):
            return cls()
