from __future__ import annotations

import base64
import json

from virallab.asset_library import AssetLibrary
from virallab.image_provider import _find_image_payload


def test_find_image_payload_supports_interactions_shape():
    encoded = base64.b64encode(b"fake-png").decode("ascii")
    payload = {
        "steps": [
            {
                "type": "model_output",
                "content": [
                    {"type": "image", "data": encoded, "mime_type": "image/png"}
                ],
            }
        ]
    }
    data, mime = _find_image_payload(payload)
    assert data == encoded
    assert mime == "image/png"


def test_approval_publishes_asset_and_updates_render_plan(tmp_path):
    render_plan = {
        "canvas": {"width": 1080, "height": 1920, "fps": 30},
        "layers": [
            {"scene_index": 2, "source_type": "generated_card", "source": "old.png"}
        ],
        "output": {"filename": "video-final.mp4"},
    }
    (tmp_path / "render-plan.json").write_text(
        json.dumps(render_plan), encoding="utf-8"
    )

    library = AssetLibrary(tmp_path)
    record = library.add_bytes(
        scene_index=2,
        data=b"fake-image",
        extension=".png",
        source="upload",
        provider="human",
    )
    library.set_status(record.id, "approved")

    published = tmp_path / "assets" / "visual-scene-02.png"
    assert published.read_bytes() == b"fake-image"

    updated = json.loads((tmp_path / "render-plan.json").read_text(encoding="utf-8"))
    assert updated["layers"][0]["source"] == "assets/visual-scene-02.png"
    assert updated["layers"][0]["source_type"] == "image_or_video"
