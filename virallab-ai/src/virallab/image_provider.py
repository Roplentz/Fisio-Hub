from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ImageGenerationError(RuntimeError):
    """Controlled failure while generating an image asset."""


@dataclass
class GeneratedImage:
    data: bytes
    mime_type: str
    model: str
    prompt: str

    @property
    def extension(self) -> str:
        return {
            "image/jpeg": ".jpg",
            "image/webp": ".webp",
        }.get(self.mime_type, ".png")

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(self.data)
        return target


class GeminiImageProvider:
    """Gemini REST adapter for provider-neutral Visual Brain assets."""

    name = "gemini_image"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model or os.getenv(
            "VIRALLAB_IMAGE_MODEL", "gemini-3.1-flash-image"
        )
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não configurada.")

    def generate(
        self,
        prompt: str,
        *,
        aspect_ratio: str = "9:16",
        image_size: str = "1K",
    ) -> GeneratedImage:
        endpoint = "https://generativelanguage.googleapis.com/v1beta/interactions"
        payload = {
            "model": self.model,
            "input": [{"type": "text", "text": prompt}],
            "response_format": {
                "type": "image",
                "aspect_ratio": aspect_ratio,
                "image_size": image_size,
            },
        }
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[-1500:]
            raise ImageGenerationError(
                f"Gemini recusou a geração ({exc.code}): {detail}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ImageGenerationError(
                f"Falha ao gerar imagem com Gemini: {exc}"
            ) from exc

        encoded, mime_type = _find_image_payload(result)
        if not encoded:
            raise ImageGenerationError("O Gemini não retornou uma imagem utilizável.")
        try:
            image_bytes = base64.b64decode(encoded)
        except (ValueError, TypeError) as exc:
            raise ImageGenerationError(
                "A imagem retornada pelo Gemini está corrompida."
            ) from exc
        return GeneratedImage(
            data=image_bytes,
            mime_type=mime_type or "image/png",
            model=self.model,
            prompt=prompt,
        )


def _find_image_payload(value: Any) -> tuple[str, str]:
    """Recursively support current and legacy Gemini image response shapes."""
    if isinstance(value, dict):
        output_image = value.get("output_image")
        if isinstance(output_image, dict) and output_image.get("data"):
            return str(output_image["data"]), str(
                output_image.get("mime_type", "image/png")
            )

        inline_data = value.get("inline_data") or value.get("inlineData")
        if isinstance(inline_data, dict) and inline_data.get("data"):
            return str(inline_data["data"]), str(
                inline_data.get("mime_type")
                or inline_data.get("mimeType")
                or "image/png"
            )

        if value.get("type") == "image" and value.get("data"):
            return str(value["data"]), str(value.get("mime_type", "image/png"))

        for child in value.values():
            encoded, mime = _find_image_payload(child)
            if encoded:
                return encoded, mime
    elif isinstance(value, list):
        for child in value:
            encoded, mime = _find_image_payload(child)
            if encoded:
                return encoded, mime
    return "", ""
