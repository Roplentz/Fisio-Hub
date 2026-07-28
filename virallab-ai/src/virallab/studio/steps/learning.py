from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from virallab.learning import FeedbackRecord, save_feedback


class LearningAction(str, Enum):
    NONE = "none"
    SAVED = "saved"


@dataclass(frozen=True)
class LearningResult:
    """Resultado produzido pela etapa de aprendizado."""

    action: LearningAction = LearningAction.NONE
    feedback: FeedbackRecord | None = None
    saved_path: Path | None = None


def render_learning(
    st: Any,
    package: Any | None,
    *,
    project_id: str,
    preferred_hook: str,
    learning_store: str | Path,
    feedback_saver: Callable[[FeedbackRecord, str | Path], Path] = save_feedback,
) -> LearningResult:
    """Coleta e persiste feedback explícito sem acessar o estado da sessão."""

    st.subheader("Aprendizado")
    if package is None:
        st.warning("Crie o roteiro primeiro.")
        return LearningResult()

    rating = st.slider("Qualidade", 1, 10, 8)
    approved = st.checkbox("Eu publicaria", value=True)
    notes = st.text_area("O que o ViralLab deve aprender?")
    if not st.button(
        "Salvar aprendizado",
        type="primary",
        use_container_width=True,
    ):
        return LearningResult()

    feedback = FeedbackRecord(
        project_id=project_id,
        theme=package.brief.theme,
        rating=rating,
        approved=approved,
        original_hook=package.hook,
        preferred_hook=preferred_hook or package.hook,
        notes=notes,
        preferred_style="Studio 3.0",
    )
    saved_path = Path(feedback_saver(feedback, learning_store))
    st.success("Aprendizado salvo.")
    return LearningResult(
        action=LearningAction.SAVED,
        feedback=feedback,
        saved_path=saved_path,
    )


__all__ = ["LearningAction", "LearningResult", "render_learning"]
