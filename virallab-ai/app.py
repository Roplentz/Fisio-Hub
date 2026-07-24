from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import streamlit as st

from virallab.generator import export_package, generate_video_package
from virallab.learning import FeedbackRecord, load_feedback, save_feedback, summarize_preferences
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

st.set_page_config(page_title="RP ViralLab Studio", page_icon="◉", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    :root { --bg:#061018; --panel:#0d1d28; --panel2:#132a38; --line:rgba(255,255,255,.10); --text:#f6f9fb; --muted:#91a6b4; --cyan:#45d6dc; --gold:#d8b96f; --green:#78dfa5; }
    html, body, [class*="css"] { font-family:'Inter',sans-serif; }
    .stApp { background:radial-gradient(circle at 85% 0%,rgba(69,214,220,.15),transparent 30%),radial-gradient(circle at 10% 20%,rgba(216,185,111,.08),transparent 25%),var(--bg); color:var(--text); }
    .block-container { max-width:1420px; padding-top:1.2rem; padding-bottom:4rem; }
    [data-testid="stSidebar"] { background:linear-gradient(180deg,#08151e,#0b1b26); border-right:1px solid var(--line); }
    .brand { display:flex; gap:13px; align-items:center; margin-bottom:20px; }
    .mark { width:52px; height:52px; border-radius:17px; display:grid; place-items:center; background:linear-gradient(135deg,var(--cyan),#178396); color:#031014; font-weight:900; box-shadow:0 12px 35px rgba(69,214,220,.22); }
    .brand-title { color:white; font-weight:900; font-size:17px; }
    .brand-sub { color:var(--muted); font-size:10px; letter-spacing:.12em; text-transform:uppercase; }
    .hero { position:relative; overflow:hidden; padding:40px; border:1px solid var(--line); border-radius:30px; background:linear-gradient(135deg,rgba(20,45,59,.98),rgba(8,24,34,.97)); box-shadow:0 28px 90px rgba(0,0,0,.28); margin-bottom:22px; }
    .hero:after { content:'RP'; position:absolute; right:35px; top:-45px; color:rgba(255,255,255,.028); font-size:190px; font-weight:900; letter-spacing:-18px; }
    .kicker { color:var(--cyan); font-size:11px; font-weight:900; letter-spacing:.14em; text-transform:uppercase; }
    .hero h1 { color:white; font-size:46px; letter-spacing:-2.3px; margin:.5rem 0; max-width:850px; }
    .hero p { color:#b3c4ce; font-size:17px; max-width:760px; margin:0; }
    .chips { display:flex; flex-wrap:wrap; gap:8px; margin-top:20px; }
    .chip { border:1px solid var(--line); background:rgba(255,255,255,.045); border-radius:999px; padding:7px 11px; color:#c9d7df; font-size:11px; }
    .action-card { min-height:195px; padding:25px; border-radius:23px; border:1px solid var(--line); background:linear-gradient(180deg,rgba(19,42,56,.95),rgba(11,27,38,.95)); }
    .action-number { color:var(--cyan); font-weight:900; font-size:12px; letter-spacing:.12em; }
    .action-card h3 { color:white; font-size:24px; margin:.5rem 0; }
    .action-card p { color:var(--muted); font-size:13px; }
    .section-title { color:white; font-size:22px; font-weight:900; letter-spacing:-.6px; margin:8px 0 3px; }
    .section-sub { color:var(--muted); font-size:13px; margin-bottom:17px; }
    .tip { border-left:3px solid var(--cyan); padding:11px 14px; border-radius:0 12px 12px 0; background:rgba(69,214,220,.065); color:#bdd0da; font-size:12px; }
    [data-testid="stMetric"] { background:linear-gradient(180deg,rgba(19,42,56,.92),rgba(11,27,38,.92)); border:1px solid var(--line); border-radius:17px; padding:15px; }
    [data-testid="stFileUploaderDropzone"] { background:#091923; border:1px dashed rgba(69,214,220,.48); border-radius:17px; }
    .stButton>button,.stDownloadButton>button { min-height:46px; border-radius:13px; font-weight:800; border:1px solid var(--line); }
    .stButton>button[kind="primary"] { background:linear-gradient(135deg,var(--cyan),#188da0); color:#031014; border:none; }
    .stTextInput input,.stTextArea textarea,.stSelectbox [data-baseweb="select"]>div { background:#091923!important; border-color:var(--line)!important; color:white!important; border-radius:12px!important; }
    .footer { text-align:center; color:#607784; font-size:11px; margin-top:35px; }
    @media(max-width:720px){ .hero{padding:25px;border-radius:22px}.hero h1{font-size:34px}.hero:after{display:none}.block-container{padding-left:1rem;padding-right:1rem} }
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
        "workspace_view": "Início",
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


def save_uploaded_file(uploaded_file, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(uploaded_file.getbuffer())
    return destination


def package_scene_rows(package) -> list[dict[str, object]]:
    names = {"avatar":"Professor RP", "title_card":"Tela de impacto", "broll":"Imagem de apoio", "screen_capture":"Captura de tela", "proof":"Prova / exemplo"}
    return [{"Cena":scene.index, "Tempo":f"{scene.start:.1f}–{scene.end:.1f}s", "Função":names.get(scene.scene_type, scene.scene_type), "Narração":scene.narration, "Texto na tela":scene.on_screen_text, "Direção visual":scene.visual_direction} for scene in package.scenes]


def open_analysis(path: Path, name: str, source: str) -> None:
    st.session_state.pending_video_path = str(path)
    st.session_state.pending_video_name = name
    st.session_state.pending_video_source = source
    for key in ("video_analysis", "semantic_analysis", "visual_analysis", "multimodal_timeline", "upload_key"):
        st.session_state.pop(key, None)
    st.switch_page("pages/01_Analisar_Video.py")


initialize_state()
records = load_feedback(LEARNING_STORE)
summary = summarize_preferences(records)

with st.sidebar:
    st.markdown('<div class="brand"><div class="mark">RP</div><div><div class="brand-title">ViralLab Studio</div><div class="brand-sub">Engenharia de conteúdo</div></div></div>', unsafe_allow_html=True)
    view = st.radio("Navegação", ["Início", "Studio", "DNA RP"], key="workspace_view", label_visibility="collapsed")
    st.divider()
    st.caption("PROJETO ATUAL")
    st.code(st.session_state.project_id)
    if st.button("＋ Novo projeto", use_container_width=True):
        new_project()
        st.rerun()
    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("Exemplos", summary["total_feedback"])
    c2.metric("Aprovação", f"{summary['approval_rate']}%")
    st.caption("O DNA RP registra decisões editoriais auditáveis.")

if view == "Início":
    st.markdown(
        """
        <section class="hero">
          <div class="kicker">Engenharia reversa de conteúdo com IA</div>
          <h1>Descubra por que um vídeo funciona. Depois, crie a sua versão original.</h1>
          <p>O ViralLab lê estrutura, fala, hook, CTA, ritmo, cenas, enquadramentos e textos para transformar referências em decisões criativas.</p>
          <div class="chips"><span class="chip">Instagram Reels</span><span class="chip">TikTok</span><span class="chip">YouTube Shorts</span><span class="chip">Upload local</span><span class="chip">Mapa multimodal</span></div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.25, .75], gap="large")
    with left:
        st.markdown('<div class="section-title">Analisar vídeo</div><div class="section-sub">Envie um arquivo ou cole uma URL pública.</div>', unsafe_allow_html=True)
        upload_tab, url_tab = st.tabs(["📁 Upload", "🔗 URL"])
        with upload_tab:
            uploaded = st.file_uploader("Escolha um vídeo", type=["mp4", "mov", "m4v", "webm", "mkv"], help="Para o primeiro teste, prefira vídeos de até 2 minutos.")
            if uploaded is not None:
                st.video(uploaded.getvalue())
                if st.button("Analisar vídeo enviado  →", type="primary", use_container_width=True):
                    suffix = Path(uploaded.name).suffix.lower() or ".mp4"
                    path = save_uploaded_file(uploaded, ANALYSIS_DIR / f"{uuid.uuid4().hex[:10]}{suffix}")
                    open_analysis(path, uploaded.name, "upload")
        with url_tab:
            url = st.text_input("Cole a URL pública", placeholder="https://www.instagram.com/reel/... ou https://youtu.be/...")
            st.caption("Funciona em páginas públicas compatíveis. Conteúdos privados ou que exigem login devem ser enviados por upload.")
            if st.button("Importar e analisar URL  →", type="primary", use_container_width=True, disabled=not bool(url.strip())):
                try:
                    with st.status("Importando vídeo público...", expanded=True) as status:
                        st.write("Validando a URL e identificando a plataforma...")
                        imported = download_video_url(url, ANALYSIS_DIR / "urls")
                        status.update(label="Vídeo importado", state="complete", expanded=False)
                    open_analysis(imported.path, imported.title, imported.source_url)
                except URLIngestError as exc:
                    st.error(str(exc))
    with right:
        st.markdown('<div class="action-card"><div class="action-number">CAMINHO 02</div><h3>Criar do zero</h3><p>Comece por tema, público e objetivo. O Studio gera roteiro, storyboard, assets e plano de renderização.</p></div>', unsafe_allow_html=True)
        st.write("")
        if st.button("✨ Criar conteúdo do zero", use_container_width=True):
            st.session_state.workspace_view = "Studio"
            st.rerun()
        st.markdown('<div class="tip"><strong>Fluxo recomendado:</strong> analise uma referência, entenda a arquitetura e então gere um conteúdo autoral.</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="section-title">O que o ViralLab entrega</div>', unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    a.metric("Estrutura", "Cortes + ritmo")
    b.metric("Narrativa", "Hook + CTA")
    c.metric("Visual", "Frames + planos")
    d.metric("Criação", "Versão original")

elif view == "Studio":
    st.markdown('<section class="hero"><div class="kicker">Criação orientada por estratégia</div><h1>Studio de conteúdo</h1><p>Crie, revise, produza e renderize vídeos verticais mantendo revisão humana em todas as etapas.</p></section>', unsafe_allow_html=True)
    brief_tab, script_tab, assets_tab, render_tab = st.tabs(["01 Estratégia", "02 Roteiro", "03 Produção", "04 Render"])

    with brief_tab:
        st.markdown('<div class="section-title">Defina a intenção</div><div class="section-sub">O brief orienta o roteiro e o storyboard.</div>', unsafe_allow_html=True)
        left, right = st.columns(2, gap="large")
        with left:
            theme = st.text_input("Tema central", value="IA na fisioterapia")
            audience = st.text_input("Público", value="fisioterapeutas brasileiros")
            objective = st.selectbox("Objetivo", ["ganhar seguidores qualificados", "educar", "gerar autoridade", "vender", "engajar"])
            duration = st.slider("Duração", 15, 90, 60, 5)
        with right:
            video_format = st.selectbox("Formato", ["professor_cinematico", "lista_demonstrativa", "narrativo", "tutorial", "case_clinico"])
            evidence_level = st.selectbox("Base", ["educacional", "cientifico", "opiniao"])
            provider_name = st.selectbox("Motor de IA", ["auto", "local", "gemini"])
            cta = st.text_area("Chamada para ação", value="Siga o Professor RP para aprender IA aplicada à saúde.", height=100)
        if st.button("Gerar roteiro e storyboard  →", type="primary", use_container_width=True):
            try:
                brief = VideoBrief(theme=theme, objective=objective, audience=audience, duration_seconds=duration, format=video_format, cta=cta, evidence_level=evidence_level)
                package = generate_video_package(brief, provider=select_provider(provider_name))
                out = project_dir(st.session_state.project_id)
                if out.exists():
                    shutil.rmtree(out)
                export_package(package, out)
                st.session_state.package = package
                st.session_state.package_dir = str(out)
                st.session_state.preferred_hook = package.hook
                st.success("Roteiro criado. Abra a aba 02 para revisar.")
            except Exception as exc:
                st.error(f"Não foi possível gerar o pacote: {exc}")

    with script_tab:
        package = st.session_state.package
        if package is None:
            st.warning("Gere um roteiro na aba Estratégia ou crie uma versão a partir de uma análise.")
        else:
            st.markdown('<div class="section-title">Sala de roteiro</div>', unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            m1.metric("Cenas", len(package.scenes))
            m2.metric("Duração", f"{package.brief.duration_seconds}s")
            m3.metric("Motor", package.metadata.get("script_provider", "—"))
            st.caption("HOOK")
            st.markdown(f"### {package.hook}")
            st.session_state.preferred_hook = st.text_area("Reescreva com sua voz", value=st.session_state.preferred_hook or package.hook, height=90)
            st.markdown(f"**Tese:** {package.thesis}")
            st.dataframe(package_scene_rows(package), use_container_width=True, hide_index=True, height=390)
            st.download_button("Baixar roteiro estruturado", json.dumps(package.to_dict(), ensure_ascii=False, indent=2), "video-package.json", "application/json", use_container_width=True)

    with assets_tab:
        package = st.session_state.package
        package_path = Path(st.session_state.package_dir) if st.session_state.package_dir else None
        if package is None or package_path is None:
            st.warning("Gere um roteiro antes de iniciar a produção.")
        else:
            st.markdown('<div class="section-title">Central de produção</div><div class="section-sub">Envie os materiais disponíveis; ausências recebem cartões temporários.</div>', unsafe_allow_html=True)
            assets_dir = package_path / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)
            for scene in package.scenes:
                mapping = {"avatar":("Vídeo do Professor RP", f"avatar-scene-{scene.index:02d}.mp4"), "screen_capture":("Captura de tela", f"screen-scene-{scene.index:02d}.mp4"), "proof":("Prova ou exemplo", f"proof-scene-{scene.index:02d}.jpg")}
                if scene.scene_type not in mapping:
                    continue
                label, suggested = mapping[scene.scene_type]
                with st.container(border=True):
                    a, b = st.columns([1.1, .9])
                    a.markdown(f"**Cena {scene.index} · {label}**")
                    a.caption(scene.narration or scene.on_screen_text)
                    upload = b.file_uploader(f"Enviar {suggested}", type=["mp4", "mov", "webm", "png", "jpg", "jpeg", "webp"], key=f"asset-{scene.index}", label_visibility="collapsed")
                    if upload is not None:
                        saved = save_uploaded_file(upload, assets_dir / suggested)
                        b.success(f"Salvo: {saved.name}")
            music = st.file_uploader("Trilha opcional", type=["mp3", "wav", "m4a", "aac"])
            if music is not None:
                suffix = Path(music.name).suffix.lower() or ".mp3"
                save_uploaded_file(music, assets_dir / f"music{suffix}")
                st.success("Trilha salva.")

    with render_tab:
        package_path = Path(st.session_state.package_dir) if st.session_state.package_dir else None
        if package_path is None:
            st.warning("Crie um projeto antes de renderizar.")
        else:
            st.markdown('<div class="section-title">Finalização</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            burn_captions = c1.checkbox("Legendas incorporadas", value=True)
            music_level = c2.slider("Trilha (dB)", -40, -12, -25)
            dry_run = c3.checkbox("Simular sem MP4", value=False)
            if st.button("Renderizar vídeo vertical  →", type="primary", use_container_width=True):
                try:
                    with st.spinner("Montando o vídeo..."):
                        video = render_video(package_path, dry_run=dry_run, burn_captions=burn_captions, music_level_db=music_level)
                    if dry_run:
                        st.success("Plano técnico gerado.")
                    elif video.exists():
                        st.success("Vídeo gerado com sucesso.")
                        st.video(str(video))
                        st.download_button("Baixar vídeo final", video.read_bytes(), "video-final.mp4", "video/mp4", use_container_width=True)
                except RenderError as exc:
                    st.error(str(exc))

else:
    st.markdown('<section class="hero"><div class="kicker">Memória editorial auditável</div><h1>DNA RP</h1><p>Transforme escolhas editoriais em exemplos que orientam as próximas gerações.</p></section>', unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    k1.metric("Feedbacks", summary["total_feedback"])
    k2.metric("Aprovação", f"{summary['approval_rate']}%")
    k3.metric("Nota média", summary["average_rating"])
    package = st.session_state.package
    if package is None:
        st.warning("Crie um roteiro para registrar um aprendizado contextual.")
    else:
        left, right = st.columns(2, gap="large")
        with left:
            rating = st.slider("Qualidade do roteiro", 1, 10, 8)
            approved = st.checkbox("Eu publicaria esta estrutura", value=True)
            preferred_style = st.selectbox("Direção a reforçar", ["Professor Cinemático", "Mais científico", "Mais direto", "Mais emocional", "Mais comercial"])
        with right:
            notes = st.text_area("O que o ViralLab deve aprender?", placeholder="Ex.: abrir com pergunta mais forte, usar exemplos clínicos...", height=140)
        if st.button("Salvar no DNA RP", type="primary", use_container_width=True):
            save_feedback(FeedbackRecord(project_id=st.session_state.project_id, theme=package.brief.theme, rating=rating, approved=approved, original_hook=package.hook, preferred_hook=st.session_state.preferred_hook or package.hook, notes=notes, preferred_style=preferred_style), LEARNING_STORE)
            st.success("Aprendizado registrado.")
            st.rerun()
    if records:
        st.divider()
        st.dataframe(records[-12:][::-1], use_container_width=True, hide_index=True)
        st.download_button("Exportar DNA RP", "\n".join(json.dumps(item, ensure_ascii=False) for item in records), "dna-rp-feedback.jsonl", "application/x-ndjson")

st.markdown('<div class="footer">RP ViralLab Studio · Conteúdo original, revisão humana e engenharia reversa ética.</div>', unsafe_allow_html=True)
