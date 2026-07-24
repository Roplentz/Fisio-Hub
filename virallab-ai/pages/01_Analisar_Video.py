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
from virallab.semantic_analyzer import SemanticAnalysisError, transcribe_video
from virallab.video_analyzer import VideoAnalysisError, analyze_video

WORKSPACE = APP_ROOT / "workspace"
ANALYSIS_DIR = WORKSPACE / "analysis"
PROJECTS_DIR = WORKSPACE / "projects"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Analisar vídeo · RP ViralLab", page_icon="◉", layout="wide", initial_sidebar_state="collapsed")
st.markdown(
    """
    <style>
    :root { --rp-bg:#071018; --rp-line:rgba(255,255,255,.10); --rp-cyan:#42D3D9; --rp-muted:#91A4B2; }
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
    @media(max-width:640px) { .block-container { padding-left:1rem; padding-right:1rem; } .rp-head { padding:18px; } .rp-head h1 { font-size:26px; } }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <section class="rp-head"><div class="rp-kicker">Engenharia reversa ética · Sprint 1</div>
    <h1>Analisar vídeo</h1><p>Estrutura, transcrição, hook verbal, narrativa, CTA e legendas em um único diagnóstico.</p></section>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="rp-note"><strong>Análise local:</strong> o áudio é transcrito pelo faster-whisper. No primeiro uso, o modelo escolhido será baixado e a análise poderá demorar mais.</div>',
    unsafe_allow_html=True,
)

uploaded = st.file_uploader("Escolha o vídeo de referência", type=["mp4", "mov", "m4v", "webm", "mkv"], help="Prefira vídeos de até 2 minutos no primeiro teste.")
c1, c2 = st.columns(2)
threshold = c1.slider("Sensibilidade dos cortes", 0.15, 0.60, 0.30, 0.05)
model_size = c2.selectbox("Modelo de transcrição", ["tiny", "base", "small"], index=0, help="Tiny é mais rápido; small tende a ser mais preciso e pesado.")

if uploaded is not None:
    upload_key = f"{uploaded.name}:{uploaded.size}"
    if st.session_state.get("upload_key") != upload_key:
        file_id = uuid.uuid4().hex[:10]
        suffix = Path(uploaded.name).suffix.lower() or ".mp4"
        video_path = ANALYSIS_DIR / f"{file_id}{suffix}"
        video_path.write_bytes(uploaded.getbuffer())
        st.session_state.upload_key = upload_key
        st.session_state.analysis_video_path = str(video_path)
        st.session_state.pop("video_analysis", None)
        st.session_state.pop("semantic_analysis", None)
    else:
        video_path = Path(st.session_state.analysis_video_path)

    st.video(uploaded.getvalue())
    if st.button("Analisar vídeo completo", type="primary", use_container_width=True):
        try:
            with st.status("Executando engenharia reversa...", expanded=True) as status:
                st.write("Lendo formato, duração, áudio e cortes...")
                st.session_state.video_analysis = analyze_video(video_path, scene_threshold=threshold)
                st.write("Transcrevendo a fala e criando timestamps...")
                st.session_state.semantic_analysis = transcribe_video(video_path, model_size=model_size, language="pt")
                st.session_state.analysis_source_name = uploaded.name
                status.update(label="Análise concluída", state="complete", expanded=False)
        except (VideoAnalysisError, SemanticAnalysisError) as exc:
            st.error(f"Não foi possível concluir a análise: {exc}")

analysis = st.session_state.get("video_analysis")
semantic = st.session_state.get("semantic_analysis")
if analysis is not None:
    st.divider()
    st.subheader("Diagnóstico estrutural")
    st.write(analysis.summary)
    m1, m2, m3 = st.columns(3)
    m1.metric("Pontuação estrutural", f"{analysis.viral_potential_score}/100")
    m2.metric("Cenas estimadas", analysis.estimated_scenes)
    m3.metric("Média por cena", f"{analysis.average_scene_seconds}s")
    m4, m5, m6 = st.columns(3)
    m4.metric("Hook visual", f"{analysis.hook_score}/100")
    m5.metric("Ritmo visual", f"{analysis.pacing_score}/100")
    m6.metric("Formato", f"{analysis.format_score}/100")

if semantic is not None:
    st.divider()
    st.subheader("Diagnóstico semântico")
    st.write(semantic.summary)
    s1, s2, s3 = st.columns(3)
    s1.metric("Hook verbal", f"{semantic.hook_score}/100")
    s2.metric("CTA", f"{semantic.cta_score}/100")
    s3.metric("Velocidade", f"{semantic.words_per_minute} ppm")

    st.markdown("#### Hook identificado")
    st.info(semantic.hook_text)
    st.markdown("#### CTA identificado")
    if semantic.cta_text:
        st.success(semantic.cta_text)
    else:
        st.warning("Nenhuma chamada para ação explícita foi identificada.")

    st.markdown("#### Mapa narrativo")
    for block in semantic.narrative_blocks:
        with st.expander(f"{block.label} · {block.start:.1f}s–{block.end:.1f}s", expanded=block.label == "Hook"):
            st.write(block.text)

    with st.expander("Transcrição completa", expanded=False):
        st.write(semantic.transcript)

    left, right = st.columns(2)
    with left:
        st.markdown("#### O que funciona")
        for item in analysis.strengths + semantic.strengths:
            st.success(item)
    with right:
        st.markdown("#### O que melhorar")
        for item in analysis.improvements + semantic.improvements:
            st.warning(item)

    combined = {"source": st.session_state.get("analysis_source_name"), "structural": analysis.to_dict(), "semantic": semantic.to_dict()}
    d1, d2 = st.columns(2)
    d1.download_button("Baixar relatório completo", json.dumps(combined, ensure_ascii=False, indent=2), "analise-virallab.json", "application/json", use_container_width=True)
    d2.download_button("Baixar legendas SRT", semantic.to_srt(), "legendas-virallab.srt", "application/x-subrip", use_container_width=True)

    st.divider()
    st.subheader("Criar uma versão RP")
    st.caption("A nova versão reutiliza a arquitetura narrativa, não copia o conteúdo original.")
    theme = st.text_input("Tema da nova versão", value="IA aplicada à fisioterapia")
    audience = st.text_input("Público", value="fisioterapeutas brasileiros")
    objective = st.selectbox("Objetivo", ["educar", "gerar autoridade", "ganhar seguidores qualificados", "engajar", "vender"])
    r1, r2 = st.columns(2)
    duration = r1.slider("Duração", 15, 90, min(60, max(15, round(analysis.duration_seconds / 5) * 5)), 5)
    evidence = r2.selectbox("Base", ["educacional", "cientifico", "opiniao"])
    cta = st.text_input("Chamada para ação", value="Siga o Professor RP para aprender inovação e IA aplicada à saúde.")
    if st.button("Criar roteiro original com esta estrutura", type="primary", use_container_width=True):
        try:
            brief = VideoBrief(theme=theme, objective=objective, audience=audience, duration_seconds=duration, format="professor_cinematico", cta=cta, evidence_level=evidence)
            package = generate_video_package(brief, provider=select_provider("local"))
            project_id = uuid.uuid4().hex[:10]
            output_dir = PROJECTS_DIR / project_id
            export_package(package, output_dir)
            st.session_state.project_id = project_id
            st.session_state.package = package
            st.session_state.package_dir = str(output_dir)
            st.session_state.preferred_hook = package.hook
            st.success("Versão RP criada e enviada ao Studio principal.")
            st.markdown(f"**Hook sugerido:** {package.hook}")
            st.markdown(f"**Tese:** {package.thesis}")
            st.download_button("Baixar pacote RP", json.dumps(package.to_dict(), ensure_ascii=False, indent=2), "video-package-rp.json", "application/json", use_container_width=True)
        except Exception as exc:
            st.error(f"Não foi possível criar a versão RP: {exc}")

st.divider()
st.page_link("app.py", label="Voltar ao RP ViralLab Studio", icon="↩️")
