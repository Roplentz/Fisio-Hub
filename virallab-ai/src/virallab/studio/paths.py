"""Caminhos e diretórios usados pelo Studio."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StudioPaths:
    """Conjunto imutável de caminhos do workspace do Studio."""

    app_root: Path
    workspace: Path
    analysis: Path
    projects: Path
    learning_store: Path

    @classmethod
    def from_app_root(cls, app_root: str | Path) -> "StudioPaths":
        root = Path(app_root).resolve()
        workspace = root / "workspace"
        return cls(
            app_root=root,
            workspace=workspace,
            analysis=workspace / "analysis",
            projects=workspace / "projects",
            learning_store=workspace / "learning" / "feedback.jsonl",
        )

    def ensure_directories(self) -> None:
        for directory in (
            self.workspace,
            self.analysis,
            self.projects,
            self.learning_store.parent,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def project_dir(self, project_id: str) -> Path:
        return self.projects / project_id


DEFAULT_PATHS = StudioPaths.from_app_root(Path(__file__).resolve().parents[3])

__all__ = ["DEFAULT_PATHS", "StudioPaths"]
