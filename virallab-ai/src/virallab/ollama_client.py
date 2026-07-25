from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.request
from typing import Any


class OllamaError(RuntimeError):
    """Controlled failure while calling a local or remote Ollama server."""


def base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "").strip().rstrip("/")


def is_configured() -> bool:
    return bool(base_url())


def chat_json(
    prompt: str,
    *,
    model: str | None = None,
    timeout: int = 120,
) -> tuple[dict[str, Any], str]:
    url = base_url()
    if not url:
        raise OllamaError("OLLAMA_BASE_URL não configurada.")

    selected_model = (model or os.getenv("VIRALLAB_OLLAMA_MODEL", "qwen3:4b")).strip()
    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "think": False,
        "options": {
            "temperature": 0.45,
            "num_ctx": 8192,
            "num_predict": 2600,
        },
    }
    result = _request(f"{url}/api/generate", payload, timeout=timeout)
    raw = result.get("response", "")
    if not isinstance(raw, str) or not raw.strip():
        raise OllamaError("O Ollama não retornou conteúdo.")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise OllamaError("O modelo local não retornou JSON válido.") from exc
    if not isinstance(parsed, dict):
        raise OllamaError("O modelo local não retornou um objeto JSON.")
    return parsed, selected_model


def embed_texts(
    texts: list[str],
    *,
    model: str | None = None,
    timeout: int = 90,
) -> tuple[list[list[float]], str]:
    url = base_url()
    if not url:
        raise OllamaError("OLLAMA_BASE_URL não configurada.")
    selected_model = (model or os.getenv("VIRALLAB_EMBEDDING_MODEL", "bge-m3")).strip()
    result = _request(
        f"{url}/api/embed",
        {"model": selected_model, "input": texts, "truncate": True},
        timeout=timeout,
    )
    embeddings = result.get("embeddings")
    if not isinstance(embeddings, list) or len(embeddings) != len(texts):
        raise OllamaError("Resposta de embeddings incompleta.")
    normalized: list[list[float]] = []
    for vector in embeddings:
        if not isinstance(vector, list) or not vector:
            raise OllamaError("Embedding inválido retornado pelo Ollama.")
        normalized.append([float(value) for value in vector])
    return normalized, selected_model


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return max(-1.0, min(1.0, dot / (left_norm * right_norm)))


def semantic_similarity(left: str, right: str) -> float | None:
    """Return neural similarity when Ollama embeddings are configured; otherwise None."""
    if not is_configured() or not left.strip() or not right.strip():
        return None
    try:
        vectors, _ = embed_texts([left, right], timeout=20)
    except OllamaError:
        return None
    return max(0.0, cosine_similarity(vectors[0], vectors[1]))


def _request(endpoint: str, payload: dict[str, Any], *, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise OllamaError(f"HTTP {exc.code}: {body[:400]}") from exc
    except urllib.error.URLError as exc:
        raise OllamaError(f"Não foi possível conectar ao Ollama: {exc.reason}") from exc
    except TimeoutError as exc:
        raise OllamaError("Tempo limite do Ollama excedido.") from exc
    except json.JSONDecodeError as exc:
        raise OllamaError("O Ollama retornou uma resposta inválida.") from exc
    if not isinstance(data, dict):
        raise OllamaError("Resposta inesperada do Ollama.")
    return data
