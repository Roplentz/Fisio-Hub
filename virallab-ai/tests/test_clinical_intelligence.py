from __future__ import annotations

import json

from virallab.clinical_intelligence import (
    EvidenceReference,
    responsible_clinical_cta,
    review_video_package,
    write_clinical_safety_report,
)
from virallab.models import Scene, VideoBrief, VideoPackage


def package_with(text: str, *, evidence_level: str = "educacional") -> VideoPackage:
    return VideoPackage(
        brief=VideoBrief(
            theme="Educação em saúde",
            audience="pacientes adultos",
            evidence_level=evidence_level,
        ),
        hook="Informação responsável",
        thesis="Decisões clínicas dependem do contexto.",
        scenes=[
            Scene(
                index=1,
                start=0,
                end=10,
                scene_type="avatar",
                narration=text,
            )
        ],
    )


def test_absolute_claim_requires_review():
    report = review_video_package(package_with("Este método garante a cura."))

    assert report.status == "review"
    assert report.findings[0].code == "absolute_claim"


def test_prescription_like_instruction_blocks_publication():
    report = review_video_package(package_with("Suspenda o medicamento agora."))

    assert report.status == "block"
    assert report.findings[0].risk == "critical"


def test_clinical_number_requires_verified_evidence():
    report = review_video_package(
        package_with("O estudo mostrou melhora de 35% em 8 semanas.")
    )
    assert {item.code for item in report.findings} == {"unsupported_number"}

    verified = EvidenceReference(
        title="Ensaio clínico",
        source="PubMed",
        year=2025,
        url="https://pubmed.ncbi.nlm.nih.gov/123/",
        verified=True,
    )
    reviewed = review_video_package(
        package_with("O estudo mostrou melhora de 35% em 8 semanas."),
        evidence=[verified],
    )
    assert not reviewed.findings


def test_red_flag_adds_immediate_evaluation_notice():
    report = review_video_package(package_with("Dor no peito precisa de atenção."))

    assert any(item.code == "red_flag_context" for item in report.findings)
    assert any("imediata" in notice for notice in report.required_disclaimers)


def test_unsafe_cta_is_replaced():
    assert responsible_clinical_cta("Pare de tomar seu remédio") == (
        "Procure orientação de um profissional de saúde qualificado."
    )


def test_report_is_written_as_auditable_json(tmp_path):
    path = write_clinical_safety_report(
        package_with("Informação geral sem promessa."),
        tmp_path / "clinical-safety-report.json",
    )
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "1.0"
    assert payload["human_review_required"] is True
    assert payload["audience"] == "pacientes adultos"
