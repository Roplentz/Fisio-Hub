from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from .renderer import render_video


RenderState = Literal["queued", "running", "succeeded", "failed", "cancelled"]


@dataclass
class RenderJob:
    package_dir: str
    job_id: str = field(default_factory=lambda: uuid4().hex)
    state: RenderState = "queued"
    progress: int = 0
    output_file: str = ""
    error_code: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: str = ""
    finished_at: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class VideoRenderer(ABC):
    @abstractmethod
    def render(self, job: RenderJob, *, dry_run: bool = False) -> RenderJob:
        raise NotImplementedError


class FFmpegVideoRenderer(VideoRenderer):
    """Adaptador do renderizador seguro já existente no ViralLab."""

    engine_name = "virallab_ffmpeg"
    engine_version = "0.11.0"

    def render(self, job: RenderJob, *, dry_run: bool = False) -> RenderJob:
        if job.state == "cancelled":
            return job
        job.state = "running"
        job.progress = 10
        job.started_at = datetime.now(timezone.utc).isoformat()
        try:
            output = render_video(job.package_dir, dry_run=dry_run)
            job.output_file = str(output)
            job.progress = 100
            job.state = "succeeded"
        except Exception as exc:
            job.state = "failed"
            job.error_code = type(exc).__name__
        finally:
            job.finished_at = datetime.now(timezone.utc).isoformat()
            self.write_report(job)
        return job

    def write_report(self, job: RenderJob) -> Path:
        root = Path(job.package_dir).resolve()
        target = root / "generated" / "render-report.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {
                    **job.to_dict(),
                    "engine": self.engine_name,
                    "engine_version": self.engine_version,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return target


def get_video_renderer() -> VideoRenderer:
    """Seleciona o motor sem acoplar a interface ao fornecedor.

    O nome da flag foi preservado conforme a decisão do Sprint 0. Neste sprint,
    "mpt" ativa os adaptadores auditados, mas continua usando o compositor
    seguro do ViralLab. Nenhuma API antiga do MoneyPrinterTurbo é exposta.
    """

    requested = os.getenv("MPT_RENDER_ENGINE", "virallab").strip().casefold()
    if requested not in {"virallab", "mpt"}:
        raise ValueError("MPT_RENDER_ENGINE deve ser 'virallab' ou 'mpt'.")
    return FFmpegVideoRenderer()
