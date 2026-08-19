from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from .models import VideoPackage


ReviewStatus = Literal["pass", "review", "block"]
ClaimRisk = Literal["low", "moderate", "high", "critical"]

_ABSOLUTE_PATTERNS = (
    r"\bcura(?:r|do|da)?\b",
    r"\bgarant(?:e|ia|ido|ida)\b",
    r"\b100\s*%",
    r"\bsem risco\b",
    r"\bresultado(?:s)? definitivo(?:s)?\b",
    r"\bfunciona para todo(?:s| mundo)\b",
)
_PRESCRIPTION_PATTERNS = (
    r"\bpare de tomar\b",
    r"\bsuspenda (?:o |a )?medicamento\b",
    r"\bfaça este exercício \d+ vezes\b",
    r"\buse esta dose\b",
)
_EMERGENCY_PATTERNS = (
    r"\bdor no peito\b",
    r"\bfalta de ar intensa\b",
    r"\bperda súbita de força\b",
    r"\bdesmaio\b",
)
_CITATION_PATTERN = re.compile(r"(?:doi:\s*10\.|https?://|pmid:\s*\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class EvidenceReference:
    title: str
    source: str
    year: int | None = None
    url: str = ""
    doi: str = ""
    evidence_type: str = ""
    verified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClaimFinding:
    scene_index: int
    text: str
    risk: ClaimRisk
    code: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ClinicalSafetyReport:
    status: ReviewStatus
    audience: str
    findings: list[ClaimFinding] = field(default_factory=list)
    evidence: list[EvidenceReference] = field(default_factory=list)
    required_disclaimers: list[str] = field(default_factory=list)
    responsible_cta: str = ""
    human_review_required: bool = True
    schema_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "findings": [item.to_dict() for item in self.findings],
            "evidence": [item.to_dict() for item in self.evidence],
        }


def review_video_package(
    package: VideoPackage,
    *,
    evidence: list[EvidenceReference] | None = None,
) -> ClinicalSafetyReport:
    """Revisa alegações sem declarar verdade clínica automaticamente.

    O mecanismo é deliberadamente conservador: identifica padrões de risco,
    exige revisão humana e nunca transforma ausência de alerta em validação
    científica.
    """

    references = list(evidence or [])
    findings: list[ClaimFinding] = []
    for scene in package.scenes:
        text = " ".join(
            part.strip()
            for part in (scene.narration, scene.on_screen_text)
            if part and part.strip()
        )
        findings.extend(_review_text(text, scene.index, references))

    audience = package.brief.audience.strip() or "público não especificado"
    disclaimers = _disclaimers_for(package, findings)
    responsible_cta = responsible_clinical_cta(package.brief.cta)
    status: ReviewStatus = "pass"
    if any(item.risk == "critical" for item in findings):
        status = "block"
    elif findings or package.brief.evidence_level == "cientifico":
        status = "review"

    return ClinicalSafetyReport(
        status=status,
        audience=audience,
        findings=findings,
        evidence=references,
        required_disclaimers=disclaimers,
        responsible_cta=responsible_cta,
    )


def responsible_clinical_cta(cta: str) -> str:
    clean = " ".join(cta.split()).strip()
    if not clean:
        return "Procure orientação de um profissional de saúde qualificado."
    if any(re.search(pattern, clean, re.IGNORECASE) for pattern in _PRESCRIPTION_PATTERNS):
        return "Procure orientação de um profissional de saúde qualificado."
    return clean[:240]


def write_clinical_safety_report(
    package: VideoPackage,
    destination: str | Path,
    *,
    evidence: list[EvidenceReference] | None = None,
) -> Path:
    report = review_video_package(package, evidence=evidence)
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target


def _review_text(
    text: str,
    scene_index: int,
    evidence: list[EvidenceReference],
) -> list[ClaimFinding]:
    if not text:
        return []
    findings: list[ClaimFinding] = []
    for pattern in _ABSOLUTE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            findings.append(
                ClaimFinding(
                    scene_index=scene_index,
                    text=text,
                    risk="high",
                    code="absolute_claim",
                    message="Alegação absoluta ou garantia exige reformulação.",
                )
            )
            break
    for pattern in _PRESCRIPTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            findings.append(
                ClaimFinding(
                    scene_index=scene_index,
                    text=text,
                    risk="critical",
                    code="unsafe_prescription",
                    message="Orientação individual ou medicamentosa não pode ser publicada neste formato.",
                )
            )
            break
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in _EMERGENCY_PATTERNS):
        findings.append(
            ClaimFinding(
                scene_index=scene_index,
                text=text,
                risk="moderate",
                code="red_flag_context",
                message="Sintoma de alerta exige orientação clara para avaliação imediata.",
            )
        )
    if re.search(r"\b\d+(?:[.,]\d+)?\s*(?:%|vezes|dias|semanas|meses)\b", text, re.IGNORECASE):
        has_verified_reference = any(item.verified for item in evidence)
        has_inline_citation = bool(_CITATION_PATTERN.search(text))
        if not (has_verified_reference or has_inline_citation):
            findings.append(
                ClaimFinding(
                    scene_index=scene_index,
                    text=text,
                    risk="moderate",
                    code="unsupported_number",
                    message="Número clínico requer fonte rastreável e verificada.",
                )
            )
    return findings


def _disclaimers_for(
    package: VideoPackage,
    findings: list[ClaimFinding],
) -> list[str]:
    notices = ["Conteúdo educativo; não substitui avaliação individual."]
    if package.brief.evidence_level == "cientifico":
        notices.append("Referências devem ser verificadas antes da publicação.")
    if any(item.code == "red_flag_context" for item in findings):
        notices.append("Sintomas de alerta exigem avaliação profissional imediata.")
    return notices
