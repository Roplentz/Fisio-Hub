from __future__ import annotations

import base64

from virallab.image_provider import _build_interaction_inputs


def test_interactions_payload_uses_top_level_image_fields() -> None:
    inputs = _build_interaction_inputs(
        "Crie uma imagem mestre",
        [(b"front", "image/jpeg"), (b"left", "image/png"), (b"right", "image/webp")],
    )

    assert inputs[0] == {"type": "text", "text": "Crie uma imagem mestre"}
    assert len(inputs) == 4

    for item, raw, mime in zip(
        inputs[1:],
        (b"front", b"left", b"right"),
        ("image/jpeg", "image/png", "image/webp"),
        strict=True,
    ):
        assert item["type"] == "image"
        assert item["mime_type"] == mime
        assert item["data"] == base64.b64encode(raw).decode("ascii")
        assert "inline_data" not in item


def test_interactions_payload_ignores_empty_reference() -> None:
    inputs = _build_interaction_inputs(
        "Prompt",
        [(b"", "image/jpeg"), (b"valid", "")],
    )

    assert inputs == [
        {"type": "text", "text": "Prompt"},
        {
            "type": "image",
            "mime_type": "image/jpeg",
            "data": base64.b64encode(b"valid").decode("ascii"),
        },
    ]
