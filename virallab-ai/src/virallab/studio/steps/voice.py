from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, MutableMapping

from virallab.voice import (
    VoiceError,
    load_voice_plan,
    save_narration,
    update_voice_plan_with_scenes,
)
from virallab.voice_engine import VoiceEngine, VoiceSettings
from virallab.voice_ui import apply_autotest_defaults, render_autotest_result


class VoiceAction(str, Enum):
    NONE = "none"
    RERUN = "rerun"
    GO_TO_CREATIVES = "go_to_creatives"


@dataclass(frozen=True)
class VoiceResult:
    """State changes requested by the voice step."""

    action: VoiceAction = VoiceAction.NONE
    last_generation: dict[str, float | bool] | None = None


def _build_script(package: Any) -> str:
    return "\n\n".join(
        f"Cena {scene.index}: {scene.narration}"
        for scene in package.scenes
        if scene.narration
    )


def render_voice(
    st: Any,
    package: Any,
    package_path: Path,
    *,
    state: MutableMapping[str, Any],
    engine_factory=VoiceEngine,
) -> VoiceResult:
    """Render voice controls without reading or mutating ``st.session_state``."""

    st.subheader("Voz e teleprompter")
    st.caption("Gere gratuitamente com IA, grave no celular ou envie um áudio pronto.")
    with st.expander("Abrir teleprompter", expanded=True):
        st.text_area(
            "Roteiro para leitura",
            value=_build_script(package),
            height=230,
            disabled=True,
        )

    mode = st.radio(
        "Entrada de voz",
        ["Gerar com IA", "Gravar agora", "Enviar arquivo"],
        horizontal=True,
        key="voice_input_mode",
    )

    if mode == "Gerar com IA":
        st.info("Motor inicial: Kokoro local e aberto. O áudio e o roteiro permanecem no projeto.")
        with st.container(border=True):
            auto_left, auto_right = st.columns([0.72, 0.28])
            auto_left.markdown("**Modo de teste rápido**")
            auto_left.caption(
                "Preenche os parâmetros recomendados e permite testar todo o fluxo com um clique."
            )
            if auto_right.button("Preencher autoteste", use_container_width=True):
                apply_autotest_defaults(state)
                return VoiceResult(action=VoiceAction.RERUN)
            autotest_enabled = st.checkbox(
                "Exibir validação automática dos artefatos",
                value=bool(state.get("voice_autotest_enabled", False)),
                key="voice_autotest_enabled",
            )

        left, right = st.columns(2)
        voice = left.selectbox(
            "Voz",
            ["pm_alex", "pf_dora"],
            format_func=lambda value: {
                "pm_alex": "Alex · masculina",
                "pf_dora": "Dora · feminina",
            }[value],
            key="voice_ai_voice",
        )
        speed = right.slider(
            "Velocidade",
            0.7,
            1.5,
            1.0,
            0.05,
            key="voice_ai_speed",
        )
        with st.expander("Ajustes avançados", expanded=autotest_enabled):
            stability = st.slider(
                "Estabilidade",
                0.0,
                1.0,
                0.65,
                0.05,
                help="Mantém a narração mais consistente. Preparado para provedores futuros.",
                key="voice_ai_stability",
            )
            similarity = st.slider(
                "Semelhança da voz",
                0.0,
                1.0,
                0.75,
                0.05,
                help="Parâmetro comum de plataformas de referência; será usado em clonagem autorizada.",
                key="voice_ai_similarity",
            )
            style = st.slider(
                "Expressividade",
                0.0,
                1.0,
                0.25,
                0.05,
                key="voice_ai_style",
            )
            speaker_boost = st.checkbox(
                "Reforçar presença da voz",
                value=True,
                key="voice_ai_speaker_boost",
            )

        settings = VoiceSettings(
            voice=voice,
            language="pt-BR",
            speed=speed,
            stability=stability,
            similarity=similarity,
            style=style,
            speaker_boost=speaker_boost,
        )
        generate_label = (
            "Executar autoteste completo"
            if autotest_enabled
            else "Gerar narração com IA"
        )
        if st.button(generate_label, type="primary", use_container_width=True):
            try:
                with st.spinner("Gerando e sincronizando a narração..."):
                    generation = engine_factory().generate_project_voice(
                        package_path,
                        package.scenes,
                        settings=settings,
                    )
                suffix = " · reutilizada do cache" if generation.cache_hit else ""
                st.success(f"Narração gerada: {generation.duration:.1f}s{suffix}.")
                return VoiceResult(
                    action=VoiceAction.RERUN,
                    last_generation={
                        "duration": generation.duration,
                        "cache_hit": generation.cache_hit,
                    },
                )
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
                    return VoiceResult(action=VoiceAction.RERUN)
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
        first, second, third = st.columns(3)
        first.metric("Voz", f"{plan.duration:.1f}s")
        second.metric("Planejado", f"{package.brief.duration_seconds:.0f}s")
        third.metric("Cenas", len(plan.scenes))
        if state.get("voice_autotest_enabled", False):
            render_autotest_result(st, package_path)
        if st.button("Continuar para Criativos →", type="primary", use_container_width=True):
            return VoiceResult(action=VoiceAction.GO_TO_CREATIVES)

    return VoiceResult()
