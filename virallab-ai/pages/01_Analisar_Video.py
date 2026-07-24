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
from virallab.timeline_builder import build_multimodal_timeline
from virallab.video_analyzer import VideoAnalysisError, analyze_video
from virallab.visual_analyzer import VisualAnalysisError, analyze_visuals

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
    .block-container { padding-top:1.2rem; padding-bottom:4rem; max-width:1120px; }
    .rp-head { border:1px solid var(--rp-line); background:linear-gradient(135deg,#132a39,#0b1923); padding:22px; border-radius:24px; margin-bottom:18px; }
    .rp-kicker { color:var(--rp-cyan); font-size:11px; font-weight:800; letter-spacing:.13em; text-transform:uppercase; }
    .rp-head h1 { color:white; margin:.3rem 0; font-size:31px; letter-spacing:-1px; }
    .rp-head p { color:var(--rp-muted); margin:0; }
    [data-testid="stMetric"] { background:linear-gradient(180deg,#122532,#0c1b25); border:1px solid var(--rp-line); border-radius:17px; padding:14px; }
    [data-testid="stFileUploaderDropzone"] { background:#0b1821; border:1px dashed rgba(66,211,217,.45); border-radius:18px; }
    .stButton>button, .stDownloadButton>button { min-height:46px; border-radius:13px; font-weight:800; }
    .rp-note { border-left:3px solid var(--rp-cyan); background:rgba(66,211,217,.06); padding:12px 14px; border-radius:0 12px 12px 0; color:#b8c9d3; }
    @media(max-width:640px) { .block-container { padding-left:1rem; padding-right:1rem; } .rp-head h1 { font-size:26px; } }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <section class="rp-head"><div class="rp-kicker">Engenharia reversa ética · Sprint 2</div>
    <h1>Análise multimodal de vídeo</h1><p>Fala, cenas, frames-chave, rosto, enquadramento, texto na tela e sincronização narrativa.</p></section>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="rp-note"><strong>Processamento local:</strong> o sistema extrai apenas frames representativos. OCR funciona quando o Tesseract está disponível; sem ele, o ViralLab estima a presença de texto visualmente.</div>',
    unsafe_allow_html=True,
)

uploaded = st.file_uploader("Escolha o vídeo de referência", type=["mp4", "mov", "m4v", "webm", "mkv"], help="Prefira vídeos de até 2 minutos no primeiro teste.")
c1, c2, c3 = st.columns(3)
threshold = c1.slider("Sensibilidade dos cortes", 0.15, 0.60, 0.30, 0.05)
model_size = c2.selectbox("Modelo de transcrição", ["tiny", "base", "small"], index=0)
max_moments = c3.slider("Frames-chave", 6, 24, 12, 2, help="Limita o custo da análise visual.")

if uploaded is not None:
    upload_key = f"{uploaded.name}:{uploaded.size}"
    if st.session_state.get("upload_key") != upload_key:
        file_id = uuid.uuid4().hex[:10]
        suffix = Path(uploaded.name).suffix.lower() or ".mp4"
        video_path = ANALYSIS_DIR / f"{file_id}{suffix}"
        video_path.write_bytes(uploaded.getbuffer())
        st.session_state.upload_key = upload_key
        st.session_state.analysis_video_path = str(video_path)
        for key in ("video_analysis", "semantic_analysis", "visual_analysis", "multimodal_timeline"):
            st.session_state.pop(key, None)
    else:
        video_path = Path(st.session_state.analysis_video_path)

    st.video(uploaded.getvalue())
    if st.button("Executar engenharia reversa completa", type="primary", use_container_width=True):
        try:
            with st.status("Analisando vídeo...", expanded=True) as status:
                st.write("1/4 · Lendo formato, duração, áudio e cortes...")
                structural = analyze_video(video_path, scene_threshold=threshold)
                st.write("2/4 · Transcrevendo fala, hook, narrativa e CTA...")
                semantic = transcribe_video(video_path, model_size=model_size, language="pt")
                st.write("3/4 · Extraindo frames, rosto, texto e enquadramentos...")
                frames_dir = ANALYSIS_DIR / f"{video_path.stem}-frames"
                visual = analyze_visuals(video_path, output_dir=frames_dir, scene_threshold=threshold, max_moments=max_moments)
                st.write("4/4 · Sincronizando fala e imagem no mapa temporal...")
                timeline = build_multimodal_timeline(semantic, visual)
                st.session_state.video_analysis = structural
                st.session_state.semantic_analysis = semantic
                st.session_state.visual_analysis = visual
                st.session_state.multimodal_timeline = timeline
                st.session_state.analysis_source_name = uploaded.name
                status.update(label="Engenharia reversa concluída", state="complete", expanded=False)
        except (VideoAnalysisError, SemanticAnalysisError, VisualAnalysisError) as exc:
            st.error(f"Não foi possível concluir a análise: {exc}")

analysis = st.session_state.get("video_analysis")
semantic = st.session_state.get("semantic_analysis")
visual = st.session_state.get("visual_analysis")
timeline = st.session_state.get("multimodal_timeline")

if analysis is not None:
    st.divider()
    st.subheader("Visão geral")
    st.write(analysis.summary)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pontuação estrutural", f"{analysis.viral_potential_score}/100")
    m2.metric("Cenas", analysis.estimated_scenes)
    m3.metric("Média por cena", f"{analysis.average_scene_seconds}s")
    m4.metric("Formato", f"{analysis.format_score}/100")

if semantic is not None:
    st.subheader("Linguagem e narrativa")
    st.write(semantic.summary)
    s1, s2, s3 = st.columns(3)
    s1.metric("Hook verbal", f"{semantic.hook_score}/100")
    s2.metric("CTA", f"{semantic.cta_score}/100")
    s3.metric("Velocidade", f"{semantic.words_per_minute} ppm")
    st.markdown("#### Hook identificado")
    st.info(semantic.hook_text)
    st.markdown("#### CTA identificado")
    st.success(semantic.cta_text) if semantic.cta_text else st.warning("Nenhuma chamada para ação explícita foi identificada.")

if visual is not None:
    st.divider()
    st.subheader("Leitura visual")
    st.write(visual.summary)
    v1, v2, v3, v4 = st.columns(4)
    v1.metric("Presença facial", f"{visual.face_presence_ratio:.0%}")
    v2.metric("Apoio textual", f"{visual.text_presence_ratio:.0%}")
    v3.metric("Mudanças de plano", visual.framing_changes)
    v4.metric("Plano dominante", visual.dominant_shot_type)

    st.markdown("#### Frames-chave")
    for start in range(0, len(visual.moments), 3):
        columns = st.columns(3)
        for column, moment in zip(columns, visual.moments[start:start + 3]):
            with column:
                st.image(moment.frame_path, caption=f"{moment.start:.1f}s · {moment.visual_role}", use_container_width=True)
                st.caption(f"{moment.shot_type} · rostos: {moment.face_count}")
                if moment.detected_text:
                    st.markdown(f"**Texto:** {moment.detected_text}")

if timeline:
    st.divider()
    st.subheader("Mapa temporal multimodal")
    st.caption("O ViralLab sincroniza o que é dito com o que aparece na tela.")
    for item in timeline:
        title = f"{item.start:.1f}s–{item.end:.1f}s · {item.narrative_label} · {item.visual_role}"
        with st.expander(title, expanded=item.narrative_label == "Hook"):
            st.markdown(f"**Fala:** {item.speech or 'Sem fala reconhecida'}")
            st.markdown(f"**Enquadramento:** {item.shot_type} · **Rosto:** {'sim' if item.face_present else 'não'}")
            if item.on_screen_text:
                st.markdown(f"**Texto na tela:** {item.on_screen_text}")
            st.info(item.recommendation)

if analysis is not None and semantic is not None and visual is not None:
    left, right = st.columns(2)
    with left:
        st.markdown("#### O que funciona")
        for item in analysis.strengths + semantic.strengths + visual.strengths:
            st.success(item)
    with right:
        st.markdown("#### O que melhorar")
        for item in analysis.improvements + semantic.improvements + visual.improvements:
            st.warning(item)

    combined = {
        "source": st.session_state.get("analysis_source_name"),
        "structural": analysis.to_dict(),
        "semantic": semantic.to_dict(),
        "visual": visual.to_dict(),
        "timeline": [item.to_dict() for item in timeline or []],
    }
    d1, d2 = st.columns(2)
    d1.download_button("Baixar relatório multimodal", json.dumps(combined, ensure_ascii=False, indent=2), "analise-multimodal-virallab.json", "application/json", use_container_width=True)
    d2.download_button("Baixar legendas SRT", semantic.to_srt(), "legendas-virallab.srt", "application/x-subrip", use_container_width=True)

    st.divider()
    st.subheader("Criar uma versão RP")
    st.caption("A nova versão reutiliza a arquitetura narrativa e audiovisual, sem copiar o conteúdo original.")
    theme = st.text_input("Tema da nova versão", value="IA aplicada à fisioterapia")
    audience = st.text_input("Público", value="fisioterapeutas brasileiros")
    objective = st.selectbox("Objetivo", ["educar", "gerar autoridade", "ganhar seguidores qualificados", "engajar", "vender"])
    r1, r2 = st.columns(2)
    duration = r1.slider("Duração", 15, 90, min(60, max(15, round(analysis.duration_seconds / 5) * 5)), 5)
    evidence = r2.selectbox("Base", ["educacional", "cientifico", "opiniao"])
    cta = st.text_input("Chamada para ação", value="Siga o Professor RP para aprender inovação e IA aplicada à saúde.")
    if st.button("Criar roteiro original com esta arquitetura", type="primary", use_container_width=True):
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
