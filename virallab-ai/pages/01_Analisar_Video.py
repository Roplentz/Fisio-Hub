from __future__ import annotations

import json
import shutil
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
    :root { --bg:#061018; --line:rgba(255,255,255,.10); --cyan:#45d6dc; --muted:#91a6b4; --green:#78dfa5; }
    .stApp { background:radial-gradient(circle at 90% 0%,rgba(69,214,220,.14),transparent 30%),var(--bg); }
    .block-container { max-width:1080px; padding-top:1.1rem; padding-bottom:4rem; }
    .head { border:1px solid var(--line); background:linear-gradient(135deg,#142d3b,#091a24); padding:30px; border-radius:27px; margin-bottom:18px; }
    .kicker { color:var(--cyan); font-size:11px; font-weight:900; letter-spacing:.13em; text-transform:uppercase; }
    .head h1 { color:white; margin:.4rem 0; font-size:40px; letter-spacing:-1.7px; }
    .head p { color:#b4c5cf; margin:0; font-size:16px; max-width:760px; }
    .note { border-left:3px solid var(--cyan); background:rgba(69,214,220,.06); padding:13px 15px; border-radius:0 13px 13px 0; color:#bdd0da; }
    .score { padding:24px; border:1px solid var(--line); border-radius:22px; text-align:center; background:linear-gradient(180deg,#132a38,#0b1c27); }
    .score strong { display:block; color:white; font-size:48px; line-height:1; }
    .score span { color:var(--muted); font-size:13px; }
    [data-testid="stMetric"] { background:linear-gradient(180deg,#132a38,#0b1c27); border:1px solid var(--line); border-radius:17px; padding:14px; }
    [data-testid="stFileUploaderDropzone"] { background:#091923; border:1px dashed rgba(69,214,220,.45); border-radius:18px; }
    .stButton>button,.stDownloadButton>button { min-height:50px; border-radius:14px; font-weight:850; }
    .stButton>button[kind="primary"] { background:linear-gradient(135deg,var(--cyan),#188da0); color:#031014; border:none; }
    @media(max-width:720px){.head{padding:22px}.head h1{font-size:32px}.block-container{padding-left:1rem;padding-right:1rem}}
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    '<section class="head"><div class="kicker">Engenharia reversa de conteúdo</div><h1>Descubra por que este vídeo prende a atenção</h1><p>O ViralLab analisa estrutura, fala, hook, ritmo, visual e chamada para ação — e transforma tudo em uma arquitetura que você pode usar para criar uma versão original.</p></section>',
    unsafe_allow_html=True,
)

pending_path = st.session_state.get("pending_video_path")
pending_name = st.session_state.get("pending_video_name")
pending_source = st.session_state.get("pending_video_source")
video_path: Path | None = Path(pending_path) if pending_path and Path(pending_path).exists() else None

if video_path is not None:
    source_label = "URL pública" if pending_source and pending_source != "upload" else "Upload"
    st.markdown(f'<div class="note"><strong>Vídeo pronto para análise:</strong> {pending_name or video_path.name} · origem: {source_label}</div>', unsafe_allow_html=True)
    st.video(str(video_path))
    replace = st.checkbox("Usar outro vídeo", value=False)
else:
    replace = True

if replace:
    uploaded = st.file_uploader("Envie o vídeo", type=["mp4", "mov", "m4v", "webm", "mkv"], help="Para o primeiro teste, prefira vídeos de até 2 minutos.")
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

threshold, model_size, max_moments = 0.30, "tiny", 8
with st.expander("⚙️ Configurações avançadas", expanded=False):
    st.caption("Os padrões já estão otimizados para uma análise rápida. Altere apenas quando necessário.")
    c1, c2, c3 = st.columns(3)
    threshold = c1.slider("Sensibilidade dos cortes", 0.15, 0.60, 0.30, 0.05)
    model_size = c2.selectbox("Precisão da transcrição", ["tiny", "base", "small"], index=0, format_func=lambda value: {"tiny":"Rápida", "base":"Equilibrada", "small":"Mais precisa"}[value])
    max_moments = c3.slider("Quantidade de frames", 6, 24, 8, 2)

if video_path is not None and st.button("Analisar vídeo  →", type="primary", use_container_width=True):
    missing = [binary for binary in ("ffmpeg", "ffprobe") if shutil.which(binary) is None]
    if missing:
        st.error("O servidor ainda está concluindo a instalação do motor de vídeo. Aguarde o novo deploy e tente novamente em alguns minutos.")
        st.caption(f"Componente indisponível: {', '.join(missing)}")
    else:
        try:
            with st.status("Analisando seu vídeo...", expanded=True) as status:
                st.write("✓ Entendendo estrutura, duração e cortes")
                structural = analyze_video(video_path, scene_threshold=threshold)
                st.write("✓ Interpretando fala, hook, narrativa e CTA")
                semantic = transcribe_video(video_path, model_size=model_size, language="pt")
                st.write("✓ Lendo frames, rostos, textos e enquadramentos")
                frames_dir = ANALYSIS_DIR / f"{video_path.stem}-frames"
                visual = analyze_visuals(video_path, output_dir=frames_dir, scene_threshold=threshold, max_moments=max_moments)
                st.write("✓ Construindo o mapa temporal")
                timeline = build_multimodal_timeline(semantic, visual)
                st.session_state.video_analysis = structural
                st.session_state.semantic_analysis = semantic
                st.session_state.visual_analysis = visual
                st.session_state.multimodal_timeline = timeline
                st.session_state.analysis_source_name = pending_name or video_path.name
                status.update(label="Análise concluída", state="complete", expanded=False)
        except (VideoAnalysisError, SemanticAnalysisError, VisualAnalysisError) as exc:
            st.error("Não foi possível concluir esta análise.")
            with st.expander("Ver detalhe técnico"):
                st.code(str(exc))

analysis = st.session_state.get("video_analysis")
semantic = st.session_state.get("semantic_analysis")
visual = st.session_state.get("visual_analysis")
timeline = st.session_state.get("multimodal_timeline")

if analysis is not None and semantic is not None and visual is not None:
    st.divider()
    overall = round((analysis.viral_potential_score + semantic.hook_score + semantic.cta_score + analysis.pacing_score + analysis.format_score) / 5)
    label = "Excelente estrutura" if overall >= 85 else "Boa estrutura" if overall >= 70 else "Estrutura com oportunidades"
    left, right = st.columns([0.34, 0.66], gap="large")
    with left:
        st.markdown(f'<div class="score"><strong>{overall}/100</strong><span>{label}</span></div>', unsafe_allow_html=True)
    with right:
        st.subheader("Seu diagnóstico")
        st.write(analysis.summary)
        q1, q2, q3 = st.columns(3)
        q1.metric("Hook", f"{semantic.hook_score}/100")
        q2.metric("Ritmo", f"{analysis.pacing_score}/100")
        q3.metric("CTA", f"{semantic.cta_score}/100")

    st.markdown("### O que mais importa")
    a, b = st.columns(2)
    with a:
        for item in (analysis.strengths + semantic.strengths + visual.strengths)[:4]:
            st.success(item)
    with b:
        for item in (analysis.improvements + semantic.improvements + visual.improvements)[:4]:
            st.warning(item)

    with st.expander("Ver relatório completo", expanded=False):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Cenas", analysis.estimated_scenes)
        m2.metric("Média por cena", f"{analysis.average_scene_seconds}s")
        m3.metric("Presença facial", f"{visual.face_presence_ratio:.0%}")
        m4.metric("Mudanças de plano", visual.framing_changes)
        st.info(f"Hook identificado: {semantic.hook_text}")
        if semantic.cta_text:
            st.success(f"CTA identificado: {semantic.cta_text}")
        st.markdown("#### Frames-chave")
        for start in range(0, len(visual.moments), 3):
            columns = st.columns(3)
            for column, moment in zip(columns, visual.moments[start:start + 3]):
                with column:
                    st.image(moment.frame_path, caption=f"{moment.start:.1f}s · {moment.visual_role}", use_container_width=True)
        st.markdown("#### Mapa temporal")
        for item in timeline or []:
            with st.expander(f"{item.start:.1f}s–{item.end:.1f}s · {item.narrative_label}"):
                st.write(item.speech or "Sem fala reconhecida")
                st.info(item.recommendation)

    combined = {"source": st.session_state.get("analysis_source_name"), "source_url": pending_source if pending_source not in {"upload", None} else None, "score": overall, "structural": analysis.to_dict(), "semantic": semantic.to_dict(), "visual": visual.to_dict(), "timeline": [item.to_dict() for item in timeline or []]}
    d1, d2 = st.columns(2)
    d1.download_button("Baixar relatório", json.dumps(combined, ensure_ascii=False, indent=2), "analise-virallab.json", "application/json", use_container_width=True)
    d2.download_button("Baixar legendas", semantic.to_srt(), "legendas-virallab.srt", "application/x-subrip", use_container_width=True)

    st.divider()
    st.subheader("Crie sua versão original")
    st.caption("Use a arquitetura que funcionou sem copiar o conteúdo da referência.")
    theme = st.text_input("Qual será o tema?", value="IA aplicada à fisioterapia")
    audience = st.text_input("Para quem?", value="fisioterapeutas brasileiros")
    objective = st.selectbox("O que você quer alcançar?", ["educar", "gerar autoridade", "ganhar seguidores qualificados", "engajar", "vender"])
    cta = st.text_input("Próximo passo para o público", value="Siga o Professor RP para aprender inovação e IA aplicada à saúde.")
    if st.button("Criar minha versão  →", type="primary", use_container_width=True):
        try:
            brief = VideoBrief(theme=theme, objective=objective, audience=audience, duration_seconds=min(60, max(15, round(analysis.duration_seconds / 5) * 5)), format="professor_cinematico", cta=cta, evidence_level="educacional")
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
            st.success("Sua versão foi criada e está pronta no Studio.")
            st.page_link("app.py", label="Continuar no Studio", icon="🎬", use_container_width=True)
        except Exception as exc:
            st.error(f"Não foi possível criar a versão: {exc}")

st.divider()
st.page_link("app.py", label="Voltar à Home", icon="↩️")
