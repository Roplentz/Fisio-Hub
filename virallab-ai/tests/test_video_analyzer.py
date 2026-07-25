from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from virallab.video_analyzer import VideoAnalysisError, analyze_video


def test_missing_video_raises(tmp_path: Path) -> None:
    with pytest.raises(VideoAnalysisError):
        analyze_video(tmp_path / "missing.mp4")


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="FFmpeg required",
)
def test_analyze_short_vertical_video(tmp_path: Path) -> None:
    output = tmp_path / "sample.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=360x640:d=1:r=30",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=stereo",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(output),
        ],
        check=True,
        capture_output=True,
    )

    analysis = analyze_video(output)

    assert analysis.orientation == "vertical"
    assert analysis.width == 360
    assert analysis.height == 640
    assert analysis.has_audio is True
    assert analysis.estimated_scenes >= 1
    assert 0 <= analysis.viral_potential_score <= 100
