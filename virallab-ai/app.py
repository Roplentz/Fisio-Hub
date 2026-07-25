from __future__ import annotations

import html
import json
import shutil
import uuid
from pathlib import Path

import streamlit as st

from virallab.asset_library import AssetLibrary
from virallab.author_profile import AuthorProfileStore
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
from virallab.voice import (
    VoiceError,
    load_voice_plan,
    save_narration,
    update_voice_plan_with_scenes,
)
from virallab.voice_renderer import render_video_with_voice

APP_ROOT = Path(__file__).resolve().parent
WORKSPACE = APP_ROOT / "workspace"
ANALYSIS_DIR = WORKSPACE / "analysis"
PROJECTS_DIR = WORKSPACE / "projects"
LEARNING_STORE = WORKSPACE / "learning" / "feedback.jsonl"
for directory in (WORKSPACE, ANALYSIS_DIR, PROJECTS_DIR, LEARNING_STORE.parent):
    directory.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="RP ViralLab Studio 2.0",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    """
    <style>
    :root{--bg:#061018;--panel:#0d1d28;--line:rgba(255,255,255,.10);--text:#f6f9fb;--muted:#91a6b4;--cyan:#45d6dc}
    .stApp{background:radial-gradient(circle at 85% 0%,rgba(69,214,220,.15),transparent 30%),var(--bg);color:var(--text)}
    .block-container{max-width:1420px;padding-top:1rem;padding-bottom:4rem}
    [data-testid="stSidebar"]{background:linear-gradient(180deg,#08151e,#0b1b26);border-right:1px solid var(--line)}
    .hero{padding:30px;border:1px solid var(--line);border-radius:26px;background:linear-gradient(135deg,rgba(20,45,59,.98),rgba(8,24,34,.97));margin-bottom:18px}
    .hero h1{color:white;font-size:42px;letter-spacing:-2px;margin:.35rem 0}.hero p{color:#b3c4ce;margin:0}.kicker{color:var(--cyan);font-size:11px;font-weight:900;letter-spacing:.14em;text-transform:uppercase}
    .scene-card{padding:18px;border-radius:18px;border:1px solid var(--line);background:rgba(13,29,40,.92);margin-bottom:10px}.scene-head{display:flex;justify-content:space-between;gap:10px;color:white;font-weight:800}.scene-label{margin-top:9px;color:var(--muted);font-size:10px;font-weight:800;text-transform:uppercase}.scene-text{color:#d8e5ea;font-size:13px;margin-top:3px}
    .step{padding:13px;border:1px solid var(--line);border-radius:14px;background:rgba(69,214,220,.05)}
    .stButton>button,.stDownloadButton>button{min-height:48px;border-radius:13px;font-weight:800}
    @media(max-width:720px){.hero{padding:20px}.hero h1{font-size:28px}.block-container{padding:.7rem .8rem 3rem}[data-testid="column"]{min-width:100%!important}.stTabs [data-baseweb="tab-list"]{gap:4px;overflow-x:auto}.stTabs [data-baseweb="tab"]{padding:0 10px;white-space:nowrap}}
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
        "nav_view": "Studio 2.0",
        "pending_video_path": None,
        "pending_video_name": None,
        "pending_video_source": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def new_project() -> None:
    st.session_state.project_id = uuid.uuid4().hex[:10]
    st.session_state.package = None
    st.session_state.package_dir = None
    st.session_state.preferred_hook = ""


def save_uploaded_file(uploaded_file, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(uploaded_file.getbuffer())
    return destination


def open_analysis(path: Path, name: str, source: str) -> None:
    st.session_state.pending_video_path = str(path)
    st.session_state.pending_video_name = name
    st.session_state.pending_video_source = source
    st.switch_page("pages/01_Analisar_Video.py")


def render_scene_cards(package) -> None:
    labels = {
        "avatar": "Autor",
        "title_card": "Impacto",
        "broll": "Apoio",
        "screen_capture": "Tela",
        "proof": "Prova",
    }
    for scene in package.scenes:
        st.markdown(
            f'<div class="scene-card"><div class="scene-head"><span>Cena {scene.index} · {labels.get(scene.scene_type, scene.scene_type)}</span><span>{scene.start:.1f}–{scene.end:.1f}s</span></div><div class="scene-label">Narração</div><div class="scene-text">{html.escape(scene.narration or "—")}</div><div class="scene-label">Texto na tela</div><div class="scene-text">{html.escape(scene.on_screen_text or "—")}</div><div class="scene-label">Direção visual</div><div class="scene-text">{html.escape(scene.visual_direction or "—")}</div></div>',
            unsafe_allow_html=True,
        )


def render_profile() -> None:
    store = AuthorProfileStore(WORKSPACE)
    profile = store.load()
    st.subheader("Perfil visual do autor")
    st.caption(
        "A imagem fica salva como referência recorrente para as cenas em que o autor aparece."
    )
    left, right = st.columns([0.8, 1.2], gap="large")
    with left:
        if profile:
            st.image(
                profile.image_path,
                caption=f"{profile.name} · {profile.role}",
                use_container_width=True,
            )
            if st.button("Remover referência", use_container_width=True):
                store.delete()
                st.rerun()
        else:
            st.info("Nenhuma referência cadastrada.")
    with right:
        name = st.text_input(
            "Nome", value=profile.name if profile else "Prof. Dr. Rodrigo Plentz"
        )
        role = st.text_input(
            "Papel", value=profile.role if profile else "Autor e especialista"
        )
        notes = st.text_area(
            "Diretrizes visuais",
            value=profile.visual_notes
            if profile
            else "Aparência profissional, segura e acolhedora; preservar rosto, cabelo e idade aparente.",
            height=100,
        )
        image = st.file_uploader(
            "Foto de referência",
            type=["png", "jpg", "jpeg", "webp"],
            key="author-reference-v2",
        )
        if st.button(
            "Salvar perfil visual",
            type="primary",
            use_container_width=True,
            disabled=image is None,
        ):
            store.save(
                name=name,
                role=role,
                image_bytes=image.getvalue(),
                extension=Path(image.name).suffix,
                mime_type=image.type,
                visual_notes=notes,
            )
            st.success("Perfil visual salvo e ativado.")
            st.rerun()


def render_voice(package, package_path: Path) -> None:
    st.subheader("Voz e teleprompter")
    st.caption(
        "Grave no celular ou envie um áudio pronto. O ViralLab distribui a narração entre as cenas."
    )
    script = "\n\n".join(
        f"Cena {s.index}: {s.narration}" for s in package.scenes if s.narration
    )
    with st.expander("Abrir teleprompter", expanded=True):
        st.text_area("Roteiro para leitura", value=script, height=230, disabled=True)
    mode = st.radio(
        "Entrada de voz", ["Gravar agora", "Enviar arquivo"], horizontal=True
    )
    audio = (
        st.audio_input("Grave a narração completa", key="voice-recorder-v2")
        if mode == "Gravar agora"
        else st.file_uploader(
            "Envie MP3, WAV, M4A, AAC ou OGG",
            type=["mp3", "wav", "m4a", "aac", "ogg", "webm"],
            key="voice-upload-v2",
        )
    )
    if audio is not None:
        st.audio(audio.getvalue())
        if st.button(
            "Salvar e sincronizar voz", type="primary", use_container_width=True
        ):
            try:
                plan = save_narration(
                    package_path,
                    audio.getvalue(),
                    filename=getattr(audio, "name", "narration.wav"),
                )
                plan = update_voice_plan_with_scenes(
                    package_path,
                    package.scenes,
                    duration=plan.duration,
                    audio_file=plan.audio_file,
                )
                st.success(f"Voz salva. Duração: {plan.duration:.1f}s.")
                st.rerun()
            except VoiceError as exc:
                st.error(str(exc))
    plan = load_voice_plan(package_path)
    if plan:
        c1, c2, c3 = st.columns(3)
        c1.metric("Duração gravada", f"{plan.duration:.1f}s")
        c2.metric("Duração planejada", f"{package.brief.duration_seconds:.0f}s")
        c3.metric("Cenas sincronizadas", len(plan.scenes))
        delta = plan.duration - package.brief.duration_seconds
        if delta > 3:
            st.warning(
                f"A voz está {delta:.1f}s acima do planejado. O final pode ser cortado."
            )
        elif delta < -5:
            st.info(
                "A narração está mais curta; os criativos poderão permanecer mais tempo em tela."
            )
        for timing in plan.scenes:
            st.caption(
                f"Cena {timing.scene_index}: {timing.start:.1f}s–{timing.end:.1f}s · {timing.text}"
            )


def render_creatives(package, package_path: Path) -> None:
    library = AssetLibrary(package_path)
    approved_count = sum(1 for item in library.load() if item.status == "approved")
    c1, c2 = st.columns(2)
    c1.metric("Cenas", len(package.scenes))
    c2.metric("Aprovadas", f"{approved_count}/{len(package.scenes)}")
    visual_style = st.selectbox(
        "DNA visual",
        [
            "RP cinematográfico",
            "Clínico premium",
            "Editorial científico",
            "Humano documental",
            "Minimalista tecnológico",
        ],
    )
    for scene in package.scenes:
        records = library.for_scene(scene.index)
        approved = next((item for item in records if item.status == "approved"), None)
        prompt = build_scene_prompt(
            scene, theme=package.brief.theme, visual_style=visual_style
        )
        with st.container(border=True):
            st.markdown(
                f"**Cena {scene.index}** · {'✓ aprovada' if approved else 'aguardando'}"
            )
            st.caption(scene.visual_direction or scene.narration)
            edited_prompt = st.text_area(
                "Prompt", value=prompt, height=130, key=f"prompt-v2-{scene.index}"
            )
            g, u = st.columns(2)
            if g.button(
                "🎨 Gerar",
                key=f"gen-v2-{scene.index}",
                type="primary",
                use_container_width=True,
            ):
                try:
                    with st.spinner("Criando..."):
                        generate_scene_asset(package_path, scene, prompt=edited_prompt)
                    st.rerun()
                except (ImageGenerationError, ValueError) as exc:
                    st.error(str(exc))
            upload = u.file_uploader(
                "Upload",
                type=["mp4", "mov", "webm", "png", "jpg", "jpeg", "webp"],
                key=f"upload-v2-{scene.index}",
                label_visibility="collapsed",
            )
            if upload is not None and u.button(
                "Salvar upload", key=f"save-v2-{scene.index}", use_container_width=True
            ):
                record = library.add_bytes(
                    scene_index=scene.index,
                    data=upload.getvalue(),
                    extension=Path(upload.name).suffix or ".png",
                    source="upload",
                    provider="human",
                    prompt=edited_prompt,
                    metadata={"original_name": upload.name},
                )
                library.set_status(record.id, "approved")
                st.rerun()
            for record in reversed(library.for_scene(scene.index)):
                path = library.resolve(record)
                if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                    st.image(str(path), use_container_width=True)
                elif path.suffix.lower() in {".mp4", ".mov", ".webm"}:
                    st.video(str(path))
                a, b = st.columns(2)
                if a.button(
                    "⭐ Aprovar",
                    key=f"approve-v2-{record.id}",
                    disabled=record.status == "approved",
                    use_container_width=True,
                ):
                    library.set_status(record.id, "approved")
                    st.rerun()
                if b.button(
                    "Rejeitar",
                    key=f"reject-v2-{record.id}",
                    disabled=record.status == "rejected",
                    use_container_width=True,
                ):
                    library.set_status(record.id, "rejected")
                    st.rerun()


def render_output(package_path: Path) -> None:
    library = AssetLibrary(package_path)
    approved = [item for item in library.load() if item.status == "approved"]
    voice_plan = load_voice_plan(package_path)
    c1, c2 = st.columns(2)
    c1.metric("Criativos aprovados", len(approved))
    c2.metric("Voz", "Pronta" if voice_plan else "Não gravada")
    burn = st.checkbox("Legendas incorporadas", value=True)
    music = st.slider("Trilha (dB)", -40, -12, -25)
    voice_gain = st.slider("Voz (dB)", -6, 6, 0)
    if st.button(
        "Renderizar vídeo 2.0",
        type="primary",
        use_container_width=True,
        disabled=not approved,
    ):
        try:
            with st.spinner("Renderizando..."):
                video = (
                    render_video_with_voice(
                        package_path,
                        burn_captions=burn,
                        music_level_db=music,
                        narration_gain_db=voice_gain,
                    )
                    if voice_plan
                    else render_video(
                        package_path, burn_captions=burn, music_level_db=music
                    )
                )
            if video.exists():
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


initialize_state()
records = load_feedback(LEARNING_STORE)
summary = summarize_preferences(records)

with st.sidebar:
    st.markdown("## ◉ RP ViralLab 2.0")
    st.caption("Estúdio de conteúdo com memória")
    view = st.radio(
        "Navegação",
        ["Studio 2.0", "Analisar vídeo", "Aprendizado"],
        key="nav_view",
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("PROJETO ATUAL")
    st.code(st.session_state.project_id)
    if st.button("＋ Novo projeto", use_container_width=True):
        new_project()
        st.rerun()
    st.metric("Taxa de aprovação", f"{summary['approval_rate']}%")

if view == "Analisar vídeo":
    st.markdown(
        '<section class="hero"><div class="kicker">Engenharia reversa</div><h1>Analisar um vídeo</h1><p>Envie um arquivo ou cole uma URL pública.</p></section>',
        unsafe_allow_html=True,
    )
    upload_tab, url_tab = st.tabs(["📁 Upload", "🔗 URL"])
    with upload_tab:
        uploaded = st.file_uploader("Vídeo", type=["mp4", "mov", "m4v", "webm", "mkv"])
        if uploaded is not None:
            st.video(uploaded.getvalue())
            if st.button("Analisar vídeo →", type="primary", use_container_width=True):
                path = save_uploaded_file(
                    uploaded,
                    ANALYSIS_DIR
                    / f"{uuid.uuid4().hex[:10]}{Path(uploaded.name).suffix or '.mp4'}",
                )
                open_analysis(path, uploaded.name, "upload")
    with url_tab:
        url = st.text_input("URL pública")
        if st.button(
            "Importar URL →", disabled=not url.strip(), use_container_width=True
        ):
            try:
                imported = download_video_url(url, ANALYSIS_DIR / "urls")
                open_analysis(imported.path, imported.title, imported.source_url)
            except URLIngestError as exc:
                st.error(str(exc))
elif view == "Aprendizado":
    st.markdown(
        '<section class="hero"><div class="kicker">Memória editorial</div><h1>Aprendizado</h1><p>Registre o que deve ser reforçado nos próximos conteúdos.</p></section>',
        unsafe_allow_html=True,
    )
    package = st.session_state.package
    if package is None:
        st.warning("Crie um roteiro primeiro.")
    else:
        rating = st.slider("Qualidade", 1, 10, 8)
        approved = st.checkbox("Eu publicaria", value=True)
        notes = st.text_area("O que aprender?")
        if st.button("Salvar aprendizado", type="primary", use_container_width=True):
            save_feedback(
                FeedbackRecord(
                    project_id=st.session_state.project_id,
                    theme=package.brief.theme,
                    rating=rating,
                    approved=approved,
                    original_hook=package.hook,
                    preferred_hook=st.session_state.preferred_hook or package.hook,
                    notes=notes,
                    preferred_style="Studio 2.0",
                ),
                LEARNING_STORE,
            )
            st.success("Aprendizado salvo.")
else:
    st.markdown(
        '<section class="hero"><div class="kicker">Nova geração</div><h1>Studio de conteúdo 2.0</h1><p>Estratégia → roteiro → voz → perfil visual → criativos → render.</p></section>',
        unsafe_allow_html=True,
    )
    strategy_tab, script_tab, voice_tab, profile_tab, assets_tab, render_tab = st.tabs(
        [
            "01 Estratégia",
            "02 Roteiro",
            "03 Voz",
            "04 Perfil",
            "05 Criativos",
            "06 Render",
        ]
    )
    with strategy_tab:
        left, right = st.columns(2, gap="large")
        with left:
            theme = st.text_input("Tema", value="IA na fisioterapia")
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
            fmt = st.selectbox(
                "Formato",
                [
                    "professor_cinematico",
                    "lista_demonstrativa",
                    "narrativo",
                    "tutorial",
                    "case_clinico",
                ],
            )
            evidence = st.selectbox("Base", ["educacional", "cientifico", "opiniao"])
            provider_name = st.selectbox(
                "Motor de IA", ["auto", "gemini", "ollama", "local"]
            )
            cta = st.text_area(
                "CTA", value="Siga o Professor RP para aprender IA aplicada à saúde."
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
                    format=fmt,
                    cta=cta,
                    evidence_level=evidence,
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
                st.success("Roteiro criado. Continue na aba 02.")
            except Exception as exc:
                st.error(f"Não foi possível gerar: {exc}")
    package = st.session_state.package
    package_path = (
        Path(st.session_state.package_dir) if st.session_state.package_dir else None
    )
    with script_tab:
        if package is None:
            st.warning("Gere uma estratégia primeiro.")
        else:
            st.metric("Cenas", len(package.scenes))
            st.session_state.preferred_hook = st.text_area(
                "Gancho", value=st.session_state.preferred_hook or package.hook
            )
            st.markdown(f"**Tese:** {package.thesis}")
            render_scene_cards(package)
            st.download_button(
                "Baixar roteiro",
                json.dumps(package.to_dict(), ensure_ascii=False, indent=2),
                "video-package.json",
                "application/json",
                use_container_width=True,
            )
    with voice_tab:
        if package is None or package_path is None:
            st.warning("Gere o roteiro primeiro.")
        else:
            render_voice(package, package_path)
    with profile_tab:
        render_profile()
    with assets_tab:
        if package is None or package_path is None:
            st.warning("Gere o roteiro primeiro.")
        else:
            render_creatives(package, package_path)
    with render_tab:
        if package_path is None:
            st.warning("Crie o projeto primeiro.")
        else:
            render_output(package_path)

st.caption(
    "RP ViralLab Studio 2.0 · Conteúdo original, identidade persistente e revisão humana."
)
