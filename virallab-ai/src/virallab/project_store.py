from __future__ import annotations

import io
import json
import re
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import Scene, VideoBrief, VideoPackage

PROJECT_PATTERN = re.compile(r"^(?:project-)?(\d{3,})$")


@dataclass
class SavedProject:
    project_id: str
    name: str
    theme: str
    status: str
    updated_at: str
    scenes: int = 0
    approved_assets: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "theme": self.theme,
            "status": self.status,
            "updated_at": self.updated_at,
            "scenes": self.scenes,
            "approved_assets": self.approved_assets,
        }


class ProjectStore:
    """Numbered project registry with ZIP backup/import.

    The local filesystem is convenient during a Streamlit session. ZIP export is the
    durable, provider-neutral backup for environments whose disk may be ephemeral.
    """

    def __init__(self, projects_dir: str | Path) -> None:
        self.root = Path(projects_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.root / "projects-index.json"

    def next_id(self) -> str:
        numbers: list[int] = []
        for path in self.root.iterdir():
            if not path.is_dir():
                continue
            match = PROJECT_PATTERN.match(path.name)
            if match:
                numbers.append(int(match.group(1)))
        for item in self.list_projects():
            match = PROJECT_PATTERN.match(item.project_id)
            if match:
                numbers.append(int(match.group(1)))
        return f"{max(numbers, default=0) + 1:03d}"

    def project_dir(self, project_id: str) -> Path:
        return self.root / self._clean_id(project_id)

    def save(
        self,
        project_id: str,
        *,
        name: str = "",
        package: VideoPackage | None = None,
        preferred_hook: str = "",
        status: str = "em produção",
    ) -> SavedProject:
        clean_id = self._clean_id(project_id)
        directory = self.project_dir(clean_id)
        directory.mkdir(parents=True, exist_ok=True)

        package_data = package.to_dict() if package is not None else self._read_package_data(directory)
        if package_data:
            (directory / "video-package.json").write_text(
                json.dumps(package_data, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        approved_assets = self._approved_assets(directory)
        theme = str((package_data.get("brief") or {}).get("theme", "")) if package_data else ""
        scenes = len(package_data.get("scenes", [])) if package_data else 0
        now = datetime.now(timezone.utc).isoformat()
        display_name = name.strip() or theme.strip() or f"Projeto {clean_id}"
        metadata = {
            "version": "1.0",
            "project_id": clean_id,
            "name": display_name,
            "theme": theme,
            "status": status,
            "updated_at": now,
            "preferred_hook": preferred_hook,
            "scenes": scenes,
            "approved_assets": approved_assets,
        }
        (directory / "project.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        saved = SavedProject(
            project_id=clean_id,
            name=display_name,
            theme=theme,
            status=status,
            updated_at=now,
            scenes=scenes,
            approved_assets=approved_assets,
        )
        self._upsert_registry(saved)
        return saved

    def list_projects(self) -> list[SavedProject]:
        projects: dict[str, SavedProject] = {}
        if self.registry_path.exists():
            try:
                payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
                for item in payload.get("projects", []):
                    project = SavedProject(**item)
                    projects[project.project_id] = project
            except (json.JSONDecodeError, TypeError, ValueError):
                pass

        for directory in self.root.iterdir():
            if not directory.is_dir():
                continue
            metadata_path = directory / "project.json"
            if not metadata_path.exists():
                continue
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                project = SavedProject(
                    project_id=str(metadata.get("project_id") or directory.name),
                    name=str(metadata.get("name") or f"Projeto {directory.name}"),
                    theme=str(metadata.get("theme", "")),
                    status=str(metadata.get("status", "em produção")),
                    updated_at=str(metadata.get("updated_at", "")),
                    scenes=int(metadata.get("scenes", 0) or 0),
                    approved_assets=int(metadata.get("approved_assets", 0) or 0),
                )
                projects[project.project_id] = project
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
        return sorted(projects.values(), key=lambda item: item.updated_at, reverse=True)

    def load(self, project_id: str) -> tuple[SavedProject, VideoPackage | None, str]:
        directory = self.project_dir(project_id)
        if not directory.is_dir():
            raise FileNotFoundError(project_id)
        metadata = json.loads((directory / "project.json").read_text(encoding="utf-8"))
        saved = SavedProject(
            project_id=str(metadata["project_id"]),
            name=str(metadata.get("name", "")),
            theme=str(metadata.get("theme", "")),
            status=str(metadata.get("status", "em produção")),
            updated_at=str(metadata.get("updated_at", "")),
            scenes=int(metadata.get("scenes", 0) or 0),
            approved_assets=int(metadata.get("approved_assets", 0) or 0),
        )
        package_data = self._read_package_data(directory)
        package = package_from_dict(package_data) if package_data else None
        return saved, package, str(metadata.get("preferred_hook", ""))

    def export_zip(self, project_id: str) -> bytes:
        directory = self.project_dir(project_id)
        if not directory.is_dir():
            raise FileNotFoundError(project_id)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in directory.rglob("*"):
                if path.is_file():
                    archive.write(path, arcname=f"project-{directory.name}/{path.relative_to(directory)}")
        return buffer.getvalue()

    def import_zip(self, data: bytes) -> SavedProject:
        new_id = self.next_id()
        destination = self.project_dir(new_id)
        destination.mkdir(parents=True, exist_ok=False)
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    relative_parts = Path(member.filename).parts
                    relative = Path(*relative_parts[1:]) if len(relative_parts) > 1 else Path(relative_parts[0])
                    target = (destination / relative).resolve()
                    if destination.resolve() not in target.parents:
                        raise ValueError("Backup contém caminho inválido.")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(member))
        except Exception:
            shutil.rmtree(destination, ignore_errors=True)
            raise

        metadata_path = destination / "project.json"
        metadata: dict[str, Any] = {}
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                metadata = {}
        return self.save(
            new_id,
            name=str(metadata.get("name", "Projeto importado")),
            preferred_hook=str(metadata.get("preferred_hook", "")),
            status=str(metadata.get("status", "em produção")),
        )

    def delete(self, project_id: str) -> None:
        clean_id = self._clean_id(project_id)
        shutil.rmtree(self.project_dir(clean_id), ignore_errors=True)
        remaining = [item for item in self.list_projects() if item.project_id != clean_id]
        self._write_registry(remaining)

    def _read_package_data(self, directory: Path) -> dict[str, Any]:
        path = directory / "video-package.json"
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _approved_assets(self, directory: Path) -> int:
        manifest = directory / "visual-assets" / "manifest.json"
        if not manifest.exists():
            return 0
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            return sum(item.get("status") == "approved" for item in payload.get("assets", []))
        except json.JSONDecodeError:
            return 0

    def _upsert_registry(self, project: SavedProject) -> None:
        items = {item.project_id: item for item in self.list_projects()}
        items[project.project_id] = project
        self._write_registry(sorted(items.values(), key=lambda item: item.updated_at, reverse=True))

    def _write_registry(self, projects: list[SavedProject]) -> None:
        self.registry_path.write_text(
            json.dumps({"version": "1.0", "projects": [item.to_dict() for item in projects]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _clean_id(project_id: str) -> str:
        value = str(project_id).strip().replace("project-", "")
        if not value.isdigit():
            raise ValueError("O código do projeto deve ser numérico.")
        return f"{int(value):03d}"


def package_from_dict(data: dict[str, Any]) -> VideoPackage:
    brief = VideoBrief(**data["brief"])
    scenes = [Scene(**item) for item in data.get("scenes", [])]
    return VideoPackage(
        brief=brief,
        hook=str(data.get("hook", "")),
        thesis=str(data.get("thesis", "")),
        scenes=scenes,
        caption=str(data.get("caption", "")),
        hashtags=list(data.get("hashtags", [])),
        warnings=list(data.get("warnings", [])),
        metadata=dict(data.get("metadata", {})),
    )
