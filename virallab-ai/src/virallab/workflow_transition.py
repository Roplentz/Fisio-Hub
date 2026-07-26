from __future__ import annotations

from typing import Any, MutableMapping

ANALYSIS_RESULT_KEYS = (
    "video_analysis",
    "semantic_analysis",
    "visual_analysis",
    "multimodal_timeline",
    "editorial_analysis",
    "analysis_warnings",
    "analysis_source_name",
)


def clear_analysis_state(
    state: MutableMapping[str, Any], *, keep_video: bool = False
) -> None:
    """Remove resultados antigos para impedir que outro vídeo reutilize uma análise anterior."""
    for key in ANALYSIS_RESULT_KEYS:
        state.pop(key, None)
    state.pop("analysis_upload_key", None)
    if not keep_video:
        for key in ("pending_video_path", "pending_video_name", "pending_video_source"):
            state.pop(key, None)


def handoff_analysis_project(
    state: MutableMapping[str, Any],
    *,
    project_id: str,
    package: Any,
    package_dir: str,
    reference_analysis_path: str,
) -> None:
    """Entrega um projeto criado na análise ao Studio 3.0 na etapa correta."""
    state["project_id"] = project_id
    state["package"] = package
    state["package_dir"] = package_dir
    state["preferred_hook"] = getattr(package, "hook", "")
    state["studio_step"] = "script"
    state["analysis_completed"] = True
    state["reference_analysis_path"] = reference_analysis_path
    state["studio_flash"] = (
        "Análise concluída. Sua versão original foi criada e está pronta para revisão no Roteiro."
    )
    # Chaves antigas da versão 2.0 não devem controlar a navegação atual.
    state.pop("nav_view", None)


__all__ = ["ANALYSIS_RESULT_KEYS", "clear_analysis_state", "handoff_analysis_project"]
