from __future__ import annotations

from dataclasses import asdict, dataclass

from .semantic_analyzer import SemanticAnalysis
from .visual_analyzer import VisualAnalysis


@dataclass(slots=True)
class TimelineItem:
    start: float
    end: float
    narrative_label: str
    speech: str
    visual_role: str
    shot_type: str
    face_present: bool
    on_screen_text: str | None
    recommendation: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _overlap(start_a: float, end_a: float, start_b: float, end_b: float) -> float:
    return max(0.0, min(end_a, end_b) - max(start_a, start_b))


def build_multimodal_timeline(
    semantic: SemanticAnalysis,
    visual: VisualAnalysis,
) -> list[TimelineItem]:
    items: list[TimelineItem] = []
    for moment in visual.moments:
        narrative = max(
            semantic.narrative_blocks,
            key=lambda block: _overlap(moment.start, moment.end, block.start, block.end),
            default=None,
        )
        speech_segments = [
            segment.text
            for segment in semantic.segments
            if _overlap(moment.start, moment.end, segment.start, segment.end) > 0
        ]
        speech = " ".join(speech_segments).strip()
        label = narrative.label if narrative else "Trecho"

        if moment.visual_role == "Apresentação principal" and not speech:
            recommendation = "Evitar trecho longo com apresentador sem fala; inserir narração, corte ou apoio visual."
        elif moment.visual_role in {"B-roll ou demonstração", "Tela de apoio ou evidência"} and speech:
            recommendation = "Boa oportunidade de sincronizar o apoio visual com a ideia verbal central."
        elif label == "Hook" and moment.text_density < 0.08 and not moment.detected_text:
            recommendation = "Reforçar o hook com uma frase curta e legível na tela."
        elif label == "Conclusão e CTA" and moment.face_count == 0:
            recommendation = "Considerar retornar ao apresentador no CTA para aumentar conexão e confiança."
        else:
            recommendation = "Manter a coerência entre fala, enquadramento e função narrativa."

        items.append(
            TimelineItem(
                start=moment.start,
                end=moment.end,
                narrative_label=label,
                speech=speech,
                visual_role=moment.visual_role,
                shot_type=moment.shot_type,
                face_present=moment.face_count > 0,
                on_screen_text=moment.detected_text,
                recommendation=recommendation,
            )
        )
    return items
