from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .drive_sync import autosync_project


@dataclass
class AssetRecord:
    id: str
    scene_index: int
    filename: str
    source: str
    provider: str
    prompt: str
    status: str = "candidate"
    created_at: str = ""
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at or datetime.now(timezone.utc).isoformat()
        data["metadata"] = self.metadata or {}
        return data


class AssetLibrary:
    """Persistent candidate/approval store scoped to one ViralLab project."""

    def __init__(self, project_dir: str | Path) -> None:
        self.project_dir = Path(project_dir)
        self.root = self.project_dir / "visual-assets"
        self.manifest_path = self.root / "manifest.json"
        self.root.mkdir(parents=True, exist_ok=True)

    def scene_dir(self, scene_index: int) -> Path:
        path = self.root / f"scene-{scene_index:02d}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def add_bytes(
        self,
        *,
        scene_index: int,
        data: bytes,
        extension: str,
        source: str,
        provider: str,
        prompt: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> AssetRecord:
        asset_id = f"asset_{uuid4().hex[:12]}"
        suffix = extension if extension.startswith(".") else f".{extension}"
        filename = f"{asset_id}{suffix.lower()}"
        target = self.scene_dir(scene_index) / filename
        target.write_bytes(data)
        record = AssetRecord(
            id=asset_id,
            scene_index=scene_index,
            filename=str(target.relative_to(self.project_dir)),
            source=source,
            provider=provider,
            prompt=prompt,
            metadata=metadata,
        )
        records = self.load()
        records.append(record)
        self.save(records)
        return record

    def add_file(
        self,
        *,
        scene_index: int,
        source_file: str | Path,
        source: str = "upload",
        provider: str = "human",
        prompt: str = "",
    ) -> AssetRecord:
        path = Path(source_file)
        if not path.is_file():
            raise FileNotFoundError(path)
        return self.add_bytes(
            scene_index=scene_index,
            data=path.read_bytes(),
            extension=path.suffix or ".png",
            source=source,
            provider=provider,
            prompt=prompt,
            metadata={"original_name": path.name},
        )

    def load(self) -> list[AssetRecord]:
        if not self.manifest_path.exists():
            return []
        try:
            payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return [AssetRecord(**item) for item in payload.get("assets", [])]

    def save(self, records: list[AssetRecord]) -> Path:
        payload = {
            "version": "1.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "assets": [item.to_dict() for item in records],
        }
        self.manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.manifest_path

    def for_scene(self, scene_index: int) -> list[AssetRecord]:
        return [item for item in self.load() if item.scene_index == scene_index]

    def set_status(self, asset_id: str, status: str) -> AssetRecord:
        allowed = {"candidate", "approved", "rejected"}
        if status not in allowed:
            raise ValueError(f"Status inválido: {status}")
        records = self.load()
        selected: AssetRecord | None = None
        for item in records:
            if item.id == asset_id:
                selected = item
                item.status = status
                if status == "approved":
                    for other in records:
                        if (
                            other.scene_index == item.scene_index
                            and other.id != item.id
                            and other.status == "approved"
                        ):
                            other.status = "candidate"
                break
        if selected is None:
            raise KeyError(asset_id)
        self.save(records)
        if status == "approved":
            self._publish_approved(selected)
            autosync_project(self.project_dir)
        return selected

    def resolve(self, record: AssetRecord) -> Path:
        return self.project_dir / record.filename

    def _publish_approved(self, record: AssetRecord) -> Path:
        source = self.resolve(record)
        assets_dir = self.project_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        target = (
            assets_dir / f"visual-scene-{record.scene_index:02d}{source.suffix.lower()}"
        )
        shutil.copy2(source, target)
        self._sync_render_plan(record.scene_index, target)
        return target

    def _sync_render_plan(self, scene_index: int, target: Path) -> None:
        plan_path = self.project_dir / "render-plan.json"
        if not plan_path.exists():
            return
        try:
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        relative = str(target.relative_to(self.project_dir))
        changed = False
        for layer in plan.get("layers", []):
            if int(layer.get("scene_index", -1)) == scene_index:
                layer["source_type"] = "image_or_video"
                layer["source"] = relative
                changed = True
                break
        if changed:
            plan_path.write_text(
                json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
            )
