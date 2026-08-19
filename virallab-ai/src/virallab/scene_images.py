from __future__ import annotations

import hashlib
import json
import math
import os
import struct
import zlib
from dataclasses import dataclass, asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .asset_library import AssetLibrary
from .creative_assets import build_scene_prompt, generate_scene_asset
from .image_provider import ImageGenerationError


@dataclass(frozen=True)
class SceneImageResult:
    scene_index: int
    provider: str
    filename: str
    prompt: str
    fallback_reason: str = ""


def prepare_scene_images(project_dir: str | Path) -> list[SceneImageResult]:
    """Generate and publish one renderable vertical image for every scene.

    Gemini is used when ``GEMINI_API_KEY`` is configured. The local renderer is
    deliberately always available so a missing key or transient provider error
    never produces an empty, solid-colour video.
    """
    root = Path(project_dir)
    package = json.loads((root / "video-package.json").read_text(encoding="utf-8"))
    theme = str((package.get("brief") or {}).get("theme", ""))
    results: list[SceneImageResult] = []

    for scene_data in package.get("scenes", []):
        scene = SimpleNamespace(**scene_data)
        prompt = build_scene_prompt(scene, theme=theme)
        current = _published_asset(root, int(scene.index))
        if current:
            results.append(
                SceneImageResult(int(scene.index), "existing", str(current), prompt)
            )
            continue

        fallback_reason = ""
        if os.getenv("GEMINI_API_KEY", "").strip():
            try:
                record = generate_scene_asset(root, scene, prompt=prompt)
                AssetLibrary(root).set_status(record.id, "approved")
                results.append(
                    SceneImageResult(
                        int(scene.index), record.provider, record.filename, prompt
                    )
                )
                continue
            except (ImageGenerationError, ValueError, OSError) as exc:
                fallback_reason = str(exc)[:500]
        else:
            fallback_reason = "GEMINI_API_KEY não configurada"

        target = _write_local_scene_image(root, scene_data, theme)
        _sync_render_plan(root, int(scene.index), target)
        results.append(
            SceneImageResult(
                int(scene.index),
                "local_visual",
                str(target.relative_to(root)),
                prompt,
                fallback_reason,
            )
        )

    manifest = root / "generated" / "scene-images.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {"version": "1.0", "assets": [asdict(item) for item in results]},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return results


def _published_asset(root: Path, scene_index: int) -> Path | None:
    assets = root / "assets"
    for suffix in (".png", ".jpg", ".jpeg", ".webp"):
        candidate = assets / f"visual-scene-{scene_index:02d}{suffix}"
        if candidate.is_file():
            return candidate.relative_to(root)
    return None


def _write_local_scene_image(root: Path, scene: dict[str, Any], theme: str) -> Path:
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    target = assets / f"visual-scene-{int(scene['index']):02d}.png"
    seed_text = "|".join(
        (theme, str(scene.get("visual_direction", "")), str(scene.get("scene_type", "")))
    )
    seed = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:8], 16)
    target.write_bytes(_editorial_png(540, 960, seed, str(scene.get("scene_type", "broll"))))
    return target


def _editorial_png(width: int, height: int, seed: int, scene_type: str) -> bytes:
    """Create a dependency-free branded editorial illustration as a valid PNG."""
    palettes = [
        ((17, 25, 44), (92, 64, 232), (38, 205, 184)),
        ((20, 31, 38), (31, 125, 132), (118, 226, 208)),
        ((29, 22, 50), (105, 65, 198), (238, 157, 105)),
    ]
    dark, brand, accent = palettes[seed % len(palettes)]
    pixels = bytearray()
    cx = width * (0.36 + ((seed >> 4) % 25) / 100)
    cy = height * (0.34 + ((seed >> 9) % 18) / 100)
    radius = width * (0.34 + ((seed >> 14) % 12) / 100)
    motif = {"avatar": 0, "broll": 1, "screen_capture": 2, "proof": 3}.get(scene_type, 4)

    for y in range(height):
        row = bytearray([0])
        vertical = y / max(1, height - 1)
        for x in range(width):
            dx, dy = x - cx, y - cy
            glow = max(0.0, 1.0 - math.sqrt(dx * dx + dy * dy) / radius)
            wave = (math.sin((x + seed % 97) / 62 + y / 130) + 1) * 0.035
            mix = min(0.72, glow * 0.58 + wave)
            r = int(dark[0] * (1 - mix) + brand[0] * mix)
            g = int(dark[1] * (1 - mix) + brand[1] * mix)
            b = int(dark[2] * (1 - mix) + brand[2] * mix)

            # Editorial motifs suggest care, movement and technology without
            # inventing anatomy or identifiable patients.
            nx, ny = x / width, y / height
            ring = abs(math.hypot(nx - 0.5, ny - 0.42) - (0.16 + motif * 0.008)) < 0.010
            spine = abs(nx - 0.5 - math.sin(ny * 18 + motif) * 0.025) < 0.008 and 0.22 < ny < 0.64
            panel = motif == 2 and 0.18 < nx < 0.82 and 0.25 < ny < 0.61
            panel_edge = panel and (
                nx < 0.195 or nx > 0.805 or ny < 0.265 or ny > 0.595
            )
            dots = motif == 3 and ((x // 54 + y // 54 + seed) % 7 == 0) and (x % 54 < 7 and y % 54 < 7)
            if ring or spine or panel_edge or dots:
                strength = 0.72 if not panel_edge else 0.5
                r = int(r * (1 - strength) + accent[0] * strength)
                g = int(g * (1 - strength) + accent[1] * strength)
                b = int(b * (1 - strength) + accent[2] * strength)
            # Gentle bottom vignette leaves a safe high-contrast caption zone.
            vignette = max(0.0, (vertical - 0.64) / 0.36) * 0.48
            row.extend((int(r * (1 - vignette)), int(g * (1 - vignette)), int(b * (1 - vignette))))
        pixels.extend(row)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(pixels), 7)) + chunk(b"IEND", b"")


def _sync_render_plan(root: Path, scene_index: int, target: Path) -> None:
    plan_path = root / "render-plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    relative = str(target.relative_to(root)).replace("\\", "/")
    for layer in plan.get("layers", []):
        if int(layer.get("scene_index", -1)) == scene_index:
            layer["source_type"] = "image_or_video"
            layer["source"] = relative
            break
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


__all__ = ["SceneImageResult", "prepare_scene_images"]
