from __future__ import annotations

import importlib.util
import json
import os
import shutil
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .gemini_client import configured_model, get_api_key
from .ollama_client import base_url


@dataclass
class ServiceStatus:
    key: str
    label: str
    state: str
    detail: str
    action: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def collect_neural_status(workspace: str | Path) -> dict[str, Any]:
    root = Path(workspace)
    feedback_store = root / "learning" / "feedback.jsonl"
    projects_dir = root / "projects"
    feedback_count = _jsonl_count(feedback_store)
    project_count = sum(1 for item in projects_dir.iterdir() if item.is_dir()) if projects_dir.exists() else 0

    ollama = _ollama_status()
    models = ollama.pop("models", [])
    qwen_model = os.getenv("VIRALLAB_OLLAMA_MODEL", "qwen3:4b")
    embedding_model = os.getenv("VIRALLAB_EMBEDDING_MODEL", "bge-m3")

    services = [
        ServiceStatus(
            key="gemini",
            label="Gemini",
            state="ready" if get_api_key() else "setup",
            detail=configured_model() if get_api_key() else "Chave não configurada",
            action="Configure GEMINI_API_KEY nos secrets." if not get_api_key() else "",
        ),
        ServiceStatus(
            key="qwen",
            label="Qwen local",
            state="ready" if ollama["state"] == "ready" and _has_model(models, qwen_model) else ollama["state"],
            detail=qwen_model if _has_model(models, qwen_model) else ollama["detail"],
            action=f"Execute: ollama pull {qwen_model}" if ollama["state"] == "ready" and not _has_model(models, qwen_model) else ollama.get("action", ""),
        ),
        ServiceStatus(
            key="embedding",
            label="Memória BGE-M3",
            state="ready" if ollama["state"] == "ready" and _has_model(models, embedding_model) else ollama["state"],
            detail=embedding_model if _has_model(models, embedding_model) else "Modelo de embeddings ainda não detectado",
            action=f"Execute: ollama pull {embedding_model}" if ollama["state"] == "ready" and not _has_model(models, embedding_model) else ollama.get("action", ""),
        ),
        ServiceStatus(
            key="whisper",
            label="Whisper",
            state="ready" if importlib.util.find_spec("faster_whisper") else "setup",
            detail="Transcrição local disponível" if importlib.util.find_spec("faster_whisper") else "Dependência opcional não instalada",
            action="Instale o extra semantic do projeto." if not importlib.util.find_spec("faster_whisper") else "",
        ),
        ServiceStatus(
            key="dna",
            label="DNA RP",
            state="ready" if feedback_count else "learning",
            detail=f"{feedback_count} aprendizados registrados",
            action="Avalie e salve roteiros no DNA RP." if not feedback_count else "",
        ),
        ServiceStatus(
            key="render",
            label="Render",
            state="ready" if shutil.which("ffmpeg") else "setup",
            detail="FFmpeg disponível" if shutil.which("ffmpeg") else "FFmpeg não detectado",
            action="Instale FFmpeg no ambiente de execução." if not shutil.which("ffmpeg") else "",
        ),
    ]

    ready = sum(item.state == "ready" for item in services)
    return {
        "services": [item.to_dict() for item in services],
        "ready_count": ready,
        "total_count": len(services),
        "feedback_count": feedback_count,
        "project_count": project_count,
        "ollama_models": models,
    }


def _ollama_status() -> dict[str, Any]:
    url = base_url()
    if not url:
        return {
            "state": "setup",
            "detail": "OLLAMA_BASE_URL não configurada",
            "action": "No celular/Streamlit Cloud, use um endpoint remoto seguro; localhost só funciona no computador servidor.",
            "models": [],
        }
    request = urllib.request.Request(f"{url}/api/tags", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "state": "offline",
            "detail": "Ollama configurado, mas não acessível",
            "action": str(exc)[:180],
            "models": [],
        }
    names = [str(item.get("name", "")) for item in payload.get("models", []) if isinstance(item, dict)]
    return {"state": "ready", "detail": f"{len(names)} modelo(s) detectado(s)", "action": "", "models": names}


def _has_model(models: list[str], expected: str) -> bool:
    expected_base = expected.split(":", 1)[0]
    return any(name == expected or name.split(":", 1)[0] == expected_base for name in models)


def _jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
