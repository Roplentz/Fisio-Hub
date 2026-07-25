from __future__ import annotations

import io
import json
import os
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DriveSyncResult:
    state: str
    detail: str
    file_id: str = ""
    synced_at: str = ""


def drive_config() -> tuple[dict[str, Any] | None, str]:
    """Read service-account credentials from env or Streamlit secrets."""
    folder_id = os.getenv("VIRALLAB_DRIVE_FOLDER_ID", "").strip()
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    credentials: dict[str, Any] | None = None
    if raw:
        try:
            credentials = json.loads(raw)
        except json.JSONDecodeError:
            return None, folder_id

    if credentials is None or not folder_id:
        try:
            import streamlit as st

            section = st.secrets.get("google_drive", {})
            if not folder_id:
                folder_id = str(section.get("folder_id", "")).strip()
            if credentials is None:
                candidate = section.get("service_account")
                if hasattr(candidate, "to_dict"):
                    candidate = candidate.to_dict()
                if isinstance(candidate, dict):
                    credentials = dict(candidate)
                elif isinstance(candidate, str) and candidate.strip():
                    credentials = json.loads(candidate)
        except Exception:
            pass
    return credentials, folder_id


def drive_status() -> DriveSyncResult:
    credentials, folder_id = drive_config()
    if not credentials or not folder_id:
        return DriveSyncResult(
            "setup",
            "Configure [google_drive], folder_id e service_account nos Secrets do Streamlit.",
        )
    try:
        _build_service(credentials)
    except ImportError:
        return DriveSyncResult("setup", "Dependências do Google Drive ainda não foram instaladas.")
    except Exception as exc:
        return DriveSyncResult("offline", f"Credenciais do Drive inválidas: {exc}"[:300])
    return DriveSyncResult("ready", "Google Drive configurado para backup automático.")


def sync_project_directory(project_dir: str | Path) -> DriveSyncResult:
    """Upload/update one ZIP per project. Failures never interrupt the ViralLab workflow."""
    directory = Path(project_dir)
    if not directory.is_dir():
        return DriveSyncResult("error", "Pasta do projeto não encontrada.")
    credentials, folder_id = drive_config()
    if not credentials or not folder_id:
        return DriveSyncResult("setup", "Google Drive ainda não configurado.")
    try:
        from googleapiclient.http import MediaIoBaseUpload

        service = _build_service(credentials)
        filename = f"virallab-projeto-{directory.name}.zip"
        data = _zip_directory(directory)
        existing_id = _find_file(service, folder_id, filename)
        media = MediaIoBaseUpload(io.BytesIO(data), mimetype="application/zip", resumable=False)
        if existing_id:
            result = service.files().update(fileId=existing_id, media_body=media, fields="id").execute()
        else:
            result = service.files().create(
                body={"name": filename, "parents": [folder_id]},
                media_body=media,
                fields="id",
            ).execute()
        now = datetime.now(timezone.utc).isoformat()
        _write_sync_metadata(directory, str(result.get("id", "")), now, "synced")
        return DriveSyncResult("ready", "Projeto salvo automaticamente no Google Drive.", str(result.get("id", "")), now)
    except ImportError:
        return DriveSyncResult("setup", "Instale google-api-python-client e google-auth.")
    except Exception as exc:
        _write_sync_metadata(directory, "", datetime.now(timezone.utc).isoformat(), "error", str(exc))
        return DriveSyncResult("error", f"Falha ao sincronizar com o Drive: {exc}"[:500])


def autosync_project(project_dir: str | Path) -> DriveSyncResult:
    """Best-effort autosave; intended for calls after meaningful project events."""
    return sync_project_directory(project_dir)


def _build_service(credentials: dict[str, Any]):
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    scopes = ["https://www.googleapis.com/auth/drive.file"]
    creds = Credentials.from_service_account_info(credentials, scopes=scopes)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _find_file(service: Any, folder_id: str, filename: str) -> str:
    escaped = filename.replace("'", "\\'")
    query = f"name = '{escaped}' and '{folder_id}' in parents and trashed = false"
    result = service.files().list(q=query, spaces="drive", fields="files(id,name)", pageSize=10).execute()
    files = result.get("files", [])
    return str(files[0].get("id", "")) if files else ""


def _zip_directory(directory: Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in directory.rglob("*"):
            if path.is_file() and path.name != "drive-sync.json":
                archive.write(path, arcname=f"project-{directory.name}/{path.relative_to(directory)}")
    return buffer.getvalue()


def _write_sync_metadata(directory: Path, file_id: str, synced_at: str, state: str, error: str = "") -> None:
    payload = {
        "version": "1.0",
        "state": state,
        "file_id": file_id,
        "synced_at": synced_at,
        "error": error[:500],
    }
    try:
        (directory / "drive-sync.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass
