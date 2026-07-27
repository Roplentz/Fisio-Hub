from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def wait_for_health(url: str, process: subprocess.Popen[str], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(
                f"Streamlit encerrou antes do healthcheck (código {process.returncode}).\n{output}"
            )

        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                body = response.read().decode("utf-8", errors="replace").strip()
                if response.status == 200 and body.lower() == "ok":
                    return
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = exc

        time.sleep(1)

    output = process.stdout.read() if process.stdout and process.poll() is not None else ""
    raise TimeoutError(
        f"Healthcheck não respondeu em {timeout:.0f}s. Último erro: {last_error}.\n{output}"
    )


def check_root(url: str) -> None:
    with urllib.request.urlopen(url, timeout=10) as response:
        body = response.read().decode("utf-8", errors="replace")
        if response.status != 200:
            raise RuntimeError(f"Página raiz respondeu HTTP {response.status}.")
        if "streamlit" not in body.lower():
            raise RuntimeError("A página raiz não retornou o shell esperado do Streamlit.")


def terminate(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return

    if os.name == "nt":
        process.terminate()
    else:
        os.killpg(process.pid, signal.SIGTERM)

    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inicializa o Streamlit e valida HTTP/healthcheck.")
    parser.add_argument("--app", default="app.py")
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument("--timeout", type=float, default=90)
    args = parser.parse_args()

    app_path = Path(args.app).resolve()
    if not app_path.is_file():
        raise FileNotFoundError(f"Entrypoint não encontrado: {app_path}")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.headless=true",
        f"--server.port={args.port}",
        "--server.address=127.0.0.1",
        "--browser.gatherUsageStats=false",
    ]

    popen_kwargs: dict[str, object] = {
        "cwd": str(app_path.parent),
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "text": True,
    }
    if os.name != "nt":
        popen_kwargs["start_new_session"] = True

    process = subprocess.Popen(command, **popen_kwargs)
    try:
        wait_for_health(
            f"http://127.0.0.1:{args.port}/_stcore/health",
            process,
            args.timeout,
        )
        check_root(f"http://127.0.0.1:{args.port}/")
        print("ViralLab Streamlit smoke: OK")
        return 0
    finally:
        terminate(process)


if __name__ == "__main__":
    raise SystemExit(main())
