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

APP_ROOT = Path(__file__).resolve().parent
WORKSPACE = APP_ROOT / "workspace"
LEARNING_STORE = WORKSPACE / "learning" / "feedback.jsonl"
WORKSPACE.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="RP ViralLab Studio",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

RP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --rp-bg: #071018;
  --rp-panel: #0E1B26;
  --rp-panel-2: #132432;
  --rp-line: rgba(255,255,255,.09);
  --rp-text: #F5F8FA;
  --rp-muted: #91A4B2;
  --rp-cyan: #42D3D9;
  --rp-gold: #D7B56D;
  --rp-green: #7ADFA7;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp {
  background:
    radial-gradient(circle at 85% 0%, rgba(66,211,217,.12), transparent 28%),
    radial-gradient(circle at 15% 10%, rgba(215,181,109,.08), transparent 24%),
    var(--rp-bg);
  color: var(--rp-text);
}
.block-container { padding-top: 1.4rem; padding-bottom: 4rem; max-width: 1500px; }

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #09141D 0%, #0C1A24 100%);
  border-right: 1px solid var(--rp-line);
}
[data-testid="stSidebar"] .block-container { padding-top: 1.25rem; }

.rp-brand {
  display:flex; align-items:center; gap:14px; margin-bottom:20px;
}
.rp-mark {
  width:54px; height:54px; border-radius:17px;
  display:grid; place-items:center;
  background: linear-gradient(135deg, var(--rp-cyan), #167F91 58%, #0D3544);
  color:#041014; font-size:20px; font-weight:900; letter-spacing:-1px;
  box-shadow: 0 10px 30px rgba(66,211,217,.20);
  border:1px solid rgba(255,255,255,.20);
}
.rp-brand-title { font-weight:800; font-size:17px; color:white; line-height:1.1; }
.rp-brand-sub { font-size:11px; color:var(--rp-muted); margin-top:4px; letter-spacing:.08em; text-transform:uppercase; }

.rp-hero {
  position:relative; overflow:hidden;
  background: linear-gradient(135deg, rgba(19,36,50,.96), rgba(10,25,35,.96));
  border:1px solid var(--rp-line); border-radius:26px;
  padding:28px 30px; margin-bottom:20px;
  box-shadow: 0 24px 70px rgba(0,0,0,.25);
}
.rp-hero:after {
  content:"RP"; position:absolute; right:28px; top:-28px;
  font-size:150px; font-weight:900; color:rgba(255,255,255,.025); letter-spacing:-12px;
}
.rp-kicker { color:var(--rp-cyan); font-weight:800; letter-spacing:.12em; text-transform:uppercase; font-size:11px; }
.rp-hero h1 { margin:.35rem 0 .35rem; font-size:38px; letter-spacing:-1.5px; color:white; }
.rp-hero p { max-width:760px; color:var(--rp-muted); margin:0; font-size:15px; }
.rp-chip-row { display:flex; flex-wrap:wrap; gap:8px; margin-top:18px; }
.rp-chip { background:rgba(255,255,255,.05); border:1px solid var(--rp-line); color:#C9D6DE; border-radius:999px; padding:6px 10px; font-size:11px; }

.rp-section-title { font-size:21px; font-weight:800; color:white; letter-spacing:-.5px; margin-bottom:4px; }
.rp-section-sub { color:var(--rp-muted); font-size:13px; margin-bottom:18px; }
.rp-card {
  background:linear-gradient(180deg, rgba(19,36,50,.92), rgba(13,28,39,.92));
  border:1px solid var(--rp-line); border-radius:20px; padding:18px;
}
.rp-tip { border-left:3px solid var(--rp-cyan); padding:10px 13px; background:rgba(66,211,217,.06); border-radius:0 12px 12px 0; color:#B8CAD4; font-size:12px; }
.rp-status { display:flex; gap:10px; align-items:center; padding:12px 14px; border:1px solid var(--rp-line); background:rgba(255,255,255,.025); border-radius:14px; }
.rp-dot { width:9px; height:9px; border-radius:50%; background:var(--rp-green); box-shadow:0 0 15px rgba(122,223,167,.55); }
.rp-step { color:var(--rp-muted); font-size:12px; }
.rp-step strong { color:white; font-size:13px; }

.stTabs [data-baseweb="tab-list"] { gap:8px; background:rgba(255,255,255,.025); padding:7px; border-radius:16px; border:1px solid var(--rp-line); }
.stTabs [data-baseweb="tab"] { border-radius:11px; padding:10px 16px; color:#8EA1AE; font-weight:700; }
.stTabs [aria-selected="true"] { background:linear-gradient(135deg, rgba(66,211,217,.18), rgba(66,211,217,.08)); color:white !important; }

[data-testid="stMetric"] { background:linear-gradient(180deg, rgba(19,36,50,.9), rgba(13,28,39,.9)); border:1px solid var(--rp-line); border-radius:18px; padding:16px; }
[data-testid="stMetricLabel"] { color:var(--rp-muted); }
[data-testid="stMetricValue"] { color:white; font-weight:800; }

.stButton > button, .stDownloadButton > button {
  border-radius:12px; min-height:44px; font-weight:800; border:1px solid var(--rp-line);
}
.stButton > button[kind="primary"] {
  background:linear-gradient(135deg, var(--rp-cyan), #188DA0); color:#031014; border:none;
  box-shadow:0 10px 25px rgba(66,211,217,.18);
}
.stButton > button[kind="primary"]:hover { filter:brightness(1.06); color:#031014; }

.stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] > div, .stNumberInput input {
  background:#0A1720 !important; border-color:var(--rp-line) !important; border-radius:12px !important; color:white !important;
}
[data-testid="stFileUploaderDropzone"] { background:#0A1720; border:1px dashed rgba(66,211,217,.35); border-radius:16px; }
[data-testid="stDataFrame"] { border:1px solid var(--rp-line); border-radius:16px; overflow:hidden; }
hr { border-color:var(--rp-line); }

.rp-footer { text-align:center; color:#607582; font-size:11px; margin-top:32px; }
</style>
"""
st.markdown(RP_CSS, unsafe_allow_html=True)


def project_dir(project_id: str) -> Path:
    return WORKSPACE / "projects" / project_id


def initialize_state() -> None:
    defaults = {
        "project_id": uuid.uuid4().hex[:10],
        "package": None,
        "package_dir": None,
        "preferred_hook": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def save_uploaded_file(uploaded_file, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(uploaded_file.getbuffer())
    return destination


def package_scene_rows(package) -> list[dict[str, object]]:
    type_names = {
        "avatar": "Professor RP",
        "title_card": "Tela de impacto",
        "broll": "Imagem de apoio",
        "screen_capture": "Captura de tela",
        "proof": "Prova / exemplo",
    }
    return [
        {
            "Cena": scene.index,
            "Tempo": f"{scene.start:.1f}–{scene.end:.1f}s",
            "Função": type_names.get(scene.scene_type, scene.scene_type),
            "Narração": scene.narration,
            "Texto na tela": scene.on_screen_text,
            "Direção visual": scene.visual_direction,
        }
        for scene in package.scenes
    ]


def new_project() -> None:
    st.session_state.project_id = uuid.uuid4().hex[:10]
    st.session_state.package = None
    st.session_state.package_dir = None
    st.session_state.preferred_hook = ""


initialize_state()
records = load_feedback(LEARNING_STORE)
summary = summarize_preferences(records)

with st.sidebar:
    st.markdown(
        """
        <div class="rp-brand">
          <div class="rp-mark">RP</div>
          <div><div class="rp-brand-title">ViralLab Studio</div><div class="rp-brand-sub">by Professor RP</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### Jornada do vídeo")
    st.markdown(
        """
        <div class="rp-status"><span class="rp-dot"></span><div class="rp-step"><strong>1. Estratégia</strong><br>Defina tema, público e objetivo</div></div><br>
        <div class="rp-status"><span class="rp-dot"></span><div class="rp-step"><strong>2. Criação</strong><br>Gere e revise o roteiro</div></div><br>
        <div class="rp-status"><span class="rp-dot"></span><div class="rp-step"><strong>3. Produção</strong><br>Envie avatar e materiais</div></div><br>
        <div class="rp-status"><span class="rp-dot"></span><div class="rp-step"><strong>4. Aprendizado</strong><br>Avalie para fortalecer o DNA RP</div></div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    st.caption("PROJETO ATUAL")
    st.code(st.session_state.project_id)
    if st.button("＋ Novo projeto", use_container_width=True):
        new_project()
        st.rerun()
    st.divider()
    st.caption("DNA RP")
    c1, c2 = st.columns(2)
    c1.metric("Exemplos", summary["total_feedback"])
    c2.metric("Aprovação", f"{summary['approval_rate']}%")
    st.info("Cada avaliação vira um exemplo auditável. Nada muda escondido no modelo.")

st.markdown(
    """
    <section class="rp-hero">
      <div class="rp-kicker">Inteligência criativa para especialistas</div>
      <h1>RP ViralLab Studio</h1>
      <p>Transforme conhecimento em vídeos de autoridade, aprenda a lógica da produção e ensine ao sistema o seu estilo.</p>
      <div class="rp-chip-row">
        <span class="rp-chip">Professor Cinemático</span>
        <span class="rp-chip">Roteiro com IA</span>
        <span class="rp-chip">Storyboard automático</span>
        <span class="rp-chip">Vídeo vertical 9:16</span>
        <span class="rp-chip">DNA RP auditável</span>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

brief_tab, script_tab, assets_tab, render_tab, learn_tab = st.tabs(
    ["01  Estratégia", "02  Roteiro", "03  Produção", "04  Render", "05  DNA RP"]
)

with brief_tab:
    st.markdown('<div class="rp-section-title">Defina a intenção do vídeo</div>', unsafe_allow_html=True)
    st.markdown('<div class="rp-section-sub">Quanto mais claro o brief, melhor o roteiro e mais útil será o aprendizado.</div>', unsafe_allow_html=True)
    left, right = st.columns([1.15, .85], gap="large")
    with left:
        theme = st.text_input("Tema central", value="IA na fisioterapia", help="A ideia principal que o público deve compreender.")
        audience = st.text_input("Público", value="fisioterapeutas brasileiros")
        objective = st.selectbox("Objetivo", ["ganhar seguidores qualificados", "educar", "gerar autoridade", "vender", "engajar"])
        c1, c2 = st.columns(2)
        duration = c1.slider("Duração", min_value=15, max_value=90, value=60, step=5)
        evidence_level = c2.selectbox("Base do conteúdo", ["educacional", "cientifico", "opiniao"])
    with right:
        video_format = st.selectbox("Formato", ["professor_cinematico", "lista_demonstrativa", "narrativo", "tutorial", "case_clinico"])
        provider_name = st.selectbox("Motor de IA", ["auto", "local", "gemini"])
        cta = st.text_area("Chamada para ação", value="Siga o Professor RP para aprender IA aplicada à saúde.", height=110)
        st.markdown('<div class="rp-tip"><strong>Como pensar:</strong> tema é o assunto; objetivo é o efeito desejado; formato é a experiência; CTA é o próximo passo.</div>', unsafe_allow_html=True)

    st.write("")
    if st.button("Gerar roteiro e storyboard  →", type="primary", use_container_width=True):
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
            provider = select_provider(provider_name)
            package = generate_video_package(brief, provider=provider)
            out = project_dir(st.session_state.project_id)
            if out.exists():
                shutil.rmtree(out)
            export_package(package, out)
            st.session_state.package = package
            st.session_state.package_dir = str(out)
            st.session_state.preferred_hook = package.hook
            st.success("Roteiro criado. Abra a aba 02 Roteiro para revisar.")
        except Exception as exc:
            st.error(f"Não foi possível gerar o pacote: {exc}")

with script_tab:
    package = st.session_state.package
    if package is None:
        st.warning("Comece pela aba 01 Estratégia e gere seu primeiro roteiro.")
    else:
        st.markdown('<div class="rp-section-title">Sala de roteiro</div>', unsafe_allow_html=True)
        st.markdown('<div class="rp-section-sub">Revise a promessa, entenda a narrativa e ajuste o que deve representar a sua voz.</div>', unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Cenas", len(package.scenes))
        m2.metric("Duração", f"{package.brief.duration_seconds}s")
        m3.metric("IA", package.metadata.get("script_provider", "—"))
        m4.metric("Formato", "RP Cinemático")
        st.write("")
        c1, c2 = st.columns([1.2, .8], gap="large")
        with c1:
            st.caption("HOOK GERADO")
            st.markdown(f"### {package.hook}")
            st.session_state.preferred_hook = st.text_area(
                "Reescreva com a sua voz",
                value=st.session_state.preferred_hook or package.hook,
                height=100,
            )
        with c2:
            st.caption("TESE CENTRAL")
            st.markdown(f"**{package.thesis}**")
            st.markdown('<div class="rp-tip">O hook conquista a atenção. A tese sustenta a credibilidade. Seu feedback ensina ao ViralLab como equilibrar os dois.</div>', unsafe_allow_html=True)
        st.write("")
        st.dataframe(package_scene_rows(package), use_container_width=True, hide_index=True, height=390)
        d1, d2 = st.columns([1, 1])
        d1.download_button(
            "Baixar roteiro estruturado",
            data=json.dumps(package.to_dict(), ensure_ascii=False, indent=2),
            file_name="video-package.json",
            mime="application/json",
            use_container_width=True,
        )
        with d2.expander("Como ler o storyboard"):
            st.write("Cada linha conecta uma intenção narrativa a uma decisão visual. Essa estrutura orienta avatar, legendas, imagens e edição.")

with assets_tab:
    package = st.session_state.package
    package_path = Path(st.session_state.package_dir) if st.session_state.package_dir else None
    if package is None or package_path is None:
        st.warning("Gere e revise um roteiro antes de iniciar a produção.")
    else:
        st.markdown('<div class="rp-section-title">Central de produção</div>', unsafe_allow_html=True)
        st.markdown('<div class="rp-section-sub">Envie somente o que tiver. Materiais ausentes serão representados por cartões temporários.</div>', unsafe_allow_html=True)
        assets_dir = package_path / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        for scene in package.scenes:
            if scene.scene_type == "avatar":
                suggested = f"avatar-scene-{scene.index:02d}.mp4"
                label = "Vídeo do Professor RP / avatar"
            elif scene.scene_type == "screen_capture":
                suggested = f"screen-scene-{scene.index:02d}.mp4"
                label = "Captura de tela"
            elif scene.scene_type == "proof":
                suggested = f"proof-scene-{scene.index:02d}.jpg"
                label = "Imagem de prova ou exemplo"
            else:
                continue
            with st.container(border=True):
                a, b = st.columns([1.1, .9])
                a.markdown(f"**Cena {scene.index} · {label}**")
                a.caption(scene.narration or scene.on_screen_text)
                upload = b.file_uploader(
                    f"Enviar · {suggested}",
                    type=["mp4", "mov", "webm", "png", "jpg", "jpeg", "webp"],
                    key=f"asset-{scene.index}",
                    label_visibility="collapsed",
                )
                if upload is not None:
                    saved = save_uploaded_file(upload, assets_dir / suggested)
                    b.success(f"Salvo: {saved.name}")
        st.divider()
        music = st.file_uploader("Trilha opcional", type=["mp3", "wav", "m4a", "aac"])
        if music is not None:
            suffix = Path(music.name).suffix.lower() or ".mp3"
            saved = save_uploaded_file(music, assets_dir / f"music{suffix}")
            st.success(f"Trilha salva: {saved.name}")
        files = sorted(path.name for path in assets_dir.iterdir() if path.is_file())
        st.caption(f"{len(files)} arquivo(s) pronto(s) para o render.")

with render_tab:
    package_path = Path(st.session_state.package_dir) if st.session_state.package_dir else None
    if package_path is None:
        st.warning("Crie um projeto antes de renderizar.")
    else:
        st.markdown('<div class="rp-section-title">Estúdio de finalização</div>', unsafe_allow_html=True)
        st.markdown('<div class="rp-section-sub">Gere uma prévia com cartões temporários ou o vídeo final com seus materiais.</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        burn_captions = c1.checkbox("Legendas incorporadas", value=True)
        music_level = c2.slider("Trilha (dB)", min_value=-40, max_value=-12, value=-25)
        dry_run = c3.checkbox("Simular sem gerar MP4", value=False)
        st.markdown('<div class="rp-tip">O ViralLab monta as cenas, preserva a voz, adiciona silêncio técnico, mistura a trilha e aplica as legendas. O vídeo final permanece sob sua revisão.</div>', unsafe_allow_html=True)
        st.write("")
        if st.button("Renderizar vídeo vertical  →", type="primary", use_container_width=True):
            try:
                with st.spinner("Montando o vídeo RP..."):
                    video = render_video(
                        package_path,
                        dry_run=dry_run,
                        burn_captions=burn_captions,
                        music_level_db=music_level,
                    )
                if dry_run:
                    st.success("Simulação concluída. O plano técnico foi gerado.")
                elif video.exists():
                    st.success("Vídeo gerado com sucesso.")
                    preview, action = st.columns([1.25, .75], gap="large")
                    preview.video(str(video))
                    action.markdown("### Pronto para revisar")
                    action.write("Assista, anote o que mudaria e registre sua avaliação na aba DNA RP.")
                    action.download_button(
                        "Baixar vídeo final",
                        data=video.read_bytes(),
                        file_name="video-final.mp4",
                        mime="video/mp4",
                        use_container_width=True,
                    )
            except RenderError as exc:
                st.error(str(exc))

with learn_tab:
    package = st.session_state.package
    st.markdown('<div class="rp-section-title">DNA RP</div>', unsafe_allow_html=True)
    st.markdown('<div class="rp-section-sub">Transforme seu julgamento editorial em dados que poderão orientar as próximas gerações.</div>', unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    k1.metric("Feedbacks", summary["total_feedback"])
    k2.metric("Aprovação", f"{summary['approval_rate']}%")
    k3.metric("Nota média", summary["average_rating"])
    st.write("")
    if package is None:
        st.warning("Gere um roteiro para registrar um aprendizado contextual.")
    else:
        left, right = st.columns([1, 1], gap="large")
        with left:
            rating = st.slider("Qualidade do roteiro", 1, 10, 8)
            approved = st.checkbox("Eu publicaria esta estrutura", value=True)
            preferred_style = st.selectbox(
                "Direção que deve ser reforçada",
                ["Professor Cinemático", "Mais científico", "Mais direto", "Mais emocional", "Mais comercial"],
            )
        with right:
            notes = st.text_area(
                "O que o ViralLab deve aprender deste exemplo?",
                placeholder="Ex.: abrir com uma pergunta mais forte, evitar exageros, usar exemplos clínicos...",
                height=145,
            )
        if st.button("Salvar no DNA RP", type="primary", use_container_width=True):
            record = FeedbackRecord(
                project_id=st.session_state.project_id,
                theme=package.brief.theme,
                rating=rating,
                approved=approved,
                original_hook=package.hook,
                preferred_hook=st.session_state.preferred_hook or package.hook,
                notes=notes,
                preferred_style=preferred_style,
            )
            save_feedback(record, LEARNING_STORE)
            st.success("Aprendizado registrado no DNA RP.")
            st.rerun()
    if records:
        st.divider()
        st.markdown("#### Memória editorial recente")
        st.dataframe(records[-12:][::-1], use_container_width=True, hide_index=True)
        st.download_button(
            "Exportar base DNA RP",
            data="\n".join(json.dumps(item, ensure_ascii=False) for item in records),
            file_name="dna-rp-feedback.jsonl",
            mime="application/x-ndjson",
        )

st.markdown('<div class="rp-footer">RP ViralLab Studio · Conteúdo original, revisão humana e aprendizado transparente.</div>', unsafe_allow_html=True)
