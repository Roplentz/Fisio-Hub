from __future__ import annotations

from pathlib import Path

import streamlit as st

from virallab.learning import load_feedback, summarize_preferences
from virallab.studio.layout import (
    configure_page,
    render_footer,
    render_hero,
    render_progress,
    render_sidebar,
)
from virallab.studio.navigation import (
    progress_value as navigation_progress_value,
    render_step_selector as navigation_step_selector,
)
from virallab.studio.paths import DEFAULT_PATHS
from virallab.studio.state import (
    LOGICAL_STEP_KEY,
    initialize_state as initialize_session_state,
    reset_project,
)
from virallab.studio.steps import (
    AnalysisAction,
    AvatarAction,
    CreativesAction,
    PublicationAction,
    RenderAction,
    VoiceAction,
)
from virallab.studio.steps.analysis import render_analysis as render_analysis_step
from virallab.studio.steps.avatar import render_avatar as render_avatar_step
from virallab.studio.steps.creatives import render_creatives as render_creatives_step
from virallab.studio.steps.learning import render_learning as render_learning_step
from virallab.studio.steps.publication import (
    render_publication as render_publication_step,
)
from virallab.studio.steps.render import render_output as render_output_step
from virallab.studio.steps.script import render_script as render_script_step
from virallab.studio.steps.strategy import render_strategy as render_strategy_step
from virallab.studio.steps.voice import render_voice as render_voice_step

APP_ROOT = DEFAULT_PATHS.app_root
WORKSPACE = DEFAULT_PATHS.workspace
ANALYSIS_DIR = DEFAULT_PATHS.analysis
PROJECTS_DIR = DEFAULT_PATHS.projects
LEARNING_STORE = DEFAULT_PATHS.learning_store
DEFAULT_PATHS.ensure_directories()
configure_page(st)


def initialize_state() -> None:
    initialize_session_state(st.session_state)


def render_step_selector() -> str:
    return navigation_step_selector(st, st.session_state)


def project_dir(project_id: str) -> Path:
    return DEFAULT_PATHS.project_dir(project_id)


def new_project() -> None:
    reset_project(st.session_state)


def open_analysis(path: Path, name: str, source: str) -> None:
    st.session_state.pending_video_path = str(path)
    st.session_state.pending_video_name = name
    st.session_state.pending_video_source = source
    st.switch_page("pages/01_Analisar_Video.py")


def progress_value() -> float:
    return navigation_progress_value(st.session_state)


def render_analysis() -> None:
    action = render_analysis_step(st, ANALYSIS_DIR, open_analysis)
    if action is AnalysisAction.CREATE_FROM_SCRATCH:
        st.session_state[LOGICAL_STEP_KEY] = "strategy"
        st.rerun()


def render_strategy() -> None:
    result = render_strategy_step(
        st,
        project_id=st.session_state.project_id,
        project_dir_factory=project_dir,
    )
    if result is None:
        return
    st.session_state.package = result.package
    st.session_state.package_dir = str(result.output_directory)
    st.session_state.preferred_hook = result.package.hook
    st.session_state[LOGICAL_STEP_KEY] = "script"
    st.rerun()


def render_script(package) -> None:
    result = render_script_step(
        st,
        package,
        preferred_hook=st.session_state.preferred_hook,
    )
    st.session_state.preferred_hook = result.preferred_hook
    if result.continue_to_avatar:
        st.session_state[LOGICAL_STEP_KEY] = "avatar"
        st.rerun()


def render_avatar() -> None:
    candidate = (
        Path(st.session_state.avatar_candidate)
        if st.session_state.avatar_candidate
        else None
    )
    result = render_avatar_step(st, WORKSPACE, candidate_path=candidate)
    if result.clear_candidate:
        st.session_state.avatar_candidate = None
    elif result.candidate_path is not None:
        st.session_state.avatar_candidate = str(result.candidate_path)
    if result.action is AvatarAction.GO_TO_VOICE:
        st.session_state[LOGICAL_STEP_KEY] = "voice"
        st.rerun()
    elif result.action is AvatarAction.RERUN:
        st.rerun()


def render_voice(package, package_path: Path) -> None:
    result = render_voice_step(
        st,
        package,
        package_path,
        state=st.session_state,
    )
    if result.last_generation is not None:
        st.session_state["voice_last_generation"] = result.last_generation
    if result.action is VoiceAction.GO_TO_CREATIVES:
        st.session_state[LOGICAL_STEP_KEY] = "creatives"
        st.rerun()
    elif result.action is VoiceAction.RERUN:
        st.rerun()


def render_creatives(package, package_path: Path) -> None:
    result = render_creatives_step(
        st,
        package,
        package_path,
        WORKSPACE,
    )
    if result.action is CreativesAction.GO_TO_RENDER:
        st.session_state[LOGICAL_STEP_KEY] = "render"
        st.rerun()
    elif result.action is CreativesAction.RERUN:
        st.rerun()


def render_output(package_path: Path) -> None:
    result = render_output_step(st, package_path)
    if result.action is RenderAction.GO_TO_PUBLICATION:
        st.session_state[LOGICAL_STEP_KEY] = "publication"
        st.rerun()


def render_publication(package) -> None:
    result = render_publication_step(st, package)
    if result.action is PublicationAction.GO_TO_LEARNING:
        st.session_state[LOGICAL_STEP_KEY] = "learning"
        st.rerun()


def render_learning(package) -> None:
    render_learning_step(
        st,
        package,
        project_id=st.session_state.project_id,
        preferred_hook=st.session_state.preferred_hook,
        learning_store=LEARNING_STORE,
    )


initialize_state()
records = load_feedback(LEARNING_STORE)
summary = summarize_preferences(records)
render_sidebar(st, st.session_state, summary, new_project)
render_hero(st)
render_progress(st, progress_value())

selected = render_step_selector()
package = st.session_state.package
package_path = (
    Path(st.session_state.package_dir) if st.session_state.package_dir else None
)

if selected == "analysis":
    render_analysis()
elif selected == "strategy":
    render_strategy()
elif selected == "script":
    render_script(package) if package else st.warning("Gere a estratégia primeiro.")
elif selected == "avatar":
    render_avatar()
elif selected == "voice":
    (
        render_voice(package, package_path)
        if package and package_path
        else st.warning("Gere o roteiro primeiro.")
    )
elif selected == "creatives":
    (
        render_creatives(package, package_path)
        if package and package_path
        else st.warning("Gere o roteiro primeiro.")
    )
elif selected == "render":
    render_output(package_path) if package_path else st.warning(
        "Crie o projeto primeiro."
    )
elif selected == "publication":
    render_publication(package)
else:
    render_learning(package)

render_footer(st)
