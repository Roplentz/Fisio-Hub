from __future__ import annotations

from virallab.models import Scene, VideoBrief, VideoPackage
from virallab.project_store import package_from_dict
from virallab.semantic_analyzer import TranscriptSegment, analyze_transcript


def test_package_roundtrip_stays_loadable() -> None:
    package = VideoPackage(
        brief=VideoBrief(theme="IA na fisioterapia"),
        hook="Hook de teste",
        thesis="Tese de teste",
        scenes=[
            Scene(
                index=1,
                start=0.0,
                end=3.0,
                scene_type="avatar",
                narration="Teste de narração.",
                on_screen_text="Texto",
                visual_direction="Plano médio.",
            )
        ],
    )

    restored = package_from_dict(package.to_dict())

    assert restored.brief.theme == package.brief.theme
    assert restored.scenes[0].narration == "Teste de narração."


def test_transcript_analysis_handles_normal_segments() -> None:
    analysis = analyze_transcript(
        [
            TranscriptSegment(0.0, 2.0, "Você sabia que a IA pode reduzir tarefas repetitivas?"),
            TranscriptSegment(2.0, 6.0, "Ela ajuda a organizar informações sem substituir o julgamento clínico."),
            TranscriptSegment(6.0, 8.0, "Siga para aprender mais."),
        ]
    )

    assert analysis.hook_score > 0
    assert analysis.cta_text == "Siga para aprender mais."
    assert analysis.words_per_minute > 0
