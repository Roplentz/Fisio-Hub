from __future__ import annotations

import html
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class ScriptResult:
    """State changes requested by the script step."""

    preferred_hook: str
    continue_to_avatar: bool = False


def render_scene_cards(st, package) -> None:
    """Render storyboard scene cards without touching application state."""

    labels = {
        "avatar": "Autor",
        "title_card": "Impacto",
        "broll": "Apoio",
        "screen_capture": "Tela",
        "proof": "Prova",
    }
    for scene in package.scenes:
        st.markdown(
            f'<div class="scene-card"><div class="scene-head"><span>Cena {scene.index} · {labels.get(scene.scene_type, scene.scene_type)}</span><span>{scene.start:.1f}–{scene.end:.1f}s</span></div><div class="scene-label">Narração</div><div class="scene-text">{html.escape(scene.narration or "—")}</div><div class="scene-label">Texto na tela</div><div class="scene-text">{html.escape(scene.on_screen_text or "—")}</div><div class="scene-label">Direção visual</div><div class="scene-text">{html.escape(scene.visual_direction or "—")}</div></div>',
            unsafe_allow_html=True,
        )


def render_script(st, package, *, preferred_hook: str = "") -> ScriptResult:
    """Render the script and return the state changes requested by the user."""

    st.subheader("Roteiro")
    st.metric("Cenas", len(package.scenes))
    hook = st.text_area("Gancho", value=preferred_hook or package.hook)
    st.markdown(f"**Tese:** {package.thesis}")
    render_scene_cards(st, package)
    st.download_button(
        "Baixar roteiro",
        json.dumps(package.to_dict(), ensure_ascii=False, indent=2),
        "video-package.json",
        "application/json",
        use_container_width=True,
    )
    continue_to_avatar = st.button(
        "Continuar para Avatar IA →",
        type="primary",
        use_container_width=True,
    )
    return ScriptResult(
        preferred_hook=hook,
        continue_to_avatar=continue_to_avatar,
    )
