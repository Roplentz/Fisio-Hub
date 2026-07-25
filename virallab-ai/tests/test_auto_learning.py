from __future__ import annotations

from virallab.learning import build_learning_profile, learning_prompt


def test_learning_profile_prioritizes_approved_relevant_feedback():
    records = [
        {
            "project_id": "p1",
            "theme": "IA na fisioterapia",
            "rating": 10,
            "approved": True,
            "original_hook": "Hook genérico",
            "preferred_hook": "A IA não substitui julgamento clínico.",
            "notes": "Usar exemplos clínicos e evitar promessas absolutas.",
            "preferred_style": "Mais científico",
            "created_at": "2026-07-25T10:00:00+00:00",
        },
        {
            "project_id": "p2",
            "theme": "Marketing para restaurantes",
            "rating": 4,
            "approved": False,
            "original_hook": "A",
            "preferred_hook": "B",
            "notes": "Ignorar este registro.",
            "preferred_style": "Mais comercial",
            "created_at": "2026-01-01T10:00:00+00:00",
        },
    ]

    profile = build_learning_profile(records, theme="inteligência artificial em fisioterapia")

    assert profile["examples_used"] == 1
    assert profile["preferred_styles"] == ["Mais científico"]
    assert profile["preferred_hooks"] == ["A IA não substitui julgamento clínico."]
    assert profile["source_project_ids"] == ["p1"]
    assert "evitar promessas absolutas" in learning_prompt(profile)


def test_learning_profile_is_empty_without_strong_signal():
    profile = build_learning_profile(
        [{"rating": 5, "approved": False, "theme": "teste"}],
        theme="teste",
    )
    assert profile["examples_used"] == 0
    assert learning_prompt(profile).startswith("Nenhum aprendizado")
