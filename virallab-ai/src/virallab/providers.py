from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict
from typing import Protocol

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
    """Minimal Gemini REST adapter using only the Python standard library."""

    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model or os.getenv("VIRALLAB_GEMINI_MODEL", "gemini-2.5-flash")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não configurada.")

    def generate(self, brief: VideoBrief) -> dict[str, str]:
        prompt = _build_prompt(brief)
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.7,
            },
        }
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Falha ao consultar Gemini: {exc}") from exc

        try:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            data = json.loads(text)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Resposta inesperada do Gemini.") from exc

        required = {"hook", "thesis", "caption"}
        missing = required.difference(data)
        if missing:
            raise RuntimeError(f"Gemini não retornou campos obrigatórios: {sorted(missing)}")
        return {key: str(data[key]).strip() for key in required}


def select_provider(name: str = "auto") -> ScriptProvider:
    normalized = name.strip().lower()
    if normalized == "local":
        return LocalRuleProvider()
    if normalized == "gemini":
        return GeminiProvider()
    if normalized != "auto":
        raise ValueError(f"Provedor desconhecido: {name}")

    if os.getenv("GEMINI_API_KEY"):
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
