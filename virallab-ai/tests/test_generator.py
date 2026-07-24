from __future__ import annotations

import json

from virallab.generator import export_package, generate_video_package
from virallab.models import VideoBrief
from virallab.providers import LocalRuleProvider


def test_professor_cinematico_exports_complete_package(tmp_path):
    brief = VideoBrief(
        theme="IA na fisioterapia",
        duration_seconds=60,
        format="professor_cinematico",
        cta="Siga o Professor RP.",
    )

    package = generate_video_package(brief, provider=LocalRuleProvider())
    export_package(package, tmp_path)

    expected = {
        "video-package.json",
        "script.md",
        "captions.srt",
        "caption.txt",
        "asset-list.txt",
        "avatar-manifest.json",
        "render-plan.json",
    }
    assert expected.issubset({path.name for path in tmp_path.iterdir()})
    assert package.metadata["script_provider"] == "local_rules"
    assert package.scenes

    avatar = json.loads((tmp_path / "avatar-manifest.json").read_text(encoding="utf-8"))
    render = json.loads((tmp_path / "render-plan.json").read_text(encoding="utf-8"))

    assert avatar["aspect_ratio"] == "9:16"
    assert avatar["jobs"]
    assert render["canvas"] == {"width": 1080, "height": 1920, "fps": 30}
    assert render["layers"]
