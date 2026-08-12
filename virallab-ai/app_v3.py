from __future__ import annotations

import html
import json
import shutil
import uuid
from pathlib import Path

import streamlit as st

from virallab.asset_library import AssetLibrary
from virallab.avatar_master import AvatarMasterStore, ImageGenerationError
from virallab.creative_assets import build_scene_prompt, generate_scene_asset
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
MAX_VIDEO_UPLOAD_BYTES = 250 * 1024 * 1024
for directory in (WORKSPACE, ANALYSIS_DIR, PROJECTS_DIR, LEARNING_STORE.parent):
    directory.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="RP ViralLab Studio 3.0",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root{--bg:#061018;--panel:#0d1d28;--line:rgba(255,255,255,.10);--text:#f6f9fb;--muted:#91a6b4;--cyan:#45d6dc;--gold:#d8b56d}
    .stApp{background:radial-gradient(circle at 85% 0%,rgba(69,214,220,.14),transparent 30%),var(--bg);color:var(--text)}
    .block-container{max-width:1160px;padding-top:.8rem;padding-bottom:5rem}
    [data-testid="stSidebar"]{background:linear-gradient(180deg,#08151e,#0b1b26);border-right:1px solid var(--line)}
    .hero{padding:30px;border:1px solid var(--line);border-radius:26px;background:linear-gradient(135deg,rgba(20,45,59,.98),rgba(8,24,34,.97));margin-bottom:18px}
    .hero h1{color:white;font-size:42px;line-height:1.08;letter-spacing:-2px;margin:.35rem 0}.hero p{color:#b3c4ce;margin:0;line-height:1.55}
    .kicker{color:var(--cyan);font-size:11px;font-weight:900;letter-spacing:.14em;text-transform:uppercase}
    .choice,.scene-card,.status-card{padding:18px;border-radius:18px;border:1px solid var(--line);background:rgba(13,29,40,.92);margin-bottom:10px}
    .choice h3{margin:.15rem 0 .35rem;color:white}.choice p{color:var(--muted);margin:0}
    .scene-head{display:flex;justify-content:space-between;gap:10px;color:white;font-weight:800}.scene-label{margin-top:9px;color:var(--muted);font-size:10px;font-weight:800;text-transform:uppercase}.scene-text{color:#d8e5ea;font-size:13px;margin-top:3px}
    .stButton>button,.stDownloadButton>button{min-height:50px;border-radius:13px;font-weight:800}
    div[data-baseweb="select"]>div{min-height:52px;border-radius:14px}
    @media(max-width:720px){.block-container{padding:.45rem .75rem 6rem}.hero{padding:18px;border-radius:19px}.hero h1{font-size:27px;letter-spacing:-1px}.hero p{font-size:14px}[data-testid="column"]{min-width:100%!important}.scene-head{display:block}h1,h2,h3{overflow-wrap:anywhere}}
    </style>
    """,
    unsafe_allow_html=True,
)

STEPS = {
    "autotest": "00 · Autoteste do sistema",
    "analysis": "01 · Analisar vídeo",
    "strategy": "02 · Estratégia",
    "script": "03 · Roteiro",
    "avatar": "04 · Avatar IA",
    "voice": "05 · Voz",
    "creatives": "06 · Criativos",
    "render": "07 · Render",
    "publication": "08 · Publicação",
    "learning": "09 · Aprendizado",
}


def initialize_state() -> None:
    defaults = {
        "project_id": uuid.uuid4().hex[:10],
        "package": None,
        "package_dir": None,
        "preferred_hook": "",
        "studio_step": "analysis",
        "pending_video_path": None,
        "pending_video_name": None,
        "pending_video_source": None,
        "avatar_candidate": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def project_dir(project_id: str) -> Path:
    return PROJECTS_DIR / project_id


def new_project() -> None:
    st.session_state.project_id = uuid.uuid4().hex[:10]
    st.session_state.package = None
    st.session_state.package_dir = None
    st.session_state.preferred_hook = ""
    st.session_state.studio_step = "analysis"
    st.session_state.avatar_candidate = None


def save_uploaded_file(uploaded_file, destination: Path) -> Path:
    """Persist uploaded media with a predictable safety limit."""
    size = getattr(uploaded_file, "size", None)
    if size is not None and int(size) > MAX_VIDEO_UPLOAD_BYTES:
        raise ValueError("O vídeo excede o limite de 250 MB.")
    payload = uploaded_file.getbuffer()
    if len(payload) > MAX_VIDEO_UPLOAD_BYTES:
        raise ValueError("O vídeo excede o limite de 250 MB.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_bytes(payload)
    temporary.replace(destination)
    return destination


def open_analysis(path: Path, name: str, source: str) -> None:
    st.session_state.pending_video_path = str(path)
    st.session_state.pending_video_name = name
    st.session_state.pending_video_source = source
    st.switch_page("pages/01_Analisar_Video.py")


def progress_value() -> float:
    index = list(STEPS).index(st.session_state.studio_step)
    return (index + 1) / len(STEPS)


def render_system_autotest() -> None:
    """Diagnóstico inicial e preparação de um projeto curto de validação."""
    import importlib.util

    checks = {
        "Streamlit": importlib.util.find_spec("streamlit") is not None,
        "NumPy": importlib.util.find_spec("numpy") is not None,
        "FFmpeg": shutil.which("ffmpeg") is not None,
        "FFprobe": shutil.which("ffprobe") is not None,
    }
    st.subheader("Autoteste do sistema")
    st.caption("Verifique o ambiente antes de iniciar um projeto completo.")
    columns = st.columns(len(checks))
    for column, (label, passed) in zip(columns, checks.items()):
        column.metric(label, "OK" if passed else "Ausente")
    missing = [label for label, passed in checks.items() if not passed]
    if missing:
        st.warning("Componentes ausentes: " + ", ".join(missing) + ".")
        return
    st.success("Ambiente básico pronto para o fluxo local.")
    with st.container(border=True):
        st.markdown("**Projeto de validação rápida**")
        st.caption("Cria um roteiro curto e abre diretamente a etapa de voz.")
        if st.button(
            "Preparar autoteste completo →", type="primary", use_container_width=True
        ):
            brief = VideoBrief(
                theme="Como a inteligência artificial pode reduzir tarefas burocráticas na fisioterapia",
                objective="educar",
                audience="fisioterapeutas brasileiros",
                duration_seconds=30,
                format="professor_cinematico",
                cta="Siga o Professor RP para aprender IA aplicada à saúde.",
                evidence_level="educacional",
            )
            try:
                with st.spinner("Criando o projeto de validação..."):
                    package = generate_video_package(
                        brief, provider=select_provider("local")
                    )
                    out = project_dir(st.session_state.project_id)
                    if out.exists():
                        shutil.rmtree(out)
                    export_package(package, out)
                st.session_state.package = package
                st.session_state.package_dir = str(out)
                st.session_state.preferred_hook = package.hook
                st.session_state.studio_step = "voice"
                st.rerun()
            except Exception as exc:
                st.error(f"Não foi possível preparar o autoteste: {exc}")


def render_analysis() -> None:
    st.subheader("Analisar vídeo")
    st.caption(
        "Use uma referência para entender estrutura, hook, ritmo e CTA — sem copiar literalmente."
    )
    upload_tab, url_tab = st.tabs(["📁 Enviar vídeo", "🔗 Importar URL"])
    with upload_tab:
        uploaded = st.file_uploader(
            "Vídeo", type=["mp4", "mov", "m4v", "webm", "mkv"], key="v3-analysis-upload"
        )
        if uploaded is not None:
            st.video(uploaded.getvalue())
            if st.button(
                "Analisar este vídeo →", type="primary", use_container_width=True
            ):
                try:
                    path = save_uploaded_file(
                        uploaded,
                        ANALYSIS_DIR
                        / f"{uuid.uuid4().hex[:10]}{Path(uploaded.name).suffix or '.mp4'}",
                    )
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    open_analysis(path, uploaded.name, "upload")
    with url_tab:
        url = st.text_input("URL pública", key="v3-analysis-url")
        if st.button(
            "Importar e analisar →", disabled=not url.strip(), use_container_width=True
        ):
            try:
                imported = download_video_url(url, ANALYSIS_DIR / "urls")
                open_analysis(imported.path, imported.title, imported.source_url)
            except URLIngestError as exc:
                st.error(str(exc))
    st.divider()
    if st.button("✨ Criar do zero, sem vídeo", use_container_width=True):
        st.session_state.studio_step = "strategy"
        st.rerun()


def render_strategy() -> None:
    st.subheader("Estratégia")
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
            st.session_state.studio_step = "script"
            st.rerun()
        except Exception as exc:
            st.error(f"Não foi possível gerar: {exc}")


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


def render_script(package) -> None:
    st.subheader("Roteiro")
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
    if st.button(
        "Continuar para Avatar IA →", type="primary", use_container_width=True
    ):
        st.session_state.studio_step = "avatar"
        st.rerun()


def render_avatar() -> None:
    store = AvatarMasterStore(WORKSPACE)
    profile = store.load()
    st.subheader("Avatar IA — Imagem Mestre")
    st.caption(
        "Envie apenas três fotos recentes. A Imagem Mestre será aprovada por você antes de ser usada nos criativos."
    )
    st.info(
        "Boa iluminação, fundo neutro, rosto visível, sem boné ou óculos escuros e expressão neutra."
    )

    if profile and profile.approved and profile.master_image_path:
        st.success(f"Imagem Mestre ativa · versão {profile.version}")
        st.image(
            profile.master_image_path,
            caption=f"{profile.name} · {profile.role}",
            use_container_width=True,
        )
        c1, c2 = st.columns(2)
        if c1.button("Substituir as três fotos", use_container_width=True):
            store.delete()
            st.session_state.avatar_candidate = None
            st.rerun()
        if c2.button("Continuar para Voz →", type="primary", use_container_width=True):
            st.session_state.studio_step = "voice"
            st.rerun()
        return

    name = st.text_input(
        "Nome do avatar", value=profile.name if profile else "Prof. Dr. Rodrigo Plentz"
    )
    role = st.text_input(
        "Papel", value=profile.role if profile else "Autor e especialista"
    )
    notes = st.text_area(
        "Diretrizes visuais",
        value=profile.visual_notes
        if profile
        else "Aparência profissional, segura e acolhedora; preservar rosto, cabelo e idade aparente.",
    )
    front, left, right = st.columns(3)
    front_photo = front.file_uploader(
        "Foto de frente", type=["png", "jpg", "jpeg", "webp"], key="avatar-front"
    )
    left_photo = left.file_uploader(
        "Lado esquerdo", type=["png", "jpg", "jpeg", "webp"], key="avatar-left"
    )
    right_photo = right.file_uploader(
        "Lado direito", type=["png", "jpg", "jpeg", "webp"], key="avatar-right"
    )
    consent = st.checkbox(
        "Confirmo que as fotos são minhas e autorizo seu uso para criar minha Imagem Mestre."
    )
    complete = all((front_photo, left_photo, right_photo)) and consent

    if st.button(
        "Salvar fotos e criar Imagem Mestre",
        type="primary",
        use_container_width=True,
        disabled=not complete,
    ):
        try:
            store.save_references(
                name=name,
                role=role,
                photos={
                    "front": (
                        front_photo.getvalue(),
                        front_photo.name,
                        front_photo.type,
                    ),
                    "left": (left_photo.getvalue(), left_photo.name, left_photo.type),
                    "right": (
                        right_photo.getvalue(),
                        right_photo.name,
                        right_photo.type,
                    ),
                },
                visual_notes=notes,
                consent_confirmed=consent,
            )
            with st.spinner("Criando a Imagem Mestre a partir dos três ângulos..."):
                candidate = store.generate_candidate()
            st.session_state.avatar_candidate = str(candidate)
            st.rerun()
        except (ValueError, ImageGenerationError) as exc:
            st.error(str(exc))

    candidate_path = (
        Path(st.session_state.avatar_candidate)
        if st.session_state.avatar_candidate
        else None
    )
    if candidate_path and candidate_path.exists():
        st.markdown("### Candidata à Imagem Mestre")
        st.image(str(candidate_path), use_container_width=True)
        approve, regenerate = st.columns(2)
        if approve.button(
            "✓ Aprovar Imagem Mestre", type="primary", use_container_width=True
        ):
            store.approve_candidate(candidate_path)
            st.session_state.avatar_candidate = None
            st.success("Imagem Mestre aprovada e ativada.")
            st.rerun()
        if regenerate.button("Gerar outra versão", use_container_width=True):
            try:
                with st.spinner("Gerando outra versão..."):
                    candidate = store.generate_candidate()
                st.session_state.avatar_candidate = str(candidate)
                st.rerun()
            except (ValueError, ImageGenerationError) as exc:
                st.error(str(exc))


def render_voice(package, package_path: Path) -> None:
    st.subheader("Voz e teleprompter")
    script = "\n\n".join(
        f"Cena {scene.index}: {scene.narration}"
        for scene in package.scenes
        if scene.narration
    )
    with st.expander("Abrir teleprompter", expanded=True):
        st.text_area("Roteiro para leitura", value=script, height=230, disabled=True)
    mode = st.radio(
        "Entrada de voz", ["Gravar agora", "Enviar arquivo"], horizontal=True
    )
    audio = (
        st.audio_input("Grave a narração completa", key="voice-recorder-v3")
        if mode == "Gravar agora"
        else st.file_uploader(
            "Envie MP3, WAV, M4A, AAC, OGG ou WebM",
            type=["mp3", "wav", "m4a", "aac", "ogg", "webm"],
            key="voice-upload-v3",
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
        c1.metric("Voz", f"{plan.duration:.1f}s")
        c2.metric("Planejado", f"{package.brief.duration_seconds:.0f}s")
        c3.metric("Cenas", len(plan.scenes))
        if st.button(
            "Continuar para Criativos →", type="primary", use_container_width=True
        ):
            st.session_state.studio_step = "creatives"
            st.rerun()


def render_creatives(package, package_path: Path) -> None:
    st.subheader("Criativos")
    avatar_store = AvatarMasterStore(WORKSPACE)
    avatar_profile = avatar_store.load()
    if avatar_profile and avatar_profile.approved:
        st.success(
            f"Avatar IA ativo: {avatar_profile.name} · versão {avatar_profile.version}"
        )
    else:
        st.warning(
            "Nenhuma Imagem Mestre aprovada. Cenas do autor usarão o modo genérico ou a referência antiga."
        )
    library = AssetLibrary(package_path)
    approved_count = sum(1 for item in library.load() if item.status == "approved")
    c1, c2 = st.columns(2)
    c1.metric("Cenas", len(package.scenes))
    c2.metric("Aprovadas", f"{approved_count}/{len(package.scenes)}")
    style = st.selectbox(
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
            scene,
            theme=package.brief.theme,
            visual_style=style,
            avatar_profile=avatar_profile,
        )
        with st.container(border=True):
            st.markdown(
                f"**Cena {scene.index}** · {'✓ aprovada' if approved else 'aguardando'}"
            )
            st.caption(scene.visual_direction or scene.narration)
            edited = st.text_area(
                "Direção da imagem",
                value=prompt,
                height=130,
                key=f"prompt-v3-{scene.index}",
            )
            generate_col, upload_col = st.columns(2)
            if generate_col.button(
                "🎨 Gerar variação",
                key=f"gen-v3-{scene.index}",
                type="primary",
                use_container_width=True,
            ):
                try:
                    with st.spinner("Criando..."):
                        generate_scene_asset(package_path, scene, prompt=edited)
                    st.rerun()
                except (ImageGenerationError, ValueError) as exc:
                    st.error(str(exc))
            upload = upload_col.file_uploader(
                "Enviar material",
                type=["mp4", "mov", "webm", "png", "jpg", "jpeg", "webp"],
                key=f"upload-v3-{scene.index}",
                label_visibility="collapsed",
            )
            if upload is not None and upload_col.button(
                "Salvar upload", key=f"save-v3-{scene.index}", use_container_width=True
            ):
                record = library.add_bytes(
                    scene_index=scene.index,
                    data=upload.getvalue(),
                    extension=Path(upload.name).suffix or ".png",
                    source="upload",
                    provider="human",
                    prompt=edited,
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
                    key=f"approve-v3-{record.id}",
                    disabled=record.status == "approved",
                    use_container_width=True,
                ):
                    library.set_status(record.id, "approved")
                    st.rerun()
                if b.button(
                    "Rejeitar",
                    key=f"reject-v3-{record.id}",
                    disabled=record.status == "rejected",
                    use_container_width=True,
                ):
                    library.set_status(record.id, "rejected")
                    st.rerun()


def render_output(package_path: Path) -> None:
    st.subheader("Render")
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
        "Renderizar vídeo",
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


def render_publication(package) -> None:
    st.subheader("Pacote de publicação")
    if package is None:
        st.warning("Crie o roteiro primeiro.")
        return
    title = st.text_input("Título", value=package.hook)
    caption = st.text_area(
        "Legenda", value=f"{package.thesis}\n\n{package.brief.cta}", height=180
    )
    hashtags = st.text_input(
        "Hashtags", value="#fisioterapia #inteligenciaartificial #inovacaoemsaude"
    )
    st.download_button(
        "Baixar pacote de publicação",
        json.dumps(
            {"title": title, "caption": caption, "hashtags": hashtags},
            ensure_ascii=False,
            indent=2,
        ),
        "publication-package.json",
        "application/json",
        use_container_width=True,
    )


def render_learning(package) -> None:
    st.subheader("Aprendizado")
    if package is None:
        st.warning("Crie um roteiro primeiro.")
        return
    rating = st.slider("Qualidade", 1, 10, 8)
    approved = st.checkbox("Eu publicaria", value=True)
    notes = st.text_area("O que o ViralLab deve aprender?")
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
                preferred_style="Studio 3.0",
            ),
            LEARNING_STORE,
        )
        st.success("Aprendizado salvo.")


initialize_state()
records = load_feedback(LEARNING_STORE)
summary = summarize_preferences(records)

with st.sidebar:
    st.markdown("## ◉ RP ViralLab 3.0")
    st.caption("Estúdio de conteúdo com memória")
    st.code(st.session_state.project_id)
    if st.button("＋ Novo projeto", use_container_width=True):
        new_project()
        st.rerun()
    st.metric("Taxa de aprovação", f"{summary['approval_rate']}%")

st.markdown(
    '<section class="hero"><div class="kicker">Estúdio inteligente de conteúdo</div><h1>RP ViralLab Studio 3.0</h1><p>Analisar vídeo → estratégia → roteiro → Avatar IA → voz → criativos → render → publicação → aprendizado.</p></section>',
    unsafe_allow_html=True,
)
st.progress(progress_value())

selected = st.selectbox(
    "Etapa do projeto",
    options=list(STEPS),
    format_func=lambda key: STEPS[key],
    key="studio_step",
)
package = st.session_state.package
package_path = (
    Path(st.session_state.package_dir) if st.session_state.package_dir else None
)

if selected == "autotest":
    render_system_autotest()
if selected == "analysis":
    render_analysis()
elif selected == "strategy":
    render_strategy()
elif selected == "script":
    render_script(package) if package else st.warning("Gere a estratégia primeiro.")
elif selected == "avatar":
    render_avatar()
elif selected == "voice":
    render_voice(package, package_path) if package and package_path else st.warning(
        "Gere o roteiro primeiro."
    )
elif selected == "creatives":
    render_creatives(package, package_path) if package and package_path else st.warning(
        "Gere o roteiro primeiro."
    )
elif selected == "render":
    render_output(package_path) if package_path else st.warning(
        "Crie o projeto primeiro."
    )
elif selected == "publication":
    render_publication(package)
else:
    render_learning(package)

st.caption(
    "RP ViralLab Studio 3.0 · Identidade autorizada, conteúdo original e revisão humana."
)
