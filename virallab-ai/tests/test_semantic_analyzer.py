from virallab.semantic_analyzer import TranscriptSegment, analyze_transcript


def test_analyze_transcript_detects_hook_cta_and_builds_srt() -> None:
    result = analyze_transcript(
        [
            TranscriptSegment(
                0.0,
                3.0,
                "Você sabia que um erro simples pode reduzir o resultado do tratamento?",
            ),
            TranscriptSegment(
                3.0,
                10.0,
                "O problema é aplicar uma tecnologia sem compreender o mecanismo e o paciente.",
            ),
            TranscriptSegment(
                10.0,
                22.0,
                "Primeiro defina o objetivo, depois selecione os parâmetros e acompanhe a resposta clínica.",
            ),
            TranscriptSegment(
                22.0,
                29.0,
                "Salve este vídeo e siga para aprender fisioterapia baseada em evidências.",
            ),
        ],
        language="pt",
    )

    assert result.hook_score >= 70
    assert result.cta_text is not None
    assert result.cta_score >= 70
    assert result.words_per_minute > 0
    assert len(result.narrative_blocks) >= 3
    assert "00:00:00,000 --> 00:00:03,000" in result.to_srt()
    assert "Você sabia" in result.transcript
