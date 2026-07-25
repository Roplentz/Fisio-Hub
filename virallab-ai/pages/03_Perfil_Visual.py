from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_ROOT = Path(__file__).resolve().parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from virallab.author_profile import AuthorProfileStore

WORKSPACE = APP_ROOT / "workspace"
STORE = AuthorProfileStore(WORKSPACE)

st.set_page_config(
    page_title="Perfil Visual · RP ViralLab",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root { --bg:#061018; --line:rgba(255,255,255,.10); --cyan:#45d6dc; --muted:#91a6b4; }
    .stApp { background:radial-gradient(circle at 90% 0%,rgba(69,214,220,.14),transparent 30%),var(--bg); }
    .block-container { max-width:960px; padding-top:1.1rem; padding-bottom:4rem; }
    .head { border:1px solid var(--line); background:linear-gradient(135deg,#142d3b,#091a24); padding:30px; border-radius:27px; margin-bottom:18px; }
    .head h1 { color:white; margin:.4rem 0; font-size:40px; letter-spacing:-1.7px; }
    .head p { color:#b4c5cf; margin:0; max-width:760px; }
    .kicker { color:var(--cyan); font-size:11px; font-weight:900; letter-spacing:.13em; text-transform:uppercase; }
    .stButton>button { min-height:50px; border-radius:14px; font-weight:850; }
    @media(max-width:720px){.head{padding:22px}.head h1{font-size:30px}.block-container{padding-left:1rem;padding-right:1rem}}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<section class="head"><div class="kicker">Memória visual do autor</div><h1>Seu rosto como personagem recorrente</h1><p>Salve uma foto de referência uma única vez. Nas cenas do tipo “Professor RP”, o ViralLab usará essa imagem para preservar a identidade do autor entre diferentes criativos e projetos.</p></section>',
    unsafe_allow_html=True,
)

profile = STORE.load()
if profile:
    left, right = st.columns([0.42, 0.58], gap="large")
    with left:
        st.image(
            profile.image_path, caption="Referência ativa", use_container_width=True
        )
    with right:
        st.success("Perfil visual ativo")
        st.markdown(f"### {profile.name}")
        st.write(profile.role)
        if profile.visual_notes:
            st.caption(profile.visual_notes)
        st.info(
            "As próximas imagens de avatar usarão esta fotografia como referência de identidade."
        )
        if st.button("Remover perfil visual", use_container_width=True):
            STORE.delete()
            st.rerun()
    st.divider()

st.subheader("Cadastrar ou substituir o autor")
st.caption(
    "Use uma foto frontal, nítida, bem iluminada e sem outras pessoas. A imagem é usada como referência, não como arquivo público."
)

name = st.text_input(
    "Nome do autor", value=profile.name if profile else "Prof. Dr. Rodrigo Plentz"
)
role = st.selectbox(
    "Função visual",
    ["Autor do canal", "Especialista", "Professor", "Personagem recorrente", "Outro"],
    index=0,
)
notes = st.text_area(
    "Diretrizes permanentes",
    value=profile.visual_notes
    if profile
    else "Fisioterapeuta e professor experiente; expressão segura e acolhedora; aparência natural; roupas profissionais contemporâneas.",
    height=110,
)
uploaded = st.file_uploader("Foto de referência", type=["png", "jpg", "jpeg", "webp"])

if uploaded is not None:
    st.image(uploaded.getvalue(), caption="Pré-visualização", width=320)

if st.button(
    "Salvar como modelo do autor",
    type="primary",
    use_container_width=True,
    disabled=uploaded is None,
):
    try:
        STORE.save(
            name=name,
            role=role,
            image_bytes=uploaded.getvalue(),
            extension=Path(uploaded.name).suffix or ".jpg",
            mime_type=uploaded.type or "image/jpeg",
            visual_notes=notes,
        )
        st.success(
            "Perfil visual salvo. Ele já será usado nas próximas cenas de avatar."
        )
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))

st.divider()
st.page_link("app.py", label="Voltar ao Studio", icon="↩️")
