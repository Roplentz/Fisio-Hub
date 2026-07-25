from __future__ import annotations

from virallab.learning import (
    FeedbackRecord,
    load_feedback,
    save_feedback,
    summarize_preferences,
)


def test_feedback_store_appends_and_summarizes(tmp_path):
    store = tmp_path / "learning" / "feedback.jsonl"

    save_feedback(
        FeedbackRecord(
            project_id="abc123",
            theme="IA na fisioterapia",
            rating=9,
            approved=True,
            original_hook="Hook A",
            preferred_hook="Hook B",
            preferred_style="Professor Cinemático",
        ),
        store,
    )
    save_feedback(
        FeedbackRecord(
            project_id="def456",
            theme="Inovação em saúde",
            rating=7,
            approved=False,
            original_hook="Hook C",
            preferred_hook="Hook D",
            preferred_style="Mais científico",
        ),
        store,
    )

    records = load_feedback(store)
    summary = summarize_preferences(records)

    assert len(records) == 2
    assert summary["total_feedback"] == 2
    assert summary["approval_rate"] == 50.0
    assert summary["average_rating"] == 8.0
    assert summary["preferred_styles"] == ["Professor Cinemático", "Mais científico"]
