from __future__ import annotations

from pathlib import Path
from typing import Any

from .voice import VoiceError, load_voice_plan, save_narration, update_voice_plan_with_scenes
from .voice_engine import VoiceEngine, VoiceSettings


def render_voice(st: Any, package: Any, package_path: Path) -> None:
    st.subheader("Voz e teleprompter")
    st.caption("Gere gratuitamente com IA, grave no celular ou envie um áudio pronto.")
    script = "\n\n".join(
        f"Cena {scene.index}: {scene.narration}"
        for scene in package.scenes
        if scene.narration
    )
    with st.expander("Abrir teleprompter", expanded=True):
        st.text_area("Roteiro para leitura", value=script, height=230, disabled=True)

    mode = st.radio(
        "Entrada de voz",
        ["Gerar com IA", "Gravar agora", "Enviar arquivo"],
        horizontal=True,
    )

    if mode == "Gerar com IA":
        st.info("Motor inicial: Kokoro local e aberto. O áudio e o roteiro permanecem no projeto.")
        left, right = st.columns(2)
        voice = left.selectbox(
            "Voz",
            ["pm_alex", "pf_dora"],
            format_func=lambda value: {
                "pm_alex": "Alex · masculina",
                "pf_dora": "Dora · feminina",
            }[value],
        )
        speed = right.slider("Velocidade", 0.7, 1.5, 1.0, 0.05)
        with st.expander("Ajustes avançados", expanded=False):
            stability = st.slider(
                "Estabilidade",
                0.0,
                1.0,
                0.65,
                0.05,
                help="Mantém a narração mais consistente. Preparado para provedores futuros.",
            )
            similarity = st.slider(
                "Semelhança da voz",
                0.0,
                1.0,
                0.75,
                0.05,
                help="Parâmetro comum de plataformas de referência; será usado em clonagem autorizada.",
            )
            style = st.slider(
                "Expressividade",
                0.0,
                1.0,
                0.25,
                0.05,
            )
            speaker_boost = st.checkbox("Reforçar presença da voz", value=True)
        if st.button("Gerar narração com IA", type="primary", use_container_width=True):
            try:
                with st.spinner("Gerando e sincronizando a narração..."):
                    result = VoiceEngine().generate_project_voice(
                        package_path,
                        package.scenes,
                        settings=VoiceSettings(
                            voice=voice,
                            language="pt-BR",
                            speed=speed,
                            stability=stability,
                            similarity=similarity,
                            style=style,
                            speaker_boost=speaker_boost,
                        ),
                    )
                suffix = " · reutilizada do cache" if result.cache_hit else ""
                st.success(f"Narração gerada: {result.duration:.1f}s{suffix}.")
                st.rerun()
            except VoiceError as exc:
                st.error(str(exc))
    else:
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
            if st.button("Salvar e sincronizar voz", type="primary", use_container_width=True):
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
        audio_path = package_path / plan.audio_file
        if audio_path.exists():
            st.audio(str(audio_path))
            st.download_button(
                "Baixar narração WAV",
                audio_path.read_bytes(),
                "narracao-virallab.wav",
                "audio/wav",
                use_container_width=True,
            )
        c1, c2, c3 = st.columns(3)
        c1.metric("Voz", f"{plan.duration:.1f}s")
        c2.metric("Planejado", f"{package.brief.duration_seconds:.0f}s")
        c3.metric("Cenas", len(plan.scenes))
        if st.button("Continuar para Criativos →", type="primary", use_container_width=True):
            st.session_state.studio_step = "creatives"
            st.rerun()


__all__ = ["render_voice"]
