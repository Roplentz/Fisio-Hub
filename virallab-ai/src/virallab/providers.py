from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Protocol

from .gemini_client import GeminiAPIError, configured_model, generate_json, get_api_key
from .learning import build_learning_profile, learning_prompt, load_feedback
from .models import VideoBrief


class ScriptProvider(Protocol):
    name: str

    def generate(self, brief: VideoBrief) -> dict[str, Any]:
        """Return hook, thesis, caption and optionally a complete scene plan."""


class LocalRuleProvider:
    name = "local_rules"

    def generate(self, brief: VideoBrief) -> dict[str, Any]:
        _attach_learning_profile(brief)
        theme = brief.theme.strip().rstrip(".?!")
        profile = brief.reference_dna.get("learning_profile", {})
        styles = profile.get("preferred_styles") or []
        if "Mais direto" in styles:
            hook = f"Você ainda perde tempo com {theme}? Existe uma forma mais inteligente de trabalhar."
        elif "Mais científico" in styles:
            hook = f"O que a evidência realmente permite afirmar sobre {theme}?"
        else:
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
            "learning_profile": profile,
            "provider_notice": "Versão local gerada porque o serviço de IA não estava disponível.",
        }


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key.strip()
        self.model = model or configured_model()
        if not get_api_key():
            raise ValueError("GEMINI_API_KEY não configurada.")

    def generate(self, brief: VideoBrief) -> dict[str, Any]:
        _attach_session_reference_dna(brief)
        _attach_learning_profile(brief)
        try:
            data, used_model = generate_json(
                _build_prompt(brief), model=self.model, temperature=None, timeout=90
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
            "learning_profile": brief.reference_dna.get("learning_profile", {}),
        }
        if isinstance(data.get("scenes"), list):
            result["scenes"] = data["scenes"]
        if isinstance(data.get("creative_rationale"), str):
            result["creative_rationale"] = data["creative_rationale"].strip()
        return result


class AutoFallbackProvider:
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
    try:
        import streamlit as st
        editorial = st.session_state.get("editorial_analysis")
        if editorial is not None and hasattr(editorial, "to_dict"):
            data = editorial.to_dict()
            brief.reference_dna.update({
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
            })
    except Exception:
        return


def _attach_learning_profile(brief: VideoBrief) -> None:
    explicit = os.getenv("VIRALLAB_LEARNING_STORE", "").strip()
    candidates = [Path(explicit)] if explicit else [
        Path("workspace/learning/feedback.jsonl"),
        Path(__file__).resolve().parents[2] / "workspace" / "learning" / "feedback.jsonl",
    ]
    records: list[dict[str, Any]] = []
    for path in candidates:
        records = load_feedback(path)
        if records:
            break
    brief.reference_dna["learning_profile"] = build_learning_profile(records, theme=brief.theme)


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
    learned_rules = learning_prompt(brief.reference_dna.get("learning_profile", {}))
    style_rules = {
        "professor_rp": "voz de professor experiente, humana, direta, confiável e provocativa; autoridade sem arrogância",
        "viral": "mais tensão, curiosidade, frases curtas e alto potencial de retenção, sem sensacionalismo",
        "conservadora": "tom sóbrio, didático, seguro e científico, com menor intensidade emocional",
    }
    style = style_rules.get(brief.creative_style, style_rules["professor_rp"])
    return f"""
Você é o diretor criativo e roteirista-chefe do RP ViralLab.
Crie um vídeo totalmente original a partir do tema informado.
Não copie texto de referências e não invente evidências, números ou fontes.

ESTILO ESCOLHIDO:
{style}

AUTOAPRENDIZADO DNA RP:
{learned_rules}
Use as preferências como orientação editorial, preservando precisão, ética e originalidade.

REGRAS:
- Hook com no máximo 22 palavras para os primeiros 3 segundos.
- Evite clichês, linguagem artificial e promessas absolutas.
- Tese clara, defensável e natural na voz do Professor RP.
- Cada cena deve cumprir uma função narrativa distinta.
- Corrija fragilidades identificadas na referência.
- Mudanças visuais devem ter função narrativa.
- Termine exatamente com o CTA informado.
- Narração compatível com a duração solicitada.

BRIEF E DNA EDITORIAL:
{brief_json}

Retorne somente JSON válido:
{{
  "hook": "frase curta e forte",
  "thesis": "tese central em uma frase",
  "caption": "legenda original que termina exatamente com o CTA",
  "creative_rationale": "até 80 palavras sobre as decisões criativas",
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
