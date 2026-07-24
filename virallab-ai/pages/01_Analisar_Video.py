from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

import streamlit as st

APP_ROOT = Path(__file__).resolve().parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from virallab.generator import export_package, generate_video_package
from virallab.models import VideoBrief
from virallab.providers import select_provider
from virallab.video_analyzer import VideoAnalysisError, analyze_video

WORKSPACE = APP_ROOT / "workspace"
ANALYSIS_DIR = WORKSPACE / "analysis"
PROJECTS_DIR = WORKSPACE / "projects"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="Analisar vídeo · RP ViralLab",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root { --rp-bg:#071018; --rp-panel:#10202c; --rp-line:rgba(255,255,255,.10); --rp-cyan:#42D3D9; --rp-muted:#91A4B2; }
    .stApp { background:radial-gradient(circle at 90% 0%,rgba(66,211,217,.13),transparent 30%),var(--rp-bg); }
    .block-container { padding-top:1.2rem; padding-bottom:4rem; max-width:1050px; }
    .rp-head { border:1px solid var(--rp-line); background:linear-gradient(135deg,#132a39,#0b1923); padding:22px; border-radius:24px; margin-bottom:18px; }
    .rp-kicker { color:var(--rp-cyan); font-size:11px; font-weight:800; letter-spacing:.13em; text-transform:uppercase; }
    .rp-head h1 { color:white; margin:.3rem 0; font-size:31px; letter-spacing:-1px; }
    .rp-head p { color:var(--rp-muted); margin:0; }
    [data-testid="stMetric"] { background:linear-gradient(180deg,#122532,#0c1b25); border:1px solid var(--rp-line); border-radius:17px; padding:14px; }
    [data-testid="stFileUploaderDropzone"] { background:#0b1821; border:1px dashed rgba(66,211,217,.45); border-radius:18px; }
    .stButton>button, .stDownloadButton>button { min-height:46px; border-radius:13px; font-weight:800; }
    .rp-note { border-left:3px solid var(--rp-cyan); background:rgba(66,211,217,.06); padding:12px 14px; border-radius:0 12px 12px 0; color:#b8c9d3; }
    @media(max-width:640px) {
      .block-container { padding-left:1rem; padding-right:1rem; }
      .rp-head { padding:18px; border-radius:19px; }
      .rp-head h1 { font-size:26px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="rp-head">
      <div class="rp-kicker">Engenharia reversa ética</div>
      <h1>Analisar vídeo</h1>
      <p>Envie um MP4, MOV ou WEBM. O ViralLab identifica formato, ritmo, cortes, hook visual e oportunidades para uma versão original com a marca RP.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="rp-note"><strong>MVP atual:</strong> esta versão analisa a estrutura audiovisual. A transcrição da fala, leitura das legendas e análise semântica serão adicionadas na próxima etapa.</div>',
    unsafe_allow_html=True,
)

uploaded = st.file_uploader(
    "Escolha o vídeo de referência",
    type=["mp4", "mov", "m4v", "webm", "mkv"],
    help="Para o primeiro teste, prefira vídeos curtos de até 2 minutos.",
)
threshold = st.slider(
    "Sensibilidade para detectar cortes",
    min_value=0.15,
    max_value=0.60,
    value=0.30,
    step=0.05,
    help="Valores menores detectam mais mudanças; valores maiores detectam apenas cortes fortes.",
)

if uploaded is not None:
    file_id = uuid.uuid4().hex[:10]
    suffix = Path(uploaded.name).suffix.lower() or ".mp4"
    video_path = ANALYSIS_DIR / f"{file_id}{suffix}"
    video_path.write_bytes(uploaded.getbuffer())
    st.video(uploaded.getvalue())

    if st.button("Analisar estrutura do vídeo", type="primary", use_container_width=True):
        with st.spinner("Lendo o vídeo, detectando cortes e calculando o ritmo..."):
            try:
                st.session_state.video_analysis = analyze_video(video_path, scene_threshold=threshold)
                st.session_state.analysis_video_path = str(video_path)
                st.session_state.analysis_source_name = uploaded.name
            except VideoAnalysisError as exc:
                st.error(f"Não foi possível analisar o vídeo: {exc}")

analysis = st.session_state.get("video_analysis")
if analysis is not None:
    st.divider()
    st.subheader("Diagnóstico estrutural")
    st.write(analysis.summary)

    m1, m2, m3 = st.columns(3)
    m1.metric("Potencial estrutural", f"{analysis.viral_potential_score}/100")
    m2.metric("Cenas estimadas", analysis.estimated_scenes)
    m3.metric("Média por cena", f"{analysis.average_scene_seconds}s")

    m4, m5, m6 = st.columns(3)
    m4.metric("Hook visual", f"{analysis.hook_score}/100")
    m5.metric("Ritmo", f"{analysis.pacing_score}/100")
    m6.metric("Formato", f"{analysis.format_score}/100")

    with st.expander("Dados técnicos", expanded=False):
        st.write(
            {
                "Duração": f"{analysis.duration_seconds}s",
                "Resolução": f"{analysis.width} × {analysis.height}",
                "Orientação": analysis.orientation,
                "FPS": analysis.fps,
                "Codec de vídeo": analysis.video_codec,
                "Áudio": "sim" if analysis.has_audio else "não",
                "Cortes nos primeiros 3s": analysis.cuts_first_3_seconds,
                "Momentos de corte": analysis.cut_times,
            }
        )

    left, right = st.columns(2)
    with left:
        st.markdown("#### O que funciona")
        for item in analysis.strengths:
            st.success(item)
    with right:
        st.markdown("#### O que melhorar")
        for item in analysis.improvements:
            st.warning(item)

    st.download_button(
        "Baixar relatório JSON",
        data=json.dumps(analysis.to_dict(), ensure_ascii=False, indent=2),
        file_name="analise-virallab.json",
        mime="application/json",
        use_container_width=True,
    )

    st.divider()
    st.subheader("Criar uma versão RP")
    st.caption("O sistema reutiliza apenas o padrão estrutural. O conteúdo novo deve ser original e adequado ao seu público.")
    theme = st.text_input("Tema da nova versão", value="IA aplicada à fisioterapia")
    audience = st.text_input("Público", value="fisioterapeutas brasileiros")
    objective = st.selectbox("Objetivo", ["educar", "gerar autoridade", "ganhar seguidores qualificados", "engajar", "vender"])
    c1, c2 = st.columns(2)
    duration = c1.slider("Duração da versão RP", 15, 90, min(60, max(15, round(analysis.duration_seconds / 5) * 5)), 5)
    evidence = c2.selectbox("Base do conteúdo", ["educacional", "cientifico", "opiniao"])
    cta = st.text_input("Chamada para ação", value="Siga o Professor RP para aprender inovação e IA aplicada à saúde.")

    if st.button("Criar roteiro original com esta estrutura", type="primary", use_container_width=True):
        try:
            brief = VideoBrief(
                theme=theme,
                objective=objective,
                audience=audience,
                duration_seconds=duration,
                format="professor_cinematico",
                cta=cta,
                evidence_level=evidence,
            )
            package = generate_video_package(brief, provider=select_provider("local"))
            project_id = uuid.uuid4().hex[:10]
            output_dir = PROJECTS_DIR / project_id
            export_package(package, output_dir)
            st.session_state.project_id = project_id
            st.session_state.package = package
            st.session_state.package_dir = str(output_dir)
            st.session_state.preferred_hook = package.hook
            st.success("Versão RP criada. Ela já está disponível no Studio principal para revisão e produção.")
            st.markdown(f"**Hook sugerido:** {package.hook}")
            st.markdown(f"**Tese:** {package.thesis}")
            st.download_button(
                "Baixar pacote da versão RP",
                data=json.dumps(package.to_dict(), ensure_ascii=False, indent=2),
                file_name="video-package-rp.json",
                mime="application/json",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"Não foi possível criar a versão RP: {exc}")

st.divider()
st.page_link("app.py", label="Voltar ao RP ViralLab Studio", icon="↩️")
