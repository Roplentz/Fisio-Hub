from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

from virallab.avatar_master import AvatarMasterStore, ImageGenerationError


class AvatarAction(str, Enum):
    NONE = "none"
    RERUN = "rerun"
    GO_TO_VOICE = "go_to_voice"


@dataclass(frozen=True)
class AvatarResult:
    """State changes requested by the avatar step."""

    action: AvatarAction = AvatarAction.NONE
    candidate_path: Path | None = None
    clear_candidate: bool = False


def render_avatar(
    st,
    workspace: Path,
    *,
    candidate_path: Path | None = None,
    store_factory: Callable[[Path], AvatarMasterStore] = AvatarMasterStore,
) -> AvatarResult:
    """Render avatar management without reading or mutating session state."""

    store = store_factory(workspace)
    profile = store.load()
    st.subheader("Avatar IA — Imagem Mestre")
    st.caption("Envie apenas três fotos recentes. A Imagem Mestre será aprovada por você antes de ser usada nos criativos.")
    st.info("Boa iluminação, fundo neutro, rosto visível, sem boné ou óculos escuros e expressão neutra.")

    if profile and profile.approved and profile.master_image_path:
        st.success(f"Imagem Mestre ativa · versão {profile.version}")
        st.image(profile.master_image_path, caption=f"{profile.name} · {profile.role}", use_container_width=True)
        replace_col, continue_col = st.columns(2)
        if replace_col.button("Substituir as três fotos", use_container_width=True):
            store.delete()
            return AvatarResult(action=AvatarAction.RERUN, clear_candidate=True)
        if continue_col.button("Continuar para Voz →", type="primary", use_container_width=True):
            return AvatarResult(action=AvatarAction.GO_TO_VOICE)
        return AvatarResult()

    name = st.text_input("Nome do avatar", value=profile.name if profile else "Prof. Dr. Rodrigo Plentz")
    role = st.text_input("Papel", value=profile.role if profile else "Autor e especialista")
    notes = st.text_area(
        "Diretrizes visuais",
        value=profile.visual_notes if profile else "Aparência profissional, segura e acolhedora; preservar rosto, cabelo e idade aparente.",
    )
    front, left, right = st.columns(3)
    front_photo = front.file_uploader("Foto de frente", type=["png", "jpg", "jpeg", "webp"], key="avatar-front")
    left_photo = left.file_uploader("Lado esquerdo", type=["png", "jpg", "jpeg", "webp"], key="avatar-left")
    right_photo = right.file_uploader("Lado direito", type=["png", "jpg", "jpeg", "webp"], key="avatar-right")
    consent = st.checkbox("Confirmo que as fotos são minhas e autorizo seu uso para criar minha Imagem Mestre.")
    complete = all((front_photo, left_photo, right_photo)) and consent

    if st.button("Salvar fotos e criar Imagem Mestre", type="primary", use_container_width=True, disabled=not complete):
        try:
            store.save_references(
                name=name,
                role=role,
                photos={
                    "front": (front_photo.getvalue(), front_photo.name, front_photo.type),
                    "left": (left_photo.getvalue(), left_photo.name, left_photo.type),
                    "right": (right_photo.getvalue(), right_photo.name, right_photo.type),
                },
                visual_notes=notes,
                consent_confirmed=consent,
            )
            with st.spinner("Criando a Imagem Mestre a partir dos três ângulos..."):
                generated = Path(store.generate_candidate())
            return AvatarResult(action=AvatarAction.RERUN, candidate_path=generated)
        except (ValueError, ImageGenerationError) as exc:
            st.error(str(exc))

    if candidate_path and candidate_path.exists():
        st.markdown("### Candidata à Imagem Mestre")
        st.image(str(candidate_path), use_container_width=True)
        approve, regenerate = st.columns(2)
        if approve.button("✓ Aprovar Imagem Mestre", type="primary", use_container_width=True):
            store.approve_candidate(candidate_path)
            st.success("Imagem Mestre aprovada e ativada.")
            return AvatarResult(action=AvatarAction.RERUN, clear_candidate=True)
        if regenerate.button("Gerar outra versão", use_container_width=True):
            try:
                with st.spinner("Gerando outra versão..."):
                    generated = Path(store.generate_candidate())
                return AvatarResult(action=AvatarAction.RERUN, candidate_path=generated)
            except (ValueError, ImageGenerationError) as exc:
                st.error(str(exc))

    return AvatarResult()
