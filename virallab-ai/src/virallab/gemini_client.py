from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class GeminiAPIError(RuntimeError):
    """Raised when the Gemini API cannot return a valid JSON response."""


DEFAULT_MODEL = "gemini-2.5-flash"
FALLBACK_MODELS = ("gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-flash-latest")


def get_api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")


def normalize_model(model: str | None) -> str:
    value = (model or DEFAULT_MODEL).strip().strip('"').strip("'")
    value = value.removeprefix("models/")
    return value or DEFAULT_MODEL


def configured_model() -> str:
    return normalize_model(os.getenv("VIRALLAB_GEMINI_MODEL", DEFAULT_MODEL))


def generate_json(
    prompt: str,
    *,
    model: str | None = None,
    temperature: float = 0.3,
    timeout: int = 90,
) -> tuple[dict[str, Any], str]:
    api_key = get_api_key()
    if not api_key:
        raise GeminiAPIError("GEMINI_API_KEY não configurada.")

    preferred = normalize_model(model or configured_model())
    candidates = list(dict.fromkeys((preferred, *FALLBACK_MODELS)))
    errors: list[str] = []

    for candidate in candidates:
        try:
            return _request_json(
                prompt,
                api_key=api_key,
                model=candidate,
                temperature=temperature,
                timeout=timeout,
            ), candidate
        except GeminiAPIError as exc:
            errors.append(f"{candidate}: {exc}")
            # Only try another model when the endpoint/model is unavailable.
            if "HTTP 404" not in str(exc):
                break

    raise GeminiAPIError(" | ".join(errors) or "Falha desconhecida ao consultar Gemini.")


def _request_json(
    prompt: str,
    *,
    api_key: str,
    model: str,
    temperature: float,
    timeout: int,
) -> dict[str, Any]:
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": temperature,
        },
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        detail = _extract_error_message(body)
        raise GeminiAPIError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise GeminiAPIError(f"Erro de conexão: {exc.reason}") from exc
    except TimeoutError as exc:
        raise GeminiAPIError("Tempo limite excedido.") from exc
    except json.JSONDecodeError as exc:
        raise GeminiAPIError("A API retornou uma resposta inválida.") from exc

    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(text)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        block_reason = result.get("promptFeedback", {}).get("blockReason")
        if block_reason:
            raise GeminiAPIError(f"Solicitação bloqueada: {block_reason}") from exc
        raise GeminiAPIError("Resposta inesperada do Gemini.") from exc

    if not isinstance(data, dict):
        raise GeminiAPIError("O Gemini não retornou um objeto JSON.")
    return data


def _extract_error_message(body: str) -> str:
    try:
        parsed = json.loads(body)
        return str(parsed.get("error", {}).get("message") or body)[:500]
    except json.JSONDecodeError:
        return body[:500] or "erro sem detalhes"
