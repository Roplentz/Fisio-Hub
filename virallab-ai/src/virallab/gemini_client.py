from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any


class GeminiAPIError(RuntimeError):
    """Raised when the Gemini API cannot return a valid JSON response."""


DEFAULT_MODEL = "gemini-3.6-flash"
FALLBACK_MODELS = (
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
    "gemini-flash-latest",
)
RETRYABLE_HTTP_CODES = {408, 429, 500, 502, 503, 504}


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
    temperature: float | None = None,
    timeout: int = 90,
    retries_per_model: int = 2,
) -> tuple[dict[str, Any], str]:
    api_key = get_api_key()
    if not api_key:
        raise GeminiAPIError("GEMINI_API_KEY não configurada.")

    preferred = normalize_model(model or configured_model())
    candidates = list(dict.fromkeys((preferred, *FALLBACK_MODELS)))
    errors: list[str] = []

    for candidate in candidates:
        for attempt in range(max(1, retries_per_model)):
            try:
                return _request_json(
                    prompt,
                    api_key=api_key,
                    model=candidate,
                    temperature=temperature,
                    timeout=timeout,
                ), candidate
            except GeminiAPIError as exc:
                message = str(exc)
                errors.append(f"{candidate}: {message}")
                code = _http_code(message)

                if code == 404:
                    break
                if code in RETRYABLE_HTTP_CODES and attempt + 1 < max(
                    1, retries_per_model
                ):
                    time.sleep(min(2**attempt, 4))
                    continue
                break

    raise GeminiAPIError(
        " | ".join(errors) or "Falha desconhecida ao consultar Gemini."
    )


def _request_json(
    prompt: str,
    *,
    api_key: str,
    model: str,
    temperature: float | None,
    timeout: int,
) -> dict[str, Any]:
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    generation_config: dict[str, Any] = {
        "responseMimeType": "application/json",
    }
    # Newer Gemini models deprecate sampling parameters. Keep support only
    # when an explicit value is requested for an older configured model.
    if temperature is not None and not model.startswith(("gemini-3.5", "gemini-3.6")):
        generation_config["temperature"] = temperature

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
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


def _http_code(message: str) -> int | None:
    if not message.startswith("HTTP "):
        return None
    try:
        return int(message.split()[1].rstrip(":"))
    except (IndexError, ValueError):
        return None


def _extract_error_message(body: str) -> str:
    try:
        parsed = json.loads(body)
        return str(parsed.get("error", {}).get("message") or body)[:500]
    except json.JSONDecodeError:
        return body[:500] or "erro sem detalhes"
