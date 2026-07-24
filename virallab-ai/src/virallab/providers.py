from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Protocol

from .gemini_client import GeminiAPIError, configured_model, generate_json, get_api_key
from .models import VideoBrief


class ScriptProvider(Protocol):
    name: str

    def generate(self, brief: VideoBrief) -> dict[str, str]:
        """Return at least hook, thesis and caption keys."""


class LocalRuleProvider:
    """Deterministic fallback that works without network access or API keys."""

    name = "local_rules"

    def generate(self, brief: VideoBrief) -> dict[str, str]:
        theme = brief.theme.strip().rstrip(".?!")
        hook = f"A verdade sobre {theme} que quase ninguém explica."
        thesis = (
            f"{theme.capitalize()} só gera valor quando amplia o raciocínio humano, "
            "sem substituir responsabilidade, julgamento e revisão crítica."
        )
        caption = (
            f"{thesis}\n\n"
            "Tecnologia útil não elimina conhecimento: aumenta a capacidade de quem sabe "
            "perguntar, avaliar e decidir.\n\n"
            f"{brief.cta}"
        )
        return {"hook": hook, "thesis": thesis, "caption": caption}


class GeminiProvider:
    """Gemini provider using the shared resilient REST client."""

    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key.strip()
        self.model = model or configured_model()
        if not get_api_key():
            raise ValueError("GEMINI_API_KEY não configurada.")

    def generate(self, brief: VideoBrief) -> dict[str, str]:
        try:
            data, used_model = generate_json(
                _build_prompt(brief),
                model=self.model,
                temperature=0.7,
                timeout=60,
            )
        except GeminiAPIError as exc:
            raise RuntimeError(f"Falha ao consultar Gemini: {exc}") from exc

        required = {"hook", "thesis", "caption"}
        missing = required.difference(data)
        if missing:
            raise RuntimeError(f"Gemini não retornou campos obrigatórios: {sorted(missing)}")

        self.model = used_model
        return {key: str(data[key]).strip() for key in required}


def select_provider(name: str = "auto") -> ScriptProvider:
    normalized = name.strip().lower()
    if normalized == "local":
        return LocalRuleProvider()
    if normalized == "gemini":
        return GeminiProvider()
    if normalized != "auto":
        raise ValueError(f"Provedor desconhecido: {name}")

    if get_api_key():
        try:
            return GeminiProvider()
        except ValueError:
            pass
    return LocalRuleProvider()


def _build_prompt(brief: VideoBrief) -> str:
    brief_json = json.dumps(asdict(brief), ensure_ascii=False, indent=2)
    return f"""
Você é o roteirista-chefe do ViralLab AI. Crie conteúdo original, direto e confiável.
Não copie frases de vídeos de referência. Não invente evidências, números ou fontes.
O hook deve ser forte, mas não sensacionalista. A tese deve caber em uma fala curta.
A legenda deve aprofundar a tese e terminar exatamente com o CTA informado.

BRIEF:
{brief_json}

Retorne somente JSON válido com esta estrutura:
{{
  "hook": "...",
  "thesis": "...",
  "caption": "..."
}}
""".strip()
