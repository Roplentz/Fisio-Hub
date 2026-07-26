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

from virallab.editorial_analyzer import analyze_editorially
from virallab.generator import export_package, generate_video_package
from virallab.models import VideoBrief
from virallab.providers import select_provider
from virallab.semantic_analyzer import (
    SemanticAnalysisError,
    transcribe_video,
    unavailable_semantic_analysis,
)
from virallab.timeline_builder import build_multimodal_timeline
from virallab.video_analyzer import VideoAnalysisError, analyze_video
from virallab.visual_analyzer import VisualAnalysisError, analyze_visuals
from virallab.workflow_transition import clear_analysis_state, handoff_analysis_project

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
    :root{--bg:#061018;--line:rgba(255,255,255,.10);--cyan:#45d6dc;--muted:#91a6b4}
    .stApp{background:radial-gradient(circle at 90% 0%,rgba(69,214,220,.14),transparent 30%),var(--bg)}
    .block-container{max-width:1080px;padding-top:1rem;padding-bottom:5rem}
    .head{border:1px solid var(--line);background:linear-gradient(135deg,#142d3b,#091a24);padding:28px;border-radius:25px;margin-bottom:18px}
    .head h1{color:white;margin:.4rem 0;font-size:39px;letter-spacing:-1.5px}.head p{color:#b4c5cf;margin:0}
    .kicker{color:var(--cyan);font-size:11px;font-weight:900;letter-spacing:.13em;text-transform:uppercase}
    .note{border-left:3px solid var(--cyan);background:rgba(69,214,220,.06);padding:13px 15px;border-radius:0 13px 13px 0;color:#bdd0da}
    .score{padding:22px;border:1px solid var(--line);border-radius:20px;text-align:center;background:#0b1c27}.score strong{display:block;color:white;font-size:45px}.score span{color:var(--muted)}
    .stButton>button,.stDownloadButton>button{min-height:50px;border-radius:14px;font-weight:800}
    @media(max-width:720px){.head{padding:19px}.head h1{font-size:29px}.block-container{padding:.5rem .8rem 5rem}[data-testid="column"]{min-width:100%!important}}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<section class="head"><div class="kicker">Etapa 01</div><h1>Analisar vídeo</h1><p>Extraia estrutura, fala, ritmo, visual e CTA. Depois, transforme a análise em um roteiro original e continue automaticamente no Studio.</p></section>',
    unsafe_allow_html=True,
)

pending_path = st.session_state.get("pending_video_path")
pending_name = st.session_state.get("pending_video_name")
pending_source = st.session_state.get("pending_video_source")
video_path = (
    Path(pending_path) if pending_path and Path(pending_path).exists() else None
)

if video_path is not None:
    source_label = "URL pública" if pending_source not in {None, "upload"} else "Upload"
    st.markdown(
        f'<div class="note"><strong>Vídeo selecionado:</strong> {pending_name or video_path.name} · {source_label}</div>',
        unsafe_allow_html=True,
    )
    st.video(str(video_path))
    replace = st.checkbox("Trocar o vídeo", value=False)
else:
    replace = True

if replace:
    uploaded = st.file_uploader(
        "Envie o vídeo",
        type=["mp4", "mov", "m4v", "webm", "mkv"],
        key="analysis-video-upload",
    )
    if uploaded is not None:
        upload_key = f"{uploaded.name}:{uploaded.size}"
        if st.session_state.get("analysis_upload_key") != upload_key:
            clear_analysis_state(st.session_state, keep_video=False)
            suffix = Path(uploaded.name).suffix.lower() or ".mp4"
            video_path = ANALYSIS_DIR / f"{uuid.uuid4().hex[:10]}{suffix}"
            video_path.write_bytes(uploaded.getbuffer())
            st.session_state.analysis_upload_key = upload_key
            st.session_state.pending_video_path = str(video_path)
            st.session_state.pending_video_name = uploaded.name
            st.session_state.pending_video_source = "upload"
            pending_name = uploaded.name
            pending_source = "upload"
        else:
            video_path = Path(st.session_state.pending_video_path)
        st.video(uploaded.getvalue())

threshold, model_size, max_moments = 0.30, "base", 10
with st.expander("Configurações avançadas", expanded=False):
    c1, c2, c3 = st.columns(3)
    threshold = c1.slider("Sensibilidade dos cortes", 0.15, 0.60, 0.30, 0.05)
    model_size = c2.selectbox(
        "Precisão da transcrição",
        ["tiny", "base", "small"],
        index=1,
        format_func=lambda value: {
            "tiny": "Rápida",
            "base": "Equilibrada",
            "small": "Mais precisa",
        }[value],
    )
    max_moments = c3.slider("Quantidade de frames", 6, 24, 10, 2)

if video_path is not None and st.button(
    "Analisar conteúdo profundamente →", type="primary", use_container_width=True
):
    missing = [
        binary for binary in ("ffmpeg", "ffprobe") if shutil.which(binary) is None
    ]
    if missing:
        st.error("O motor de vídeo ainda não está disponível no servidor.")
        st.code("Ausente: " + ", ".join(missing))
    else:
        clear_analysis_state(st.session_state, keep_video=True)
        warnings: list[str] = []
        try:
            with st.status("Interpretando o conteúdo...", expanded=True) as status:
                st.write("1/4 · Estrutura, duração, cortes e ritmo")
                structural = analyze_video(video_path, scene_threshold=threshold)

                st.write("2/4 · Transcrição e leitura da fala")
                try:
                    semantic = transcribe_video(
                        video_path, model_size=model_size, language="pt"
                    )
                    if semantic.warning:
                        warnings.append(semantic.warning)
                except SemanticAnalysisError as exc:
                    warnings.append(str(exc))
                    semantic = unavailable_semantic_analysis(str(exc))
                    st.warning(
                        "A transcrição falhou; a análise continuará com estrutura e imagem."
                    )

                st.write("3/4 · Frames, enquadramento e mudanças visuais")
                frames_dir = ANALYSIS_DIR / f"{video_path.stem}-frames"
                visual = analyze_visuals(
                    video_path,
                    output_dir=frames_dir,
                    scene_threshold=threshold,
                    max_moments=max_moments,
                )

                st.write("4/4 · Diagnóstico editorial integrado")
                timeline = build_multimodal_timeline(semantic, visual)
                editorial = analyze_editorially(structural, semantic, visual, timeline)

                st.session_state.video_analysis = structural
                st.session_state.semantic_analysis = semantic
                st.session_state.visual_analysis = visual
                st.session_state.multimodal_timeline = timeline
                st.session_state.editorial_analysis = editorial
                st.session_state.analysis_warnings = warnings
                st.session_state.analysis_source_name = pending_name or video_path.name
                status.update(
                    label="Análise concluída"
                    if not warnings
                    else "Análise parcial concluída",
                    state="complete",
                    expanded=False,
                )
                st.rerun()
        except (VideoAnalysisError, VisualAnalysisError) as exc:
            st.error("Não foi possível concluir uma etapa essencial da análise.")
            st.code(str(exc))
        except Exception as exc:
            st.error("A análise não pôde ser concluída.")
            st.code(f"{type(exc).__name__}: {exc}")

analysis = st.session_state.get("video_analysis")
semantic = st.session_state.get("semantic_analysis")
visual = st.session_state.get("visual_analysis")
timeline = st.session_state.get("multimodal_timeline")
editorial = st.session_state.get("editorial_analysis")
warnings = st.session_state.get("analysis_warnings", [])

if all(item is not None for item in (analysis, semantic, visual, editorial)):
    st.divider()
    if warnings:
        st.warning(
            "A análise foi concluída com limitações, mas os dados disponíveis foram preservados."
        )
    else:
        st.success("Análise concluída com sucesso.")

    left, right = st.columns([0.34, 0.66], gap="large")
    with left:
        st.markdown(
            f'<div class="score"><strong>{editorial.content_score}/100</strong><span>força editorial</span></div>',
            unsafe_allow_html=True,
        )
    with right:
        st.subheader("Leitura executiva")
        st.write(editorial.executive_summary)
        st.info(f"Prioridade: {editorial.priority_action}")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Conteúdo", f"{editorial.content_score}/100")
    m2.metric("Retenção", f"{editorial.retention_score}/100")
    m3.metric("Persuasão", f"{editorial.persuasion_score}/100")
    m4.metric("Clareza", f"{editorial.clarity_score}/100")

    with st.expander("Ver diagnóstico completo", expanded=False):
        st.markdown("### Tese central")
        st.write(editorial.thesis)
        st.markdown("### Promessa")
        st.write(editorial.promise)
        st.markdown("### Público inferido")
        st.write(editorial.target_audience)
        st.markdown("### Hook")
        st.write(editorial.hook_diagnosis)
        st.markdown("### Retenção")
        st.write(editorial.retention_diagnosis)
        st.markdown("### Visual")
        st.write(editorial.visual_diagnosis)
        st.markdown("### CTA")
        st.write(editorial.cta_diagnosis)
        st.markdown("### Fórmula reproduzível")
        for index, step in enumerate(editorial.reusable_formula, start=1):
            st.write(f"{index}. {step}")

    combined = {
        "source": st.session_state.get("analysis_source_name"),
        "source_url": pending_source
        if pending_source not in {"upload", None}
        else None,
        "warnings": warnings,
        "editorial": editorial.to_dict(),
        "structural": analysis.to_dict(),
        "semantic": semantic.to_dict(),
        "visual": visual.to_dict(),
        "timeline": [item.to_dict() for item in timeline or []],
    }

    st.download_button(
        "Baixar relatório da análise",
        json.dumps(combined, ensure_ascii=False, indent=2),
        "analise-editorial-virallab.json",
        "application/json",
        use_container_width=True,
    )

    st.divider()
    st.subheader("Criar uma versão original")
    st.caption(
        "A nova versão usará a estrutura aprendida, sem copiar literalmente o vídeo de referência."
    )
    theme = st.text_input(
        "Tema da nova versão", value=editorial.thesis or "IA aplicada à fisioterapia"
    )
    audience = st.text_input(
        "Público", value=editorial.target_audience or "fisioterapeutas brasileiros"
    )
    objective = st.selectbox(
        "Objetivo",
        [
            "educar",
            "gerar autoridade",
            "ganhar seguidores qualificados",
            "engajar",
            "vender",
        ],
    )
    cta = st.text_input(
        "CTA",
        value="Siga o Professor RP para aprender inovação e IA aplicada à saúde.",
    )

    if st.button(
        "Criar versão e continuar no Roteiro →",
        type="primary",
        use_container_width=True,
    ):
        try:
            brief = VideoBrief(
                theme=theme,
                objective=objective,
                audience=audience,
                duration_seconds=min(
                    60, max(15, round(analysis.duration_seconds / 5) * 5)
                ),
                format="professor_cinematico",
                cta=cta,
                evidence_level="educacional",
            )
            package = generate_video_package(brief, provider=select_provider("auto"))
            project_id = uuid.uuid4().hex[:10]
            output_dir = PROJECTS_DIR / project_id
            export_package(package, output_dir)
            reference_path = output_dir / "reference-analysis.json"
            reference_path.write_text(
                json.dumps(combined, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            handoff_analysis_project(
                st.session_state,
                project_id=project_id,
                package=package,
                package_dir=str(output_dir),
                reference_analysis_path=str(reference_path),
            )
            st.switch_page("app.py")
        except Exception as exc:
            st.error(f"Não foi possível criar a nova versão: {exc}")

st.divider()
back_col, new_col = st.columns(2)
back_col.page_link(
    "app.py", label="Voltar ao Studio", icon="↩️", use_container_width=True
)
if new_col.button("Limpar análise e começar outra", use_container_width=True):
    clear_analysis_state(st.session_state, keep_video=False)
    st.rerun()
