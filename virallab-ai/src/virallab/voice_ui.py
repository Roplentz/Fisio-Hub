from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .voice import VoiceError, load_voice_plan, save_narration, update_voice_plan_with_scenes
from .voice_engine import VoiceEngine, VoiceSettings

AUTOTEST_KEYS = {
    "voice_ai_voice": "pm_alex",
    "voice_ai_speed": 1.0,
    "voice_ai_stability": 0.65,
    "voice_ai_similarity": 0.75,
    "voice_ai_style": 0.25,
    "voice_ai_speaker_boost": True,
}


def apply_autotest_defaults(state: Any) -> None:
    """Preenche os controles de voz com o preset seguro do autoteste."""
    for key, value in AUTOTEST_KEYS.items():
        state[key] = value
    state["voice_autotest_enabled"] = True


def autotest_report(package_path: Path) -> dict[str, bool]:
    """Valida os artefatos mínimos produzidos pelo Voice Engine."""
    plan = load_voice_plan(package_path)
    metadata_path = package_path / "voice-generation.json"
    narration = package_path / "assets" / "narration.wav"
    metadata_valid = False
    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata_valid = bool(metadata.get("provider") and metadata.get("cache_key"))
        except (json.JSONDecodeError, OSError):
            metadata_valid = False
    return {
        "audio": narration.exists() and narration.stat().st_size > 0,
        "voice_plan": bool(plan and plan.duration >= 0 and plan.audio_file),
        "metadata": metadata_valid,
        "scenes": bool(plan and plan.scenes),
    }


def render_autotest_result(st: Any, package_path: Path) -> None:
    report = autotest_report(package_path)
    if not any(report.values()):
        return
    labels = {
        "audio": "Arquivo WAV",
        "voice_plan": "Plano de voz",
        "metadata": "Metadados e cache",
        "scenes": "Sincronização das cenas",
    }
    st.markdown("#### Resultado do autoteste")
    columns = st.columns(4)
    for column, (key, passed) in zip(columns, report.items(), strict=True):
        column.metric(labels[key], "OK" if passed else "Falhou")
    if all(report.values()):
        st.success("Autoteste concluído: geração, cache, metadados e sincronização estão prontos.")
    else:
        failed = ", ".join(labels[key] for key, passed in report.items() if not passed)
        st.warning(f"Autoteste parcial. Verifique: {failed}.")


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
        key="voice_input_mode",
    )

    if mode == "Gerar com IA":
        st.info("Motor inicial: Kokoro local e aberto. O áudio e o roteiro permanecem no projeto.")

        with st.container(border=True):
            auto_left, auto_right = st.columns([0.72, 0.28])
            auto_left.markdown("**Modo de teste rápido**")
            auto_left.caption("Preenche os parâmetros recomendados e permite testar todo o fluxo com um clique.")
            if auto_right.button("Preencher autoteste", use_container_width=True):
                apply_autotest_defaults(st.session_state)
                st.rerun()
            autotest_enabled = st.checkbox(
                "Exibir validação automática dos artefatos",
                value=bool(st.session_state.get("voice_autotest_enabled", False)),
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
        generate_label = "Executar autoteste completo" if autotest_enabled else "Gerar narração com IA"
        if st.button(generate_label, type="primary", use_container_width=True):
            try:
                with st.spinner("Gerando e sincronizando a narração..."):
                    result = VoiceEngine().generate_project_voice(
                        package_path,
                        package.scenes,
                        settings=settings,
                    )
                suffix = " · reutilizada do cache" if result.cache_hit else ""
                st.session_state["voice_last_generation"] = {
                    "duration": result.duration,
                    "cache_hit": result.cache_hit,
                }
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
        if st.session_state.get("voice_autotest_enabled", False):
            render_autotest_result(st, package_path)
        if st.button("Continuar para Criativos →", type="primary", use_container_width=True):
            st.session_state.studio_step = "creatives"
            st.rerun()


__all__ = [
    "AUTOTEST_KEYS",
    "apply_autotest_defaults",
    "autotest_report",
    "render_voice",
]
