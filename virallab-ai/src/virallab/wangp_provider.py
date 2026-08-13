from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .asset_library import AssetLibrary, AssetRecord


class WanGPError(RuntimeError):
    """Controlled error raised by the optional WanGP integration."""


@dataclass(frozen=True)
class WanGPConfig:
    root: Path
    output_dir: Path | None = None
    model_type: str = "ltx2_22B_distilled"
    cli_args: tuple[str, ...] = ("--attention", "sdpa", "--profile", "4")

    @classmethod
    def from_env(cls) -> "WanGPConfig":
        raw_root = os.getenv("WANGP_ROOT", "").strip()
        if not raw_root:
            raise WanGPError(
                "WanGP não configurado. Defina WANGP_ROOT com a pasta da instalação local."
            )
        output = os.getenv("WANGP_OUTPUT_DIR", "").strip()
        raw_args = os.getenv("WANGP_CLI_ARGS", "--attention sdpa --profile 4")
        return cls(
            root=Path(raw_root).expanduser(),
            output_dir=Path(output).expanduser() if output else None,
            model_type=os.getenv("WANGP_MODEL", "ltx2_22B_distilled").strip()
            or "ltx2_22B_distilled",
            cli_args=tuple(raw_args.split()),
        )


class WanGPProvider:
    """Thin adapter over WanGP's in-process Python API.

    WanGP remains an optional, separately installed GPU runtime. ViralLab only imports
    it when this provider is instantiated, so cloud deployments continue to work
    without CUDA, PyTorch or WanGP model files.
    """

    name = "wangp-local"

    def __init__(
        self,
        config: WanGPConfig | None = None,
        *,
        session_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.config = config or WanGPConfig.from_env()
        self._validate_root()
        self._session_factory = session_factory or self._load_session_factory()
        self._session: Any | None = None

    def _validate_root(self) -> None:
        if not self.config.root.is_dir():
            raise WanGPError(f"Pasta WanGP não encontrada: {self.config.root}")

    def _load_session_factory(self) -> Callable[..., Any]:
        root_text = str(self.config.root.resolve())
        if root_text not in sys.path:
            sys.path.insert(0, root_text)
        try:
            module = importlib.import_module("shared.api")
        except Exception as exc:  # optional external runtime
            raise WanGPError(
                "Não foi possível importar shared.api. Confirme a instalação do WanGP "
                "e suas dependências no computador com GPU."
            ) from exc
        factory = getattr(module, "init", None)
        if not callable(factory):
            raise WanGPError("A instalação do WanGP não expõe shared.api.init().")
        return factory

    @property
    def session(self) -> Any:
        if self._session is None:
            kwargs: dict[str, Any] = {
                "root": self.config.root,
                "cli_args": list(self.config.cli_args),
                "console_output": False,
            }
            if self.config.output_dir is not None:
                self.config.output_dir.mkdir(parents=True, exist_ok=True)
                kwargs["output_dir"] = self.config.output_dir
            try:
                self._session = self._session_factory(**kwargs)
            except Exception as exc:
                raise WanGPError(f"Falha ao inicializar o WanGP: {exc}") from exc
        return self._session

    def generate_video(
        self,
        *,
        prompt: str,
        duration_seconds: int = 4,
        resolution: str = "704x1280",
        model_type: str | None = None,
        num_inference_steps: int = 8,
        fps: int = 24,
        reference_image: str | Path | None = None,
        progress_callback: Callable[[Any], None] | None = None,
    ) -> Path:
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise WanGPError("O prompt da cena está vazio.")
        if duration_seconds < 1 or duration_seconds > 30:
            raise WanGPError("A duração deve ficar entre 1 e 30 segundos.")

        settings: dict[str, Any] = {
            "model_type": model_type or self.config.model_type,
            "prompt": clean_prompt,
            "resolution": resolution,
            "num_inference_steps": int(num_inference_steps),
            "duration_seconds": int(duration_seconds),
            "force_fps": int(fps),
        }
        if reference_image is not None:
            reference = Path(reference_image).expanduser().resolve()
            if not reference.is_file():
                raise WanGPError(f"Imagem de referência não encontrada: {reference}")
            settings["image_start"] = str(reference)

        try:
            job = self.session.submit_task(settings)
            if progress_callback is not None:
                for event in job.events.iter(timeout=0.2):
                    if getattr(event, "kind", "") == "progress":
                        progress_callback(event.data)
            result = job.result()
        except Exception as exc:
            raise WanGPError(f"Falha durante a geração no WanGP: {exc}") from exc

        if not getattr(result, "success", False):
            errors = getattr(result, "errors", []) or []
            detail = "; ".join(
                str(getattr(error, "message", error)) for error in errors
            ) or "erro não informado"
            raise WanGPError(f"O WanGP não concluiu a geração: {detail}")

        generated = [Path(item) for item in getattr(result, "generated_files", [])]
        video = next(
            (item for item in generated if item.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv"}),
            None,
        )
        if video is None or not video.is_file():
            raise WanGPError("O WanGP terminou sem retornar um arquivo de vídeo válido.")
        return video

    def generate_scene_asset(
        self,
        project_dir: str | Path,
        scene: Any,
        *,
        prompt: str,
        duration_seconds: int | None = None,
        resolution: str = "704x1280",
        num_inference_steps: int = 8,
        reference_image: str | Path | None = None,
    ) -> AssetRecord:
        scene_index = int(getattr(scene, "index"))
        if duration_seconds is None:
            start = float(getattr(scene, "start", 0.0))
            end = float(getattr(scene, "end", start + 4.0))
            duration_seconds = max(1, min(30, round(end - start)))

        generated = self.generate_video(
            prompt=prompt,
            duration_seconds=duration_seconds,
            resolution=resolution,
            num_inference_steps=num_inference_steps,
            reference_image=reference_image,
        )
        library = AssetLibrary(project_dir)
        return library.add_file(
            scene_index=scene_index,
            source_file=generated,
            source="generated",
            provider=self.name,
            prompt=prompt,
        )


__all__ = ["WanGPConfig", "WanGPError", "WanGPProvider"]
