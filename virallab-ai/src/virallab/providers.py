from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Any, Protocol

from .gemini_client import GeminiAPIError, configured_model, generate_json, get_api_key
from .models import VideoBrief


class ScriptProvider(Protocol):
    name: str

    def generate(self, brief: VideoBrief) -> dict[str, Any]:
        """Return hook, thesis, caption and optionally a complete scene plan."""


class LocalRuleProvider:
    """Deterministic fallback that works without network access or API keys."""

    name = "local_rules"

    def generate(self, brief: VideoBrief) -> dict[str, Any]:
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
        return {
            "hook": hook,
            "thesis": thesis,
            "caption": caption,
            "provider_notice": "Versão local gerada porque o serviço de IA não estava disponível.",
        }


class GeminiProvider:
    """Gemini provider using the shared resilient REST client."""

    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key.strip()
        self.model = model or configured_model()
        if not get_api_key():
            raise ValueError("GEMINI_API_KEY não configurada.")

    def generate(self, brief: VideoBrief) -> dict[str, Any]:
        _attach_session_reference_dna(brief)
        try:
            data, used_model = generate_json(
                _build_prompt(brief),
                model=self.model,
                temperature=None,
                timeout=90,
            )
        except GeminiAPIError as exc:
            raise RuntimeError(f"Falha ao consultar Gemini: {exc}") from exc

        required = {"hook", "thesis", "caption"}
        missing = required.difference(data)
        if missing:
            raise RuntimeError(f"Gemini não retornou campos obrigatórios: {sorted(missing)}")

        self.model = used_model
        result: dict[str, Any] = {
            "hook": str(data["hook"]).strip(),
            "thesis": str(data["thesis"]).strip(),
            "caption": str(data["caption"]).strip(),
            "provider_model": used_model,
        }
        if isinstance(data.get("scenes"), list):
            result["scenes"] = data["scenes"]
        if isinstance(data.get("creative_rationale"), str):
            result["creative_rationale"] = data["creative_rationale"].strip()
        return result


class AutoFallbackProvider:
    """Prefer Gemini, but never block the creator when the service is unavailable."""

    name = "auto"

    def generate(self, brief: VideoBrief) -> dict[str, Any]:
        if get_api_key():
            try:
                result = GeminiProvider().generate(brief)
                self.name = f"gemini:{result.get('provider_model', configured_model())}"
                return result
            except (RuntimeError, ValueError) as exc:
                result = LocalRuleProvider().generate(brief)
                result["provider_notice"] = (
                    "O serviço de IA está temporariamente indisponível. "
                    "O ViralLab gerou uma versão local para você continuar trabalhando."
                )
                result["provider_error"] = str(exc)[:500]
                self.name = "local_fallback"
                return result

        self.name = "local_rules"
        return LocalRuleProvider().generate(brief)


def _attach_session_reference_dna(brief: VideoBrief) -> None:
    """Use the latest Streamlit editorial analysis without coupling core models to UI code."""
    if brief.reference_dna:
        return
    try:
        import streamlit as st

        editorial = st.session_state.get("editorial_analysis")
        if editorial is not None and hasattr(editorial, "to_dict"):
            data = editorial.to_dict()
            brief.reference_dna = {
                "thesis": data.get("thesis"),
                "promise": data.get("promise"),
                "target_audience": data.get("target_audience"),
                "attention_mechanism": data.get("attention_mechanism"),
                "hook_type": data.get("hook_type"),
                "retention_risks": data.get("retention_risks", []),
                "specific_recommendations": data.get("specific_recommendations", []),
                "reusable_formula": data.get("reusable_formula", []),
                "priority_action": data.get("priority_action"),
                "emotional_drivers": data.get("emotional_drivers", []),
                "narrative_structure": data.get("narrative_structure", []),
            }
    except Exception:
        return


def select_provider(name: str = "auto") -> ScriptProvider:
    normalized = name.strip().lower()
    if normalized == "local":
        return LocalRuleProvider()
    if normalized == "gemini":
        return GeminiProvider()
    if normalized == "auto":
        return AutoFallbackProvider()
    raise ValueError(f"Provedor desconhecido: {name}")


def _build_prompt(brief: VideoBrief) -> str:
    brief_json = json.dumps(asdict(brief), ensure_ascii=False, indent=2)
    style_rules = {
        "professor_rp": "voz de professor experiente, humana, direta, confiável e provocativa; autoridade sem arrogância",
        "viral": "mais tensão, curiosidade, frases curtas e alto potencial de retenção, sem sensacionalismo",
        "conservadora": "tom sóbrio, didático, seguro e científico, com menor intensidade emocional",
    }
    style = style_rules.get(brief.creative_style, style_rules["professor_rp"])
    return f"""
Você é o diretor criativo e roteirista-chefe do RP ViralLab.
Crie um vídeo TOTALMENTE ORIGINAL a partir do tema informado, usando apenas a ARQUITETURA do DNA editorial da referência.
Não copie frases, exemplos, nomes, listas ou conteúdo específico do vídeo analisado.
Não invente evidências, números, resultados clínicos ou fontes.

ESTILO ESCOLHIDO:
{style}

REGRAS OBRIGATÓRIAS:
- O hook deve ter no máximo 22 palavras e funcionar falado nos primeiros 3 segundos.
- Evite linguagem genérica de IA, clichês e frases excessivamente longas.
- A tese deve ser clara, defensável e natural na voz do Professor RP.
- Cada cena deve cumprir uma função narrativa distinta.
- Use o DNA da referência: fórmula, mecanismo de atenção, riscos de retenção e recomendações.
- Corrija explicitamente as fragilidades encontradas na referência.
- Inclua mudanças visuais motivadas pelo conteúdo, não apenas decorativas.
- Termine exatamente com o CTA informado.
- Narração total compatível com a duração solicitada.

BRIEF E DNA EDITORIAL:
{brief_json}

Retorne SOMENTE JSON válido nesta estrutura:
{{
  "hook": "frase curta e forte",
  "thesis": "tese central em uma frase",
  "caption": "legenda original que termina exatamente com o CTA",
  "creative_rationale": "explique em até 80 palavras como o DNA da referência foi transformado",
  "scenes": [
    {{
      "scene_type": "title_card|avatar|broll|screen_capture|proof",
      "duration_seconds": 3.0,
      "narration": "fala natural",
      "on_screen_text": "texto curto",
      "visual_direction": "o que mostrar e por quê",
      "edit_direction": "ritmo, corte ou transição",
      "asset_query": "busca visual opcional"
    }}
  ]
}}
""".strip()
