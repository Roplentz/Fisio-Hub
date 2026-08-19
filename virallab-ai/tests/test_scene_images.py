import json

from virallab.scene_images import prepare_scene_images


def _project(tmp_path):
    package = {
        "brief": {"theme": "Mobilidade cervical"},
        "scenes": [
            {
                "index": 1,
                "start": 0,
                "end": 4,
                "scene_type": "broll",
                "narration": "Movimento confortável e gradual.",
                "on_screen_text": "Movimente sem forçar",
                "visual_direction": "Pessoa em ambiente profissional",
                "edit_direction": "fade",
                "asset_query": "mobilidade cervical",
            }
        ],
    }
    plan = {
        "canvas": {"width": 1080, "height": 1920, "fps": 30},
        "layers": [{"scene_index": 1, "source_type": "image_or_video", "source": "assets/missing"}],
        "output": {"filename": "video-final.mp4"},
    }
    (tmp_path / "video-package.json").write_text(json.dumps(package), encoding="utf-8")
    (tmp_path / "render-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    return tmp_path


def test_prepares_local_png_and_connects_it_to_render_plan(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    project = _project(tmp_path)

    results = prepare_scene_images(project)

    image = project / "assets" / "visual-scene-01.png"
    assert image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    plan = json.loads((project / "render-plan.json").read_text(encoding="utf-8"))
    assert plan["layers"][0]["source"] == "assets/visual-scene-01.png"
    assert results[0].provider == "local_visual"


def test_reuses_existing_scene_image(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    project = _project(tmp_path)
    prepare_scene_images(project)

    results = prepare_scene_images(project)

    assert results[0].provider == "existing"
