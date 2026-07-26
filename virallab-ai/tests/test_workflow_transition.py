from types import SimpleNamespace

from virallab.workflow_transition import clear_analysis_state, handoff_analysis_project


def test_handoff_analysis_project_opens_script_and_removes_legacy_navigation() -> None:
    state = {
        "nav_view": "Studio",
        "studio_step": "analysis",
        "pending_video_path": "/tmp/video.mp4",
    }
    package = SimpleNamespace(hook="Gancho criado")

    handoff_analysis_project(
        state,
        project_id="abc123",
        package=package,
        package_dir="/tmp/project",
        reference_analysis_path="/tmp/project/reference-analysis.json",
    )

    assert state["project_id"] == "abc123"
    assert state["package"] is package
    assert state["package_dir"] == "/tmp/project"
    assert state["preferred_hook"] == "Gancho criado"
    assert state["studio_step"] == "script"
    assert state["analysis_completed"] is True
    assert "nav_view" not in state
    assert "Roteiro" in state["studio_flash"]


def test_clear_analysis_state_removes_stale_results_but_can_keep_video() -> None:
    state = {
        "video_analysis": object(),
        "semantic_analysis": object(),
        "visual_analysis": object(),
        "editorial_analysis": object(),
        "analysis_upload_key": "old",
        "pending_video_path": "/tmp/video.mp4",
        "pending_video_name": "video.mp4",
        "pending_video_source": "upload",
    }

    clear_analysis_state(state, keep_video=True)

    assert "video_analysis" not in state
    assert "semantic_analysis" not in state
    assert "visual_analysis" not in state
    assert "editorial_analysis" not in state
    assert "analysis_upload_key" not in state
    assert state["pending_video_path"] == "/tmp/video.mp4"

    clear_analysis_state(state, keep_video=False)
    assert "pending_video_path" not in state
    assert "pending_video_name" not in state
    assert "pending_video_source" not in state
