from virallab.semantic_analyzer import NarrativeBlock, SemanticAnalysis, TranscriptSegment
from virallab.timeline_builder import build_multimodal_timeline
from virallab.visual_analyzer import VisualAnalysis, VisualMoment


def test_build_multimodal_timeline_aligns_speech_and_visual_role():
    semantic = SemanticAnalysis(
        language="pt",
        transcript="Você sabia? Veja a explicação. Siga para mais.",
        segments=[
            TranscriptSegment(0.0, 2.0, "Você sabia?"),
            TranscriptSegment(2.0, 8.0, "Veja a explicação."),
            TranscriptSegment(8.0, 10.0, "Siga para mais."),
        ],
        hook_text="Você sabia?",
        hook_score=80,
        cta_text="Siga para mais.",
        cta_score=85,
        words_per_minute=120,
        narrative_blocks=[
            NarrativeBlock("Hook", 0.0, 2.0, "Você sabia?"),
            NarrativeBlock("Desenvolvimento", 2.0, 8.0, "Veja a explicação."),
            NarrativeBlock("Conclusão e CTA", 8.0, 10.0, "Siga para mais."),
        ],
        summary="",
        strengths=[],
        improvements=[],
    )
    moments = [
        VisualMoment(0.0, 2.0, "hook.jpg", 1, 0.2, 120, 90, 0.02, None, "close-up", "Hook visual"),
        VisualMoment(2.0, 8.0, "broll.jpg", 0, 0.0, 110, 80, 0.10, "Evidência", "sem rosto", "Tela de apoio ou evidência"),
        VisualMoment(8.0, 10.0, "cta.jpg", 1, 0.1, 120, 90, 0.05, None, "plano médio", "Fechamento/CTA"),
    ]
    visual = VisualAnalysis(
        moments=moments,
        face_presence_ratio=0.66,
        text_presence_ratio=0.33,
        average_brightness=116,
        average_sharpness=86,
        framing_changes=2,
        dominant_shot_type="plano médio",
        key_frame_paths=[item.frame_path for item in moments],
        summary="",
        strengths=[],
        improvements=[],
    )

    timeline = build_multimodal_timeline(semantic, visual)

    assert len(timeline) == 3
    assert timeline[0].narrative_label == "Hook"
    assert timeline[0].speech == "Você sabia?"
    assert timeline[1].on_screen_text == "Evidência"
    assert timeline[2].narrative_label == "Conclusão e CTA"
