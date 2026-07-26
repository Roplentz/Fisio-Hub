from __future__ import annotations

from pathlib import Path

from virallab.neural_status import collect_neural_status


def test_collect_neural_status_without_workspace(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    status = collect_neural_status(tmp_path)

    assert status["total_count"] == len(status["services"])
    assert status["total_count"] == 7
    assert status["feedback_count"] == 0
    assert status["project_count"] == 0
    keys = {service["key"] for service in status["services"]}
    assert keys == {
        "gemini",
        "qwen",
        "embedding",
        "whisper",
        "dna",
        "render",
        "drive",
    }


def test_collect_neural_status_counts_learning_and_projects(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    store = tmp_path / "learning" / "feedback.jsonl"
    store.parent.mkdir(parents=True)
    store.write_text('{"rating": 9}\n\n{"rating": 8}\n', encoding="utf-8")
    (tmp_path / "projects" / "alpha").mkdir(parents=True)

    status = collect_neural_status(tmp_path)

    assert status["feedback_count"] == 2
    assert status["project_count"] == 1
    dna = next(item for item in status["services"] if item["key"] == "dna")
    assert dna["state"] == "ready"
