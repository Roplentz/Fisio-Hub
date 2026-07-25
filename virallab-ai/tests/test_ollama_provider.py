from __future__ import annotations

import json

from virallab.models import VideoBrief
from virallab.ollama_client import cosine_similarity
from virallab.providers import OllamaProvider


def test_cosine_similarity_handles_identical_and_orthogonal_vectors():
    assert round(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 5) == 1.0
    assert round(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 5) == 0.0


def test_ollama_provider_normalizes_json(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def fake_chat_json(prompt: str, *, model: str | None = None, timeout: int = 120):
        assert "AUTOAPRENDIZADO DNA RP" in prompt
        return {
            "hook": "Hook local",
            "thesis": "Tese local",
            "caption": "Legenda local",
            "scenes": [],
        }, model or "qwen3:4b"

    monkeypatch.setattr("virallab.providers.chat_json", fake_chat_json)
    provider = OllamaProvider(model="qwen3:4b")
    result = provider.generate(VideoBrief(theme="IA na fisioterapia"))

    assert result["hook"] == "Hook local"
    assert result["provider_model"] == "qwen3:4b"
    assert "Qwen3" in result["provider_notice"]
