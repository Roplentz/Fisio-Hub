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

st.set_page_config(page_title="Engenharia reversa · RP ViralLab", page_icon="◉", layout="wide", initial_sidebar_state="collapsed")
st.markdown(
    """
    <style>
    :root { --bg:#061018; --line:rgba(255,255,255,.10); --cyan:#45d6dc; --muted:#91a6b4; }
    .stApp { background:radial-gradient(circle at 90% 0%,rgba(69,214,220,.14),transparent 30%),var(--bg); }
    .block-container { max-width:1160px; padding-top:1.2rem; padding-bottom:4rem; }
    .head { border:1px solid var(--line); background:linear-gradient(135deg,#142d3b,#091a24); padding:26px; border-radius:25px; margin-bottom:18px; }
    .kicker { color:var(--cyan); font-size:11px; font-weight:900; letter-spacing:.13em; text-transform:uppercase; }
    .head h1 { color:white; margin:.35rem 0; font-size:34px; letter-spacing:-1.2px; }
    .head p { color:var(--muted); margin:0; }
    [data-testid="stMetric"] { background:linear-gradient(180deg,#132a38,#0b1c27); border:1px solid var(--line); border-radius:17px; padding:14px; }
    [data-testid="stFileUploaderDropzone"] { background:#091923; border:1px dashed rgba(69,214,220,.45); border-radius:18px; }
    .stButton>button,.stDownloadButton>button { min-height:46px; border-radius:13px; font-weight:800; }
    .note { border-left:3px solid var(--cyan); background:rgba(69,214,220,.06); padding:12px 14px; border-radius:0 12px 12px 0; color:#bdd0da; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown('<section class="head"><div class="kicker">Engenharia reversa ética</div><h1>Análise multimodal</h1><p>Estrutura, fala, hook, CTA, frames, rostos, enquadramentos, textos e mapa temporal.</p></section>', unsafe_allow_html=True)

pending_path = st.session_state.get("pending_video_path")
pending_name = st.session_state.get("pending_video_name")
pending_source = st.session_state.get("pending_video_source")
video_path: Path | None = Path(pending_path) if pending_path and Path(pending_path).exists() else None

if video_path is not None:
    source_label = "URL pública" if pending_source and pending_source != "upload" else "Upload"
    st.markdown(f'<div class="note"><strong>Vídeo recebido pela Home:</strong> {pending_name or video_path.name} · origem: {source_label}</div>', unsafe_allow_html=True)
    st.video(str(video_path))
    if pending_source and pending_source not in {"upload", None}:
        st.caption(f"Fonte: {pending_source}")
    replace = st.checkbox("Substituir por outro arquivo", value=False)
else:
    replace = True

if replace:
    uploaded = st.file_uploader("Escolha o vídeo de referência", type=["mp4", "mov", "m4v", "webm", "mkv"])
    if uploaded is not None:
        key = f"{uploaded.name}:{uploaded.size}"
        if st.session_state.get("analysis_upload_key") != key:
            suffix = Path(uploaded.name).suffix.lower() or ".mp4"
            video_path = ANALYSIS_DIR / f"{uuid.uuid4().hex[:10]}{suffix}"
            video_path.write_bytes(uploaded.getbuffer())
            st.session_state.analysis_upload_key = key
            st.session_state.pending_video_path = str(video_path)
            st.session_state.pending_video_name = uploaded.name
            st.session_state.pending_video_source = "upload"
            for item in ("video_analysis", "semantic_analysis", "visual_analysis", "multimodal_timeline"):
                st.session_state.pop(item, None)
        else:
            video_path = Path(st.session_state.pending_video_path)
        st.video(uploaded.getvalue())

c1, c2, c3 = st.columns(3)
threshold = c1.slider("Sensibilidade dos cortes", 0.15, 0.60, 0.30, 0.05)
model_size = c2.selectbox("Modelo de transcrição", ["tiny", "base", "small"], index=0)
max_moments = c3.slider("Frames-chave", 6, 24, 10, 2)

if video_path is not None and st.button("Executar engenharia reversa completa  →", type="primary", use_container_width=True):
    try:
        with st.status("Analisando vídeo...", expanded=True) as status:
            st.write("1/4 · Estrutura, duração, áudio e cortes")
            structural = analyze_video(video_path, scene_threshold=threshold)
            st.write("2/4 · Transcrição, hook, narrativa e CTA")
            semantic = transcribe_video(video_path, model_size=model_size, language="pt")
            st.write("3/4 · Frames, rostos, textos e enquadramentos")
            frames_dir = ANALYSIS_DIR / f"{video_path.stem}-frames"
            visual = analyze_visuals(video_path, output_dir=frames_dir, scene_threshold=threshold, max_moments=max_moments)
            st.write("4/4 · Sincronização do mapa temporal")
            timeline = build_multimodal_timeline(semantic, visual)
            st.session_state.video_analysis = structural
            st.session_state.semantic_analysis = semantic
            st.session_state.visual_analysis = visual
            st.session_state.multimodal_timeline = timeline
            st.session_state.analysis_source_name = pending_name or video_path.name
            status.update(label="Engenharia reversa concluída", state="complete", expanded=False)
    except (VideoAnalysisError, SemanticAnalysisError, VisualAnalysisError) as exc:
        st.error(f"Não foi possível concluir a análise: {exc}")

analysis = st.session_state.get("video_analysis")
semantic = st.session_state.get("semantic_analysis")
visual = st.session_state.get("visual_analysis")
timeline = st.session_state.get("multimodal_timeline")

if analysis is not None:
    st.divider()
    st.subheader("Dashboard executivo")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pontuação estrutural", f"{analysis.viral_potential_score}/100")
    m2.metric("Cenas", analysis.estimated_scenes)
    m3.metric("Média por cena", f"{analysis.average_scene_seconds}s")
    m4.metric("Formato", f"{analysis.format_score}/100")

if semantic is not None:
    s1, s2, s3 = st.columns(3)
    s1.metric("Hook verbal", f"{semantic.hook_score}/100")
    s2.metric("CTA", f"{semantic.cta_score}/100")
    s3.metric("Velocidade", f"{semantic.words_per_minute} ppm")
    a, b = st.columns(2)
    a.info(f"Hook: {semantic.hook_text}")
    b.success(f"CTA: {semantic.cta_text}") if semantic.cta_text else b.warning("CTA explícito não identificado.")

if visual is not None:
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
    st.markdown("#### Mapa temporal multimodal")
    for item in timeline:
        with st.expander(f"{item.start:.1f}s–{item.end:.1f}s · {item.narrative_label} · {item.visual_role}", expanded=item.narrative_label == "Hook"):
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

    combined = {"source": st.session_state.get("analysis_source_name"), "source_url": pending_source if pending_source not in {"upload", None} else None, "structural": analysis.to_dict(), "semantic": semantic.to_dict(), "visual": visual.to_dict(), "timeline": [item.to_dict() for item in timeline or []]}
    d1, d2 = st.columns(2)
    d1.download_button("Baixar relatório multimodal", json.dumps(combined, ensure_ascii=False, indent=2), "analise-multimodal-virallab.json", "application/json", use_container_width=True)
    d2.download_button("Baixar legendas SRT", semantic.to_srt(), "legendas-virallab.srt", "application/x-subrip", use_container_width=True)

    st.divider()
    st.subheader("Criar uma versão original")
    st.caption("A arquitetura narrativa e audiovisual orienta a criação, sem copiar o conteúdo da referência.")
    theme = st.text_input("Tema da nova versão", value="IA aplicada à fisioterapia")
    audience = st.text_input("Público", value="fisioterapeutas brasileiros")
    objective = st.selectbox("Objetivo", ["educar", "gerar autoridade", "ganhar seguidores qualificados", "engajar", "vender"])
    r1, r2 = st.columns(2)
    duration = r1.slider("Duração", 15, 90, min(60, max(15, round(analysis.duration_seconds / 5) * 5)), 5)
    evidence = r2.selectbox("Base", ["educacional", "cientifico", "opiniao"])
    cta = st.text_input("Chamada para ação", value="Siga o Professor RP para aprender inovação e IA aplicada à saúde.")
    if st.button("Criar versão com esta arquitetura  →", type="primary", use_container_width=True):
        try:
            brief = VideoBrief(theme=theme, objective=objective, audience=audience, duration_seconds=duration, format="professor_cinematico", cta=cta, evidence_level=evidence)
            package = generate_video_package(brief, provider=select_provider("local"))
            project_id = uuid.uuid4().hex[:10]
            output_dir = PROJECTS_DIR / project_id
            export_package(package, output_dir)
            (output_dir / "reference-analysis.json").write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")
            st.session_state.project_id = project_id
            st.session_state.package = package
            st.session_state.package_dir = str(output_dir)
            st.session_state.preferred_hook = package.hook
            st.session_state.workspace_view = "Studio"
            st.success("Projeto original criado e conectado ao Studio.")
            st.markdown(f"**Hook sugerido:** {package.hook}")
            st.page_link("app.py", label="Continuar no Studio", icon="🎬", use_container_width=True)
        except Exception as exc:
            st.error(f"Não foi possível criar a versão: {exc}")

st.divider()
st.page_link("app.py", label="Voltar à Home", icon="↩️")
