"""Interface e caso de uso da etapa de estratégia editorial."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from virallab.generator import export_package, generate_video_package
from virallab.models import VideoBrief
from virallab.providers import select_provider


@dataclass(frozen=True, slots=True)
class StrategyResult:
    """Resultado que o runtime deve aplicar ao estado da sessão."""

    package: Any
    output_directory: Path


ProjectDirFactory = Callable[[str], Path]
ProviderSelector = Callable[[str], Any]
PackageGenerator = Callable[..., Any]
PackageExporter = Callable[[Any, Path], Any]


def render_strategy(
    st: Any,
    *,
    project_id: str,
    project_dir_factory: ProjectDirFactory,
    provider_selector: ProviderSelector = select_provider,
    package_generator: PackageGenerator = generate_video_package,
    package_exporter: PackageExporter = export_package,
) -> StrategyResult | None:
    """Renderiza o formulário e devolve o resultado sem alterar a sessão."""

    st.subheader("Estratégia")
    left, right = st.columns(2, gap="large")
    with left:
        theme = st.text_input("Tema", value="IA na fisioterapia")
        audience = st.text_input("Público", value="fisioterapeutas brasileiros")
        objective = st.selectbox(
            "Objetivo",
            ["ganhar seguidores qualificados", "educar", "gerar autoridade", "vender", "engajar"],
        )
        duration = st.slider("Duração", 15, 90, 60, 5)
    with right:
        fmt = st.selectbox(
            "Formato",
            ["professor_cinematico", "lista_demonstrativa", "narrativo", "tutorial", "case_clinico"],
        )
        evidence = st.selectbox("Base", ["educacional", "cientifico", "opiniao"])
        provider_name = st.selectbox("Motor de IA", ["auto", "gemini", "ollama", "local"])
        cta = st.text_area("CTA", value="Siga o Professor RP para aprender IA aplicada à saúde.")

    if not st.button("Gerar roteiro e storyboard →", type="primary", use_container_width=True):
        return None

    try:
        brief = VideoBrief(
            theme=theme,
            objective=objective,
            audience=audience,
            duration_seconds=duration,
            format=fmt,
            cta=cta,
            evidence_level=evidence,
        )
        provider = provider_selector(provider_name)
        package = package_generator(brief, provider=provider)
        output_directory = project_dir_factory(project_id)
        if output_directory.exists():
            shutil.rmtree(output_directory)
        package_exporter(package, output_directory)
        return StrategyResult(package=package, output_directory=output_directory)
    except Exception as exc:
        st.error(f"Não foi possível gerar: {exc}")
        return None


__all__ = ["StrategyResult", "render_strategy"]
