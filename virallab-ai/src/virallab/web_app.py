from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from decimal import Decimal
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from uuid import uuid4

from .clinical_intelligence import review_video_package
from .commercial import CommercialLedger, InsufficientCredits, estimate_credits
from .generator import generate_video_package
from .models import VideoBrief
from .providers import select_provider

MAX_BODY_BYTES = 32_768
ACCOUNT_ID = "web-demo"


@dataclass
class WebAppService:
    ledger: CommercialLedger

    @classmethod
    def create(cls, data_dir: str | Path) -> "WebAppService":
        ledger = CommercialLedger(Path(data_dir) / "commercial.db")
        ledger.create_account(ACCOUNT_ID, plan_id="creator")
        return cls(ledger)

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "fisio-ia-creator",
            "balance": self.ledger.balance(ACCOUNT_ID),
        }

    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        theme = _required_text(payload, "theme", max_length=240)
        audience = _text(payload, "audience", "fisioterapeutas brasileiros", 160)
        objective = _text(payload, "objective", "educar e gerar confiança", 160)
        duration = _duration(payload.get("duration_seconds", 30))
        provider_name = _text(payload, "provider", "auto", 24).lower()
        project_id = f"web_{uuid4().hex}"

        reservation = self.ledger.reserve(
            ACCOUNT_ID,
            project_id=project_id,
            kind="script",
            estimated_cost_brl=Decimal("0.02"),
        )
        try:
            brief = VideoBrief(
                theme=theme,
                audience=audience,
                objective=objective,
                duration_seconds=duration,
                format="professor_cinematico",
                cta="Se os sintomas persistirem, procure avaliação de um fisioterapeuta.",
                evidence_level="educacional",
                creative_style="professor_rp",
            )
            package = generate_video_package(
                brief, provider=select_provider(provider_name)
            )
            report = review_video_package(package)
            self.ledger.complete(reservation.event_id)
        except Exception:
            self.ledger.fail_and_refund(reservation.event_id)
            raise

        return {
            "project_id": project_id,
            "package": package.to_dict(),
            "safety": report.to_dict(),
            "balance": self.ledger.balance(ACCOUNT_ID),
            "credits_used": reservation.credits,
        }

    def render_preview(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_id = _required_text(payload, "project_id", max_length=100)
        duration = _duration(payload.get("duration_seconds", 30))
        if _text(payload, "safety_status", "block", 12) == "block":
            raise ValueError("Conteúdo bloqueado pela verificação clínica.")

        quantities = (
            ("image", Decimal("1"), Decimal("0.05")),
            ("tts_minute", Decimal(str(duration)) / Decimal("60"), Decimal("0.03")),
            ("render_minute", Decimal(str(duration)) / Decimal("60"), Decimal("0.04")),
        )
        estimated = sum(
            estimate_credits(kind, quantity) for kind, quantity, _cost in quantities
        )
        if self.ledger.balance(ACCOUNT_ID) < estimated:
            raise InsufficientCredits("Saldo insuficiente para gerar a prévia.")

        reservations = []
        try:
            for kind, quantity, cost in quantities:
                reservations.append(
                    self.ledger.reserve(
                        ACCOUNT_ID,
                        project_id=project_id,
                        kind=kind,
                        quantity=quantity,
                        estimated_cost_brl=cost,
                    )
                )
            for event in reservations:
                self.ledger.complete(event.event_id)
        except Exception:
            for event in reservations:
                try:
                    self.ledger.fail_and_refund(event.event_id)
                except ValueError:
                    pass
            raise

        return {
            "status": "preview_ready",
            "project_id": project_id,
            "balance": self.ledger.balance(ACCOUNT_ID),
            "credits_used": sum(event.credits for event in reservations),
            "notice": "Prévia lógica concluída; renderização MP4 entra na próxima etapa.",
        }


def _required_text(payload: dict[str, Any], key: str, *, max_length: int) -> str:
    value = str(payload.get(key, "")).strip()
    if not value:
        raise ValueError(f"Campo obrigatório: {key}.")
    if len(value) > max_length:
        raise ValueError(f"Campo {key} excede {max_length} caracteres.")
    return value


def _text(payload: dict[str, Any], key: str, default: str, max_length: int) -> str:
    value = str(payload.get(key, default)).strip() or default
    if len(value) > max_length:
        raise ValueError(f"Campo {key} excede {max_length} caracteres.")
    return value


def _duration(value: Any) -> int:
    try:
        duration = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Duração inválida.") from exc
    if duration not in {30, 45, 60}:
        raise ValueError("A duração deve ser 30, 45 ou 60 segundos.")
    return duration


def build_handler(service: WebAppService, static_dir: str | Path):
    directory = str(Path(static_dir).resolve())

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

        def do_GET(self) -> None:
            if self.path == "/api/health":
                self._json(HTTPStatus.OK, service.health())
                return
            super().do_GET()

        def do_POST(self) -> None:
            try:
                payload = self._payload()
                if self.path == "/api/generate":
                    response = service.generate(payload)
                elif self.path == "/api/render-preview":
                    response = service.render_preview(payload)
                else:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "Rota não encontrada."})
                    return
                self._json(HTTPStatus.OK, response)
            except (ValueError, KeyError, InsufficientCredits) as exc:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            except Exception:
                self._json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": "Não foi possível concluir a operação."},
                )

        def _payload(self) -> dict[str, Any]:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise ValueError("Content-Length inválido.") from exc
            if length <= 0 or length > MAX_BODY_BYTES:
                raise ValueError("Corpo da requisição vazio ou muito grande.")
            try:
                data = json.loads(self.rfile.read(length))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise ValueError("JSON inválido.") from exc
            if not isinstance(data, dict):
                raise ValueError("O corpo deve ser um objeto JSON.")
            return data

        def _json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            if os.getenv("VIRALLAB_WEB_QUIET") != "1":
                super().log_message(format, *args)

    return Handler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fisio IA Creator web local")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument(
        "--data-dir",
        default=os.getenv("VIRALLAB_WEB_DATA_DIR", "workspace/web-demo"),
    )
    args = parser.parse_args(argv)
    static_dir = Path(__file__).resolve().parents[2] / "web-demo"
    service = WebAppService.create(args.data_dir)
    server = ThreadingHTTPServer(
        (args.host, args.port), build_handler(service, static_dir)
    )
    print(f"Fisio IA Creator disponível em http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
