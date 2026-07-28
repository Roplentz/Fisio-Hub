from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any


class PublicationAction(str, Enum):
    NONE = "none"
    GO_TO_LEARNING = "go_to_learning"


@dataclass(frozen=True)
class PublicationPackage:
    title: str
    caption: str
    hashtags: str

    def to_dict(self) -> dict[str, str]:
        return {
            "title": self.title,
            "caption": self.caption,
            "hashtags": self.hashtags,
        }


@dataclass(frozen=True)
class PublicationResult:
    """Resultado produzido pela etapa de publicação."""

    action: PublicationAction = PublicationAction.NONE
    publication: PublicationPackage | None = None


def render_publication(st: Any, package: Any | None) -> PublicationResult:
    """Renderiza e exporta o pacote de publicação sem acessar o estado da sessão."""

    st.subheader("Pacote de publicação")
    if package is None:
        st.warning("Crie o roteiro primeiro.")
        return PublicationResult()

    publication = PublicationPackage(
        title=st.text_input("Título", value=package.hook),
        caption=st.text_area(
            "Legenda",
            value=f"{package.thesis}\n\n{package.brief.cta}",
            height=180,
        ),
        hashtags=st.text_input(
            "Hashtags",
            value="#fisioterapia #inteligenciaartificial #inovacaoemsaude",
        ),
    )
    st.download_button(
        "Baixar pacote de publicação",
        json.dumps(publication.to_dict(), ensure_ascii=False, indent=2),
        "publication-package.json",
        "application/json",
        use_container_width=True,
    )

    if st.button(
        "Continuar para Aprendizado →",
        type="primary",
        use_container_width=True,
    ):
        return PublicationResult(
            action=PublicationAction.GO_TO_LEARNING,
            publication=publication,
        )
    return PublicationResult(publication=publication)


__all__ = [
    "PublicationAction",
    "PublicationPackage",
    "PublicationResult",
    "render_publication",
]
