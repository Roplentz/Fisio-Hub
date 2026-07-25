from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from .gemini_client import GeminiAPIError, configured_model, generate_json, get_api_key


class EditorialAnalysisError(RuntimeError):
    """Raised when the deep editorial analysis cannot be produced."""


@dataclass(slots=True)
class EditorialAnalysis:
    engine: str
    thesis: str
    promise: str
    target_audience: str
    attention_mechanism: str
    hook_type: str
    hook_diagnosis: str
    retention_diagnosis: str
    persuasion_diagnosis: str
    visual_diagnosis: str
    cta_diagnosis: str
    emotional_drivers: list[str]
    narrative_structure: list[dict[str, str]]
    retention_risks: list[dict[str, str]]
    specific_recommendations: list[dict[str, str]]
    reusable_formula: list[str]
    priority_action: str
    executive_summary: str
    content_score: int
    retention_score: int
    persuasion_score: int
    clarity_score: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def analyze_editorially(
    structural: Any, semantic: Any, visual: Any, timeline: list[Any]
) -> EditorialAnalysis:
    payload = _build_payload(structural, semantic, visual, timeline)
    if get_api_key():
        try:
            return _analyze_with_gemini(payload)
        except EditorialAnalysisError:
            # The app remains usable when the free API is unavailable or rate-limited.
            pass
    return _analyze_locally(payload)


def _build_payload(
    structural: Any, semantic: Any, visual: Any, timeline: list[Any]
) -> dict[str, Any]:
    moments = []
    for item in timeline:
        moments.append(
            {
                "start": round(float(getattr(item, "start", 0)), 2),
                "end": round(float(getattr(item, "end", 0)), 2),
                "speech": str(getattr(item, "speech", "")),
                "narrative_label": str(getattr(item, "narrative_label", "")),
                "visual_role": str(getattr(item, "visual_role", "")),
                "shot_type": str(getattr(item, "shot_type", "")),
                "face_present": bool(getattr(item, "face_present", False)),
                "on_screen_text": str(getattr(item, "on_screen_text", "")),
            }
        )
    return {
        "duration_seconds": float(getattr(structural, "duration_seconds", 0)),
        "estimated_scenes": int(getattr(structural, "estimated_scenes", 0)),
        "average_scene_seconds": float(getattr(structural, "average_scene_seconds", 0)),
        "pacing_score": int(getattr(structural, "pacing_score", 0)),
        "format_score": int(getattr(structural, "format_score", 0)),
        "transcript": str(getattr(semantic, "transcript", "")),
        "hook_text": str(getattr(semantic, "hook_text", "")),
        "cta_text": getattr(semantic, "cta_text", None),
        "words_per_minute": int(getattr(semantic, "words_per_minute", 0)),
        "face_presence_ratio": float(getattr(visual, "face_presence_ratio", 0)),
        "text_presence_ratio": float(getattr(visual, "text_presence_ratio", 0)),
        "framing_changes": int(getattr(visual, "framing_changes", 0)),
        "dominant_shot_type": str(getattr(visual, "dominant_shot_type", "")),
        "timeline": moments,
    }


def _analyze_with_gemini(payload: dict[str, Any]) -> EditorialAnalysis:
    try:
        data, used_model = generate_json(
            _editorial_prompt(payload),
            model=configured_model(),
            temperature=0.25,
            timeout=90,
        )
    except GeminiAPIError as exc:
        raise EditorialAnalysisError(f"Falha na inteligência editorial: {exc}") from exc
    return _from_dict(data, engine=f"gemini:{used_model}")


def _from_dict(data: dict[str, Any], engine: str) -> EditorialAnalysis:
    def text(name: str, default: str = "Não identificado com segurança.") -> str:
        return str(data.get(name) or default).strip()

    def score(name: str, default: int = 50) -> int:
        try:
            return max(0, min(100, int(data.get(name, default))))
        except (TypeError, ValueError):
            return default

    return EditorialAnalysis(
        engine=engine,
        thesis=text("thesis"),
        promise=text("promise"),
        target_audience=text("target_audience"),
        attention_mechanism=text("attention_mechanism"),
        hook_type=text("hook_type"),
        hook_diagnosis=text("hook_diagnosis"),
        retention_diagnosis=text("retention_diagnosis"),
        persuasion_diagnosis=text("persuasion_diagnosis"),
        visual_diagnosis=text("visual_diagnosis"),
        cta_diagnosis=text("cta_diagnosis"),
        emotional_drivers=[str(x) for x in data.get("emotional_drivers", [])][:6],
        narrative_structure=[
            dict(x) for x in data.get("narrative_structure", []) if isinstance(x, dict)
        ][:10],
        retention_risks=[
            dict(x) for x in data.get("retention_risks", []) if isinstance(x, dict)
        ][:8],
        specific_recommendations=[
            dict(x)
            for x in data.get("specific_recommendations", [])
            if isinstance(x, dict)
        ][:10],
        reusable_formula=[str(x) for x in data.get("reusable_formula", [])][:10],
        priority_action=text("priority_action"),
        executive_summary=text("executive_summary"),
        content_score=score("content_score"),
        retention_score=score("retention_score"),
        persuasion_score=score("persuasion_score"),
        clarity_score=score("clarity_score"),
    )


def _analyze_locally(payload: dict[str, Any]) -> EditorialAnalysis:
    transcript = re.sub(r"\s+", " ", payload["transcript"]).strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", transcript) if s.strip()]
    opening = payload["hook_text"] or (sentences[0] if sentences else "")
    thesis = sentences[1] if len(sentences) > 1 else opening
    promise = _infer_promise(opening, transcript)
    duration = payload["duration_seconds"]
    avg_scene = payload["average_scene_seconds"]
    face = payload["face_presence_ratio"]
    framing_changes = payload["framing_changes"]
    cta = payload["cta_text"]

    risks: list[dict[str, str]] = []
    if avg_scene > 5:
        risks.append(
            {
                "moment": "Ao longo do vídeo",
                "risk": "Planos longos podem reduzir a renovação visual.",
                "why": f"A média estimada é de {avg_scene:.1f}s por cena.",
            }
        )
    if duration > 90:
        risks.append(
            {
                "moment": "Metade final",
                "risk": "Conteúdo longo para consumo vertical sem marcos de progressão claros.",
                "why": "Vídeos longos precisam reabrir ciclos de curiosidade.",
            }
        )
    if face > 0.75 and framing_changes < 4:
        risks.append(
            {
                "moment": "Desenvolvimento",
                "risk": "Excesso de talking head no mesmo plano.",
                "why": "A presença humana ajuda, mas sem alternância visual pode gerar monotonia.",
            }
        )
    if not cta:
        risks.append(
            {
                "moment": "Encerramento",
                "risk": "Ausência de próximo passo explícito.",
                "why": "O público pode compreender o conteúdo e ainda assim não agir.",
            }
        )

    recs = [
        {
            "moment": "0–3s",
            "action": "Transformar a promessa inicial em uma frase visual curta e específica.",
            "reason": "O início precisa comunicar benefício e tensão antes de qualquer contexto.",
        },
        {
            "moment": "A cada nova ideia",
            "action": "Alternar rosto, captura de tela, palavra-chave e exemplo concreto.",
            "reason": "A mudança deve acompanhar a progressão lógica, não apenas decorar o vídeo.",
        },
        {
            "moment": "Após 30–45s",
            "action": "Inserir uma nova pergunta, contraste ou micro-promessa.",
            "reason": "Isso reabre a curiosidade em conteúdos mais longos.",
        },
    ]
    if not cta:
        recs.append(
            {
                "moment": "Últimos 5s",
                "action": "Adicionar um CTA único ligado ao valor entregue.",
                "reason": "Um próximo passo específico converte atenção em comportamento.",
            }
        )

    formula = [
        "Contraste ou promessa específica",
        "Nomeação do problema",
        "Redução da complexidade",
        "Sequência prática",
        "Exemplo ou demonstração",
        "Síntese",
        "CTA coerente",
    ]
    content_score = min(
        100, max(35, round((payload["format_score"] + 70 + (80 if thesis else 45)) / 3))
    )
    retention_score = min(
        100,
        max(
            20,
            round(
                (
                    payload["pacing_score"]
                    + (80 if avg_scene <= 4 else 45)
                    + min(framing_changes * 8, 80)
                )
                / 3
            ),
        ),
    )
    persuasion_score = 68 if promise else 48
    if cta:
        persuasion_score += 10
    clarity_score = 75 if payload["words_per_minute"] <= 175 else 58

    return EditorialAnalysis(
        engine="local_editorial_fallback",
        thesis=thesis or "A tese não ficou explícita na transcrição.",
        promise=promise,
        target_audience="Público interessado no tema apresentado, não explicitado com precisão.",
        attention_mechanism=f"O vídeo abre com: “{opening[:180]}”. A força depende da combinação entre especificidade, benefício e curiosidade.",
        hook_type=_hook_type(opening),
        hook_diagnosis="O hook é verbalmente identificável, mas precisa ser julgado pelo valor concreto prometido e pela rapidez com que o vídeo começa a cumpri-lo.",
        retention_diagnosis=f"O conteúdo dura {duration:.0f}s, usa média de {avg_scene:.1f}s por cena e apresenta {framing_changes} mudanças de enquadramento. O principal risco é a perda de progressão visual e narrativa ao longo do desenvolvimento.",
        persuasion_diagnosis="A persuasão depende mais da utilidade percebida do que de urgência. O vídeo ganha força quando transforma afirmações em exemplos, demonstrações e consequências concretas.",
        visual_diagnosis=f"A presença facial estimada é de {face:.0%}. O rosto sustenta proximidade e autoridade, mas deve ser alternado com apoios visuais exatamente quando cada ideia é mencionada.",
        cta_diagnosis=f"CTA identificado: {cta}"
        if cta
        else "Não foi identificado um CTA claro no encerramento.",
        emotional_drivers=[
            "curiosidade",
            "redução de complexidade",
            "utilidade",
            "segurança",
        ],
        narrative_structure=_local_structure(payload),
        retention_risks=risks,
        specific_recommendations=recs,
        reusable_formula=formula,
        priority_action=recs[0]["action"],
        executive_summary="O vídeo tem uma ideia central reconhecível e um início potencialmente forte, mas precisa sincronizar melhor progressão verbal, provas e mudanças visuais. A prioridade é tornar a promessa mais específica e renovar a atenção em blocos previsíveis.",
        content_score=content_score,
        retention_score=retention_score,
        persuasion_score=min(100, persuasion_score),
        clarity_score=clarity_score,
    )


def _infer_promise(opening: str, transcript: str) -> str:
    text = f"{opening} {transcript[:700]}".lower()
    if any(token in text for token in ("como", "passo", "maneira", "forma")):
        return "Ensinar um caminho mais simples ou prático para alcançar um resultado desejado."
    if any(token in text for token in ("erro", "nunca", "verdade", "mito")):
        return "Corrigir uma crença ou evitar um erro relevante para o público."
    if any(ch.isdigit() for ch in opening):
        return "Entregar uma seleção objetiva e reduzir a complexidade por meio de uma promessa quantificada."
    return "Entregar compreensão ou utilidade prática sobre o tema apresentado."


def _hook_type(opening: str) -> str:
    lowered = opening.lower()
    if any(ch.isdigit() for ch in opening):
        return "Contraste ou promessa numérica"
    if "?" in opening:
        return "Pergunta de curiosidade"
    if any(token in lowered for token in ("erro", "nunca", "verdade", "mito")):
        return "Ruptura de crença"
    return "Promessa direta"


def _local_structure(payload: dict[str, Any]) -> list[dict[str, str]]:
    timeline = payload["timeline"]
    if timeline:
        return [
            {
                "time": f"{x['start']:.0f}–{x['end']:.0f}s",
                "function": x["narrative_label"] or "Desenvolvimento",
                "content": x["speech"][:220],
                "visual": x["visual_role"] or x["shot_type"],
            }
            for x in timeline[:8]
        ]
    duration = payload["duration_seconds"]
    return [
        {
            "time": f"0–{max(3, round(duration * 0.08))}s",
            "function": "Hook",
            "content": payload["hook_text"],
            "visual": "Abrir com mudança ou texto de impacto",
        },
        {
            "time": f"{round(duration * 0.08)}–{round(duration * 0.7)}s",
            "function": "Desenvolvimento",
            "content": "Explicação principal",
            "visual": "Alternar rosto e evidências",
        },
        {
            "time": f"{round(duration * 0.7)}–{round(duration)}s",
            "function": "Síntese e CTA",
            "content": payload["cta_text"] or "Encerramento sem CTA explícito",
            "visual": "Retorno ao apresentador",
        },
    ]


def _editorial_prompt(payload: dict[str, Any]) -> str:
    source = json.dumps(payload, ensure_ascii=False, indent=2)
    return f"""
Você é um estrategista editorial sênior especializado em vídeos curtos, educação, persuasão e retenção.
Analise o conteúdo abaixo de forma profunda, concreta e contextual. Não repita métricas mecanicamente.
Toda conclusão deve ser sustentada pela transcrição ou pelo mapa temporal. Quando não houver evidência, diga que não é possível concluir.
Não invente alcance, retenção real, intenção do autor ou dados de plataforma.

DADOS DO VÍDEO:
{source}

Retorne SOMENTE JSON válido com:
{{
  "thesis": "tese central em uma frase",
  "promise": "benefício ou transformação prometida",
  "target_audience": "público inferido e sinais usados",
  "attention_mechanism": "por que o início cria ou não atenção",
  "hook_type": "tipo de hook",
  "hook_diagnosis": "forças, falhas e grau de cumprimento da promessa",
  "retention_diagnosis": "progressão, monotonia, reabertura de curiosidade e pontos de abandono prováveis",
  "persuasion_diagnosis": "autoridade, prova, especificidade, utilidade e confiança",
  "visual_diagnosis": "como imagem, rosto, texto e cortes sustentam ou prejudicam o significado",
  "cta_diagnosis": "clareza, coerência e força do próximo passo",
  "emotional_drivers": ["..."],
  "narrative_structure": [{{"time":"0–3s","function":"...","content":"...","visual":"..."}}],
  "retention_risks": [{{"moment":"...","risk":"...","why":"..."}}],
  "specific_recommendations": [{{"moment":"...","action":"...","reason":"..."}}],
  "reusable_formula": ["etapa 1", "etapa 2"],
  "priority_action": "a melhoria única de maior impacto",
  "executive_summary": "síntese editorial em até 120 palavras",
  "content_score": 0,
  "retention_score": 0,
  "persuasion_score": 0,
  "clarity_score": 0
}}
""".strip()
