from __future__ import annotations

import pytest

from virallab.semantic_analyzer import (
    SemanticAnalysisError,
    TranscriptSegment,
    _collect_segments,
    analyze_transcript,
    unavailable_semantic_analysis,
)


def test_unavailable_semantic_analysis_is_valid_partial_result() -> None:
    result = unavailable_semantic_analysis("falha simulada")
    assert result.available is False
    assert result.warning == "falha simulada"
    assert result.segments == []
    assert result.to_srt() == ""


def test_analyze_transcript_builds_expected_metrics() -> None:
    result = analyze_transcript(
        [
            TranscriptSegment(0.0, 2.5, "Você sabe por que isso importa?"),
            TranscriptSegment(2.5, 7.0, "Aqui está uma explicação simples."),
            TranscriptSegment(7.0, 10.0, "Siga para aprender mais."),
        ]
    )
    assert result.available is True
    assert result.hook_score > 50
    assert result.cta_text is not None
    assert result.words_per_minute > 0


def test_collect_segments_converts_iterator_failure_to_domain_error() -> None:
    class BrokenIterator:
        def __iter__(self):
            yield type("Segment", (), {"start": 0.0, "end": 1.0, "text": "Olá"})()
            raise IndexError("tuple index out of range")

    with pytest.raises(SemanticAnalysisError, match="interrompeu a leitura"):
        _collect_segments(BrokenIterator())
