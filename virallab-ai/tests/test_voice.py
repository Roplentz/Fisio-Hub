from __future__ import annotations

from dataclasses import dataclass

from virallab.voice import (
    VoicePlan,
    align_scenes_by_script,
    load_voice_plan,
    save_voice_plan,
)


@dataclass
class Scene:
    index: int
    narration: str


def test_align_scenes_uses_script_word_weight() -> None:
    scenes = [Scene(1, "frase curta"), Scene(2, "esta é uma frase bem mais longa")]
    timings = align_scenes_by_script(scenes, duration=9.0)
    assert len(timings) == 2
    assert timings[0].start == 0.0
    assert timings[-1].end == 9.0
    assert (timings[1].end - timings[1].start) > (timings[0].end - timings[0].start)


def test_voice_plan_round_trip(tmp_path) -> None:
    plan = VoicePlan(
        audio_file="assets/narration.wav", duration=12.5, mode="full", scenes=[]
    )
    save_voice_plan(tmp_path, plan)
    loaded = load_voice_plan(tmp_path)
    assert loaded is not None
    assert loaded.audio_file == "assets/narration.wav"
    assert loaded.duration == 12.5
