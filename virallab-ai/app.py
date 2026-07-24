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

st.set_page_config(page_title="ViralLab AI", page_icon="🎬", layout="wide")


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
    return [
        {
            "Cena": scene.index,
            "Tempo": f"{scene.start:.1f}–{scene.end:.1f}s",
            "Tipo": scene.scene_type,
            "Narração": scene.narration,
            "Texto na tela": scene.on_screen_text,
            "Direção visual": scene.visual_direction,
        }
        for scene in package.scenes
    ]


initialize_state()

st.title("🎬 ViralLab AI")
st.caption("MVP didático para criar, revisar, treinar e renderizar vídeos curtos.")

with st.sidebar:
    st.header("Como usar")
    st.markdown(
        """
1. Preencha o **Brief**.
2. Gere o roteiro.
3. Revise o hook e as cenas.
4. Envie avatar, imagens ou trilha.
5. Renderize o MP4.
6. Registre seu feedback para treinar o sistema.
        """
    )
    st.info("O treinamento deste MVP é transparente: suas escolhas ficam salvas em JSONL, sem alterar o modelo automaticamente.")
    if st.button("Novo projeto", use_container_width=True):
        st.session_state.project_id = uuid.uuid4().hex[:10]
        st.session_state.package = None
        st.session_state.package_dir = None
        st.session_state.preferred_hook = ""
        st.rerun()
    st.code(f"Projeto: {st.session_state.project_id}")

brief_tab, script_tab, assets_tab, render_tab, learn_tab = st.tabs(
    ["1. Brief", "2. Roteiro e cenas", "3. Assets", "4. Render", "5. Ensinar"]
)

with brief_tab:
    st.subheader("Defina o vídeo")
    left, right = st.columns(2)
    with left:
        theme = st.text_input("Tema", value="IA na fisioterapia")
        objective = st.selectbox(
            "Objetivo",
            ["ganhar seguidores qualificados", "educar", "gerar autoridade", "vender", "engajar"],
        )
        audience = st.text_input("Público", value="fisioterapeutas brasileiros")
        duration = st.slider("Duração", min_value=15, max_value=90, value=60, step=5)
    with right:
        video_format = st.selectbox(
            "Formato",
            ["professor_cinematico", "lista_demonstrativa", "narrativo", "tutorial", "case_clinico"],
        )
        provider_name = st.selectbox("IA", ["auto", "local", "gemini"])
        evidence_level = st.selectbox("Nível de evidência", ["educacional", "cientifico", "opiniao"])
        cta = st.text_input("Chamada para ação", value="Siga o Professor RP para aprender IA aplicada à saúde.")

    with st.expander("O que esta etapa ensina?"):
        st.write(
            "O brief controla a intenção do vídeo. Tema e público definem a linguagem; objetivo define a persuasão; "
            "formato define o ritmo; e nível de evidência ativa alertas de revisão científica."
        )

    if st.button("Gerar roteiro e storyboard", type="primary", use_container_width=True):
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
            st.success("Roteiro criado. Vá para a aba ‘Roteiro e cenas’.")
        except Exception as exc:
            st.error(f"Não foi possível gerar o pacote: {exc}")

with script_tab:
    package = st.session_state.package
    if package is None:
        st.warning("Gere um roteiro na aba Brief.")
    else:
        st.subheader("Revise antes de produzir")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.text_input("Hook original", value=package.hook, disabled=True)
            st.session_state.preferred_hook = st.text_area(
                "Sua versão preferida do hook",
                value=st.session_state.preferred_hook or package.hook,
                height=90,
            )
            st.markdown(f"**Tese:** {package.thesis}")
        with col2:
            st.metric("Cenas", len(package.scenes))
            st.metric("Duração", f"{package.brief.duration_seconds}s")
            st.metric("Provedor", package.metadata.get("script_provider", "—"))

        st.dataframe(package_scene_rows(package), use_container_width=True, hide_index=True)
        with st.expander("Entenda a lógica do storyboard"):
            st.write(
                "Cada linha é uma decisão de produção: tempo, função narrativa, fala, texto e visual. "
                "O ViralLab usa essa estrutura como fonte única para avatar, assets, legendas e renderização."
            )

        st.download_button(
            "Baixar pacote JSON",
            data=json.dumps(package.to_dict(), ensure_ascii=False, indent=2),
            file_name="video-package.json",
            mime="application/json",
        )

with assets_tab:
    package = st.session_state.package
    package_path = Path(st.session_state.package_dir) if st.session_state.package_dir else None
    if package is None or package_path is None:
        st.warning("Gere um roteiro antes de enviar assets.")
    else:
        st.subheader("Envie os materiais")
        st.write("Use o nome sugerido para que o renderizador associe o arquivo automaticamente.")
        assets_dir = package_path / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        for scene in package.scenes:
            if scene.scene_type == "avatar":
                suggested = f"avatar-scene-{scene.index:02d}.mp4"
            elif scene.scene_type == "screen_capture":
                suggested = f"screen-scene-{scene.index:02d}.mp4"
            elif scene.scene_type == "proof":
                suggested = f"proof-scene-{scene.index:02d}.jpg"
            else:
                continue
            upload = st.file_uploader(
                f"Cena {scene.index} — {scene.scene_type} · salvar como {suggested}",
                type=["mp4", "mov", "webm", "png", "jpg", "jpeg", "webp"],
                key=f"asset-{scene.index}",
            )
            if upload is not None:
                saved = save_uploaded_file(upload, assets_dir / suggested)
                st.success(f"Salvo: {saved.name}")

        music = st.file_uploader("Trilha opcional", type=["mp3", "wav", "m4a", "aac"])
        if music is not None:
            suffix = Path(music.name).suffix.lower() or ".mp3"
            saved = save_uploaded_file(music, assets_dir / f"music{suffix}")
            st.success(f"Trilha salva: {saved.name}")

        files = sorted(path.name for path in assets_dir.iterdir() if path.is_file())
        st.write("**Arquivos disponíveis:**", files or "Nenhum asset enviado.")

with render_tab:
    package_path = Path(st.session_state.package_dir) if st.session_state.package_dir else None
    if package_path is None:
        st.warning("Crie um projeto primeiro.")
    else:
        st.subheader("Gerar vídeo")
        c1, c2, c3 = st.columns(3)
        with c1:
            burn_captions = st.checkbox("Legendas incorporadas", value=True)
        with c2:
            music_level = st.slider("Volume da trilha (dB)", min_value=-40, max_value=-12, value=-25)
        with c3:
            dry_run = st.checkbox("Somente simular", value=False)

        with st.expander("O que acontece ao clicar em renderizar?"):
            st.write(
                "O FFmpeg cria um segmento por cena, preserva a voz do avatar, adiciona silêncio onde necessário, "
                "mistura a trilha, incorpora as legendas e produz video-final.mp4. Assets ausentes viram cartões temporários."
            )

        if st.button("Renderizar vídeo", type="primary", use_container_width=True):
            try:
                video = render_video(
                    package_path,
                    dry_run=dry_run,
                    burn_captions=burn_captions,
                    music_level_db=music_level,
                )
                if dry_run:
                    st.success("Simulação concluída. Veja generated/ffmpeg-commands.json.")
                elif video.exists():
                    st.success("Vídeo gerado.")
                    st.video(str(video))
                    st.download_button(
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
    st.subheader("Ensine suas preferências")
    st.write(
        "Este MVP não promete ‘treinar um modelo’ sozinho. Ele registra exemplos de preferência que depois poderão "
        "alimentar prompts, regras, avaliações e um futuro modelo personalizado."
    )

    if package is None:
        st.warning("Gere um roteiro para registrar feedback contextual.")
    else:
        rating = st.slider("Nota do roteiro", 1, 10, 8)
        approved = st.checkbox("Eu publicaria esta estrutura", value=True)
        preferred_style = st.selectbox(
            "Estilo que quero reforçar",
            ["Professor Cinemático", "Mais científico", "Mais direto", "Mais emocional", "Mais comercial"],
        )
        notes = st.text_area("O que deve melhorar no próximo vídeo?")

        if st.button("Salvar aprendizado", type="primary"):
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
            path = save_feedback(record, LEARNING_STORE)
            st.success(f"Aprendizado salvo em {path.relative_to(APP_ROOT)}")

    records = load_feedback(LEARNING_STORE)
    summary = summarize_preferences(records)
    m1, m2, m3 = st.columns(3)
    m1.metric("Feedbacks", summary["total_feedback"])
    m2.metric("Taxa de aprovação", f"{summary['approval_rate']}%")
    m3.metric("Nota média", summary["average_rating"])
    if summary["preferred_styles"]:
        st.write("**Estilos mais escolhidos:**", ", ".join(summary["preferred_styles"]))
    if records:
        st.dataframe(records[-20:][::-1], use_container_width=True, hide_index=True)
        st.download_button(
            "Baixar base de aprendizado",
            data="\n".join(json.dumps(item, ensure_ascii=False) for item in records),
            file_name="virallab-feedback.jsonl",
            mime="application/x-ndjson",
        )
