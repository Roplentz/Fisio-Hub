"""Componentes visuais reutilizáveis do RP ViralLab Studio."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

PAGE_TITLE = "RP ViralLab Studio 3.0"
PAGE_ICON = "◉"
HERO_HTML = (
    '<section class="hero"><div class="kicker">Estúdio inteligente de conteúdo</div>'
    '<h1>RP ViralLab Studio 3.0</h1><p>Analisar vídeo → estratégia → roteiro → '
    'Avatar IA → voz → criativos → render → publicação → aprendizado.</p></section>'
)
FOOTER_TEXT = "RP ViralLab Studio 3.0 · Identidade autorizada, conteúdo original e revisão humana."
THEME_CSS = """
<style>
:root{--bg:#061018;--panel:#0d1d28;--line:rgba(255,255,255,.10);--text:#f6f9fb;--muted:#91a6b4;--cyan:#45d6dc;--gold:#d8b56d}
.stApp{background:radial-gradient(circle at 85% 0%,rgba(69,214,220,.14),transparent 30%),var(--bg);color:var(--text)}
.block-container{max-width:1160px;padding-top:.8rem;padding-bottom:5rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#08151e,#0b1b26);border-right:1px solid var(--line)}
.hero{padding:30px;border:1px solid var(--line);border-radius:26px;background:linear-gradient(135deg,rgba(20,45,59,.98),rgba(8,24,34,.97));margin-bottom:18px}
.hero h1{color:white;font-size:42px;line-height:1.08;letter-spacing:-2px;margin:.35rem 0}.hero p{color:#b3c4ce;margin:0;line-height:1.55}
.kicker{color:var(--cyan);font-size:11px;font-weight:900;letter-spacing:.14em;text-transform:uppercase}
.choice,.scene-card,.status-card{padding:18px;border-radius:18px;border:1px solid var(--line);background:rgba(13,29,40,.92);margin-bottom:10px}
.choice h3{margin:.15rem 0 .35rem;color:white}.choice p{color:var(--muted);margin:0}
.scene-head{display:flex;justify-content:space-between;gap:10px;color:white;font-weight:800}.scene-label{margin-top:9px;color:var(--muted);font-size:10px;font-weight:800;text-transform:uppercase}.scene-text{color:#d8e5ea;font-size:13px;margin-top:3px}
.stButton>button,.stDownloadButton>button{min-height:50px;border-radius:13px;font-weight:800}
div[data-baseweb="select"]>div{min-height:52px;border-radius:14px}
@media(max-width:720px){.block-container{padding:.45rem .75rem 6rem}.hero{padding:18px;border-radius:19px}.hero h1{font-size:27px;letter-spacing:-1px}.hero p{font-size:14px}[data-testid="column"]{min-width:100%!important}.scene-head{display:block}h1,h2,h3{overflow-wrap:anywhere}}
</style>
"""


def configure_page(ui: Any) -> None:
    """Configura metadados e tema global da aplicação."""
    ui.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    ui.markdown(THEME_CSS, unsafe_allow_html=True)


def render_sidebar(
    ui: Any,
    state: Mapping[str, Any],
    summary: Mapping[str, Any],
    on_new_project: Callable[[], None],
) -> None:
    """Renderiza a barra lateral sem conhecer regras internas do projeto."""
    with ui.sidebar:
        ui.markdown("## ◉ RP ViralLab 3.0")
        ui.caption("Estúdio de conteúdo com memória")
        ui.code(state["project_id"])
        if ui.button("＋ Novo projeto", use_container_width=True):
            on_new_project()
            ui.rerun()
        ui.metric("Taxa de aprovação", f"{summary['approval_rate']}%")


def render_hero(ui: Any) -> None:
    ui.markdown(HERO_HTML, unsafe_allow_html=True)


def render_progress(ui: Any, value: float) -> None:
    ui.progress(value)


def render_footer(ui: Any) -> None:
    ui.caption(FOOTER_TEXT)


__all__ = [
    "FOOTER_TEXT",
    "HERO_HTML",
    "PAGE_ICON",
    "PAGE_TITLE",
    "THEME_CSS",
    "configure_page",
    "render_footer",
    "render_hero",
    "render_progress",
    "render_sidebar",
]
