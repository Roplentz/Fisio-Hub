from __future__ import annotations

import html
import json
import shutil
import uuid
from pathlib import Path

import streamlit as st

from virallab.asset_library import AssetLibrary
from virallab.creative_assets import (
    ImageGenerationError,
    build_scene_prompt,
    generate_scene_asset,
)
from virallab.generator import export_package, generate_video_package
from virallab.learning import (
    FeedbackRecord,
    load_feedback,
    save_feedback,
    summarize_preferences,
)
from virallab.models import VideoBrief
from virallab.providers import select_provider
from virallab.renderer import RenderError, render_video
from virallab.url_ingest import URLIngestError, download_video_url

APP_ROOT = Path(__file__).resolve().parent
WORKSPACE = APP_ROOT / "workspace"
ANALYSIS_DIR = WORKSPACE / "analysis"
PROJECTS_DIR = WORKSPACE / "projects"
LEARNING_STORE = WORKSPACE / "learning" / "feedback.jsonl"
for directory in (WORKSPACE, ANALYSIS_DIR, PROJECTS_DIR, LEARNING_STORE.parent):
    directory.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="RP ViralLab Studio",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --bg:#061018; --panel:#0d1d28; --line:rgba(255,255,255,.10); --text:#f6f9fb; --muted:#91a6b4; --cyan:#45d6dc; }
    .stApp { background:radial-gradient(circle at 85% 0%,rgba(69,214,220,.15),transparent 30%),var(--bg); color:var(--text); }
    .block-container { max-width:1420px; padding-top:1.1rem; padding-bottom:4rem; }
    [data-testid="stSidebar"] { background:linear-gradient(180deg,#08151e,#0b1b26); border-right:1px solid var(--line); }
    .brand { display:flex; gap:12px; align-items:center; margin-bottom:18px; }
    .mark { width:50px; height:50px; border-radius:16px; display:grid; place-items:center; background:linear-gradient(135deg,var(--cyan),#178396); color:#031014; font-weight:900; }
    .brand-title { color:white; font-weight:900; font-size:17px; }
    .brand-sub { color:var(--muted); font-size:10px; letter-spacing:.12em; text-transform:uppercase; }
    .hero { padding:36px; border:1px solid var(--line); border-radius:28px; background:linear-gradient(135deg,rgba(20,45,59,.98),rgba(8,24,34,.97)); margin-bottom:20px; }
    .hero h1 { color:white; font-size:44px; letter-spacing:-2px; margin:.4rem 0; max-width:850px; }
    .hero p { color:#b3c4ce; font-size:16px; max-width:760px; margin:0; }
    .kicker { color:var(--cyan); font-size:11px; font-weight:900; letter-spacing:.14em; text-transform:uppercase; }
    .action-card,.scene-card,.creative-card { padding:20px; border-radius:20px; border:1px solid var(--line); background:linear-gradient(180deg,rgba(19,42,56,.95),rgba(11,27,38,.95)); margin-bottom:12px; }
    .action-card h3 { color:white; font-size:24px; margin:.5rem 0; }
    .action-card p,.muted { color:var(--muted); }
    .section-title { color:white; font-size:22px; font-weight:900; margin:8px 0 3px; }
    .section-sub { color:var(--muted); font-size:13px; margin-bottom:16px; }
    .scene-head { display:flex; justify-content:space-between; gap:10px; color:white; font-weight:800; }
    .scene-label { margin-top:10px; color:var(--muted); font-size:10px; font-weight:800; text-transform:uppercase; }
    .scene-text { color:#d8e5ea; font-size:13px; margin-top:3px; }
    .creative-status { display:inline-block; padding:5px 9px; border-radius:999px; background:rgba(69,214,220,.10); color:var(--cyan); font-size:11px; font-weight:800; }
    .stButton>button,.stDownloadButton>button { min-height:48px; border-radius:13px; font-weight:800; }
    .footer { text-align:center; color:#607784; font-size:11px; margin-top:35px; }
    @media(max-width:720px){
      .hero{padding:20px;border-radius:19px;margin-bottom:14px}
      .hero h1{font-size:28px;line-height:1.08;letter-spacing:-1px}
      .hero p{font-size:14px;line-height:1.5}
      .block-container{padding:.7rem .8rem 3rem}
      [data-testid="column"]{min-width:100%!important}
      .stTabs [data-baseweb="tab-list"]{gap:4px;overflow-x:auto}
      .stTabs [data-baseweb="tab"]{padding:0 10px;white-space:nowrap}
      .stButton>button,.stDownloadButton>button{min-height:52px}
      .action-card,.scene-card,.creative-card{padding:15px;border-radius:16px}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def project_dir(project_id: str) -> Path:
    return PROJECTS_DIR / project_id


def initialize_state() -> None:
    defaults = {
        "project_id": uuid.uuid4().hex[:10],
        "package": None,
        "package_dir": None,
        "preferred_hook": "",
        "nav_view": "Início",
        "pending_video_path": None,
        "pending_video_name": None,
        "pending_video_source": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def new_project() -> None:
    st.session_state.project_id = uuid.uuid4().hex[:10]
    st.session_state.package = None
    st.session_state.package_dir = None
    st.session_state.preferred_hook = ""


def go_to_studio() -> None:
    st.session_state.nav_view = "Studio"


def save_uploaded_file(uploaded_file, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(uploaded_file.getbuffer())
    return destination


def open_analysis(path: Path, name: str, source: str) -> None:
    st.session_state.pending_video_path = str(path)
    st.session_state.pending_video_name = name
    st.session_state.pending_video_source = source
    for key in (
        "video_analysis",
        "semantic_analysis",
        "visual_analysis",
        "multimodal_timeline",
        "upload_key",
    ):
        st.session_state.pop(key, None)
    st.switch_page("pages/01_Analisar_Video.py")


def render_scene_cards(package) -> None:
    names = {
        "avatar": "Professor RP",
        "title_card": "Tela de impacto",
        "broll": "Imagem de apoio",
        "screen_capture": "Captura de tela",
        "proof": "Prova / exemplo",
    }
    for scene in package.scenes:
        st.markdown(
            f"""
            <div class="scene-card">
              <div class="scene-head"><span>Cena {scene.index} · {names.get(scene.scene_type, scene.scene_type)}</span><span>{scene.start:.1f}–{scene.end:.1f}s</span></div>
              <div class="scene-label">Narração</div><div class="scene-text">{html.escape(scene.narration or "—")}</div>
              <div class="scene-label">Texto na tela</div><div class="scene-text">{html.escape(scene.on_screen_text or "—")}</div>
              <div class="scene-label">Direção visual</div><div class="scene-text">{html.escape(scene.visual_direction or "—")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_creative_studio(package, package_path: Path) -> None:
    library = AssetLibrary(package_path)
    all_records = library.load()
    approved_count = len([item for item in all_records if item.status == "approved"])

    st.markdown(
        '<div class="section-title">Criativos por cena</div>', unsafe_allow_html=True
    )
    st.markdown(
        '<div class="section-sub">Gere imagens intermediárias a partir do storyboard, aprove a melhor versão ou envie um material próprio.</div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    c1.metric("Cenas", len(package.scenes))
    c2.metric("Aprovadas", f"{approved_count}/{len(package.scenes)}")

    visual_style = st.selectbox(
        "Identidade visual",
        [
            "RP cinematográfico",
            "Clínico premium",
            "Editorial científico",
            "Humano documental",
            "Minimalista tecnológico",
        ],
        help="A identidade escolhida orienta os prompts de todas as cenas.",
    )

    for scene in package.scenes:
        scene_records = library.for_scene(scene.index)
        approved = next(
            (item for item in scene_records if item.status == "approved"), None
        )
        default_prompt = build_scene_prompt(
            scene, theme=package.brief.theme, visual_style=visual_style
        )

        with st.container(border=True):
            status = "✓ Criativo aprovado" if approved else "Aguardando criativo"
            st.markdown(
                f'<div class="scene-head"><span>Cena {scene.index} · {html.escape(scene.on_screen_text or scene.scene_type)}</span><span class="creative-status">{status}</span></div>',
                unsafe_allow_html=True,
            )
            st.caption(scene.visual_direction or scene.narration)

            prompt_key = f"creative-prompt-{st.session_state.project_id}-{scene.index}"
            prompt = st.text_area(
                "Prompt da imagem", value=default_prompt, height=150, key=prompt_key
            )
            generate_col, upload_col = st.columns(2)
            with generate_col:
                if st.button(
                    "🎨 Gerar imagem",
                    key=f"generate-creative-{scene.index}",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        with st.spinner(f"Criando imagem da cena {scene.index}..."):
                            generate_scene_asset(package_path, scene, prompt=prompt)
                        st.success("Imagem criada. Escolha e aprove abaixo.")
                        st.rerun()
                    except (ImageGenerationError, ValueError) as exc:
                        st.error(str(exc))
            with upload_col:
                upload = st.file_uploader(
                    "Enviar imagem ou vídeo próprio",
                    type=["mp4", "mov", "webm", "png", "jpg", "jpeg", "webp"],
                    key=f"creative-upload-{scene.index}",
                    label_visibility="collapsed",
                )
                if upload is not None and st.button(
                    "Salvar upload",
                    key=f"save-upload-{scene.index}",
                    use_container_width=True,
                ):
                    record = library.add_bytes(
                        scene_index=scene.index,
                        data=upload.getvalue(),
                        extension=Path(upload.name).suffix or ".png",
                        source="upload",
                        provider="human",
                        prompt=prompt,
                        metadata={"original_name": upload.name},
                    )
                    library.set_status(record.id, "approved")
                    st.success("Material enviado e aprovado para a cena.")
                    st.rerun()

            scene_records = library.for_scene(scene.index)
            if not scene_records:
                st.info(
                    "Ainda não há imagens nesta cena. Gere uma arte ou envie um arquivo próprio."
                )
                continue

            st.markdown("**Variações disponíveis**")
            for record in reversed(scene_records):
                path = library.resolve(record)
                with st.container(border=True):
                    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                        st.image(str(path), use_container_width=True)
                    elif path.suffix.lower() in {".mp4", ".mov", ".webm"}:
                        st.video(str(path))
                    st.caption(f"{record.source} · {record.provider} · {record.status}")
                    a, b, c = st.columns(3)
                    if a.button(
                        "⭐ Aprovar",
                        key=f"approve-{record.id}",
                        use_container_width=True,
                        disabled=record.status == "approved",
                    ):
                        library.set_status(record.id, "approved")
                        st.rerun()
                    if b.button(
                        "Rejeitar",
                        key=f"reject-{record.id}",
                        use_container_width=True,
                        disabled=record.status == "rejected",
                    ):
                        library.set_status(record.id, "rejected")
                        st.rerun()
                    c.download_button(
                        "Baixar",
                        path.read_bytes(),
                        file_name=path.name,
                        mime="application/octet-stream",
                        key=f"download-{record.id}",
                        use_container_width=True,
                    )


initialize_state()
records = load_feedback(LEARNING_STORE)
summary = summarize_preferences(records)

with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="mark">RP</div><div><div class="brand-title">ViralLab Studio</div><div class="brand-sub">Engenharia de conteúdo</div></div></div>',
        unsafe_allow_html=True,
    )
    view = st.radio(
        "Navegação",
        ["Início", "Studio", "DNA RP"],
        key="nav_view",
        label_visibility="collapsed",
    )
    if st.button("🧠 Painel Neural", use_container_width=True):
        st.switch_page("pages/04_Painel_Neural.py")
    st.divider()
    st.caption("PROJETO ATUAL")
    st.code(st.session_state.project_id)
    if st.button("＋ Novo projeto", use_container_width=True):
        new_project()
        st.rerun()
    c1, c2 = st.columns(2)
    c1.metric("Exemplos", summary["total_feedback"])
    c2.metric("Aprovação", f"{summary['approval_rate']}%")

if view == "Início":
    st.markdown(
        '<section class="hero"><div class="kicker">Engenharia reversa de conteúdo com IA</div><h1>Descubra por que um vídeo funciona. Depois, crie a sua versão original.</h1><p>Analise referências ou crie conteúdos autorais com roteiro, storyboard, criativos, vídeo e aprendizado contínuo.</p></section>',
        unsafe_allow_html=True,
    )
    left, right = st.columns([1.25, 0.75], gap="large")
    with left:
        st.markdown(
            '<div class="section-title">Analisar vídeo</div><div class="section-sub">Envie um arquivo ou cole uma URL pública.</div>',
            unsafe_allow_html=True,
        )
        upload_tab, url_tab = st.tabs(["📁 Upload", "🔗 URL"])
        with upload_tab:
            uploaded = st.file_uploader(
                "Escolha um vídeo", type=["mp4", "mov", "m4v", "webm", "mkv"]
            )
            if uploaded is not None:
                st.video(uploaded.getvalue())
                if st.button(
                    "Analisar vídeo enviado →", type="primary", use_container_width=True
                ):
                    suffix = Path(uploaded.name).suffix.lower() or ".mp4"
                    path = save_uploaded_file(
                        uploaded, ANALYSIS_DIR / f"{uuid.uuid4().hex[:10]}{suffix}"
                    )
                    open_analysis(path, uploaded.name, "upload")
        with url_tab:
            url = st.text_input("Cole a URL pública")
            if st.button(
                "Importar e analisar URL →",
                type="primary",
                use_container_width=True,
                disabled=not bool(url.strip()),
            ):
                try:
                    imported = download_video_url(url, ANALYSIS_DIR / "urls")
                    open_analysis(imported.path, imported.title, imported.source_url)
                except URLIngestError as exc:
                    st.error(str(exc))
    with right:
        st.markdown(
            '<div class="action-card"><div class="kicker">CAMINHO 02</div><h3>Criar do zero</h3><p>Comece por tema, público e objetivo.</p></div>',
            unsafe_allow_html=True,
        )
        st.button(
            "✨ Criar conteúdo do zero", use_container_width=True, on_click=go_to_studio
        )

elif view == "Studio":
    st.markdown(
        '<section class="hero"><div class="kicker">Criação orientada por estratégia</div><h1>Studio de conteúdo</h1><p>Crie, revise, gere os criativos e renderize vídeos verticais.</p></section>',
        unsafe_allow_html=True,
    )
    brief_tab, script_tab, assets_tab, render_tab = st.tabs(
        ["01 Estratégia", "02 Roteiro", "03 Criativos", "04 Render"]
    )

    with brief_tab:
        left, right = st.columns(2, gap="large")
        with left:
            theme = st.text_input("Tema central", value="IA na fisioterapia")
            audience = st.text_input("Público", value="fisioterapeutas brasileiros")
            objective = st.selectbox(
                "Objetivo",
                [
                    "ganhar seguidores qualificados",
                    "educar",
                    "gerar autoridade",
                    "vender",
                    "engajar",
                ],
            )
            duration = st.slider("Duração", 15, 90, 60, 5)
        with right:
            video_format = st.selectbox(
                "Formato",
                [
                    "professor_cinematico",
                    "lista_demonstrativa",
                    "narrativo",
                    "tutorial",
                    "case_clinico",
                ],
            )
            evidence_level = st.selectbox(
                "Base", ["educacional", "cientifico", "opiniao"]
            )
            provider_name = st.selectbox(
                "Motor de IA", ["auto", "gemini", "ollama", "local"]
            )
            cta = st.text_area(
                "Chamada para ação",
                value="Siga o Professor RP para aprender IA aplicada à saúde.",
                height=100,
            )
        if st.button(
            "Gerar roteiro e storyboard →", type="primary", use_container_width=True
        ):
            try:
                brief = VideoBrief(
                    theme=theme,
                    objective=objective,
                    audience=audience,
                    duration_seconds=duration,
                    format=video_format,
                    cta=cta,
                    evidence_level=evidence_level,
                )
                package = generate_video_package(
                    brief, provider=select_provider(provider_name)
                )
                out = project_dir(st.session_state.project_id)
                if out.exists():
                    shutil.rmtree(out)
                export_package(package, out)
                st.session_state.package = package
                st.session_state.package_dir = str(out)
                st.session_state.preferred_hook = package.hook
                st.success(
                    "Roteiro criado. Abra a aba 02 para revisar e a aba 03 para gerar as artes."
                )
            except Exception as exc:
                st.error(f"Não foi possível gerar o pacote: {exc}")

    with script_tab:
        package = st.session_state.package
        if package is None:
            st.warning("Gere um roteiro na aba Estratégia.")
        else:
            st.metric("Cenas", len(package.scenes))
            st.markdown(f"### {package.hook}")
            st.session_state.preferred_hook = st.text_area(
                "Reescreva com sua voz",
                value=st.session_state.preferred_hook or package.hook,
                height=90,
            )
            st.markdown(f"**Tese:** {package.thesis}")
            render_scene_cards(package)
            st.download_button(
                "Baixar roteiro estruturado",
                json.dumps(package.to_dict(), ensure_ascii=False, indent=2),
                "video-package.json",
                "application/json",
                use_container_width=True,
            )

    with assets_tab:
        package = st.session_state.package
        package_path = (
            Path(st.session_state.package_dir) if st.session_state.package_dir else None
        )
        if package is None or package_path is None:
            st.warning("Gere um roteiro antes de criar as artes.")
        else:
            render_creative_studio(package, package_path)

    with render_tab:
        package_path = (
            Path(st.session_state.package_dir) if st.session_state.package_dir else None
        )
        if package_path is None:
            st.warning("Crie um projeto antes de renderizar.")
        else:
            library = AssetLibrary(package_path)
            approved = [item for item in library.load() if item.status == "approved"]
            st.metric("Criativos aprovados", len(approved))
            if not approved:
                st.warning(
                    "Aprove pelo menos um criativo na aba 03 antes de renderizar."
                )
            burn_captions = st.checkbox("Legendas incorporadas", value=True)
            music_level = st.slider("Trilha (dB)", -40, -12, -25)
            dry_run = st.checkbox("Simular sem MP4", value=False)
            if st.button(
                "Renderizar vídeo vertical →", type="primary", use_container_width=True
            ):
                try:
                    video = render_video(
                        package_path,
                        dry_run=dry_run,
                        burn_captions=burn_captions,
                        music_level_db=music_level,
                    )
                    if dry_run:
                        st.success("Plano técnico gerado.")
                    elif video.exists():
                        st.video(str(video))
                        st.download_button(
                            "Baixar vídeo final",
                            video.read_bytes(),
                            "video-final.mp4",
                            "video/mp4",
                            use_container_width=True,
                        )
                except RenderError as exc:
                    st.error(str(exc))

else:
    st.markdown(
        '<section class="hero"><div class="kicker">Memória editorial auditável</div><h1>DNA RP</h1><p>Registre escolhas que orientarão as próximas gerações.</p></section>',
        unsafe_allow_html=True,
    )
    k1, k2, k3 = st.columns(3)
    k1.metric("Feedbacks", summary["total_feedback"])
    k2.metric("Aprovação", f"{summary['approval_rate']}%")
    k3.metric("Nota média", summary["average_rating"])
    package = st.session_state.package
    if package is None:
        st.warning("Crie um roteiro para registrar um aprendizado contextual.")
    else:
        rating = st.slider("Qualidade do roteiro", 1, 10, 8)
        approved = st.checkbox("Eu publicaria esta estrutura", value=True)
        preferred_style = st.selectbox(
            "Direção a reforçar",
            [
                "Professor Cinemático",
                "Mais científico",
                "Mais direto",
                "Mais emocional",
                "Mais comercial",
            ],
        )
        notes = st.text_area("O que o ViralLab deve aprender?", height=140)
        if st.button("Salvar no DNA RP", type="primary", use_container_width=True):
            save_feedback(
                FeedbackRecord(
                    project_id=st.session_state.project_id,
                    theme=package.brief.theme,
                    rating=rating,
                    approved=approved,
                    original_hook=package.hook,
                    preferred_hook=st.session_state.preferred_hook or package.hook,
                    notes=notes,
                    preferred_style=preferred_style,
                ),
                LEARNING_STORE,
            )
            st.success("Aprendizado registrado.")
            st.rerun()
    if records:
        st.download_button(
            "Exportar DNA RP",
            "\n".join(json.dumps(item, ensure_ascii=False) for item in records),
            "dna-rp-feedback.jsonl",
            "application/x-ndjson",
        )

st.markdown(
    '<div class="footer">RP ViralLab Studio · Conteúdo original, revisão humana e engenharia reversa ética.</div>',
    unsafe_allow_html=True,
)
