from __future__ import annotations

VOICE_START = "def render_voice(package, package_path: Path) -> None:\n"
VOICE_END = "\ndef render_creatives(package, package_path: Path) -> None:\n"
STEPS_MARKER = 'STEPS = {\n    "analysis": "01 · Analisar vídeo",'
ROUTER_MARKER = 'if selected == "analysis":\n    render_analysis()'
BOOT_MARKER = "\n\ninitialize_state()\n"


def _install_voice_step(source: str) -> str:
    start = source.find(VOICE_START)
    end = source.find(VOICE_END)
    if start < 0 or end < 0 or end <= start:
        raise RuntimeError("Não foi possível localizar a etapa de voz no Studio 3.0.")
    replacement = (
        "def render_voice(package, package_path: Path) -> None:\n"
        "    from virallab.voice_ui import render_voice as render_voice_engine\n"
        "    render_voice_engine(st, package, package_path)\n\n"
    )
    return source[:start] + replacement + source[end + 1 :]


def _install_autotest_step(source: str) -> str:
    if STEPS_MARKER not in source:
        raise RuntimeError("Não foi possível localizar as etapas do Studio 3.0.")
    source = source.replace(
        STEPS_MARKER,
        'STEPS = {\n    "autotest": "00 · Autoteste do sistema",\n    "analysis": "01 · Analisar vídeo",',
        1,
    )

    autotest_function = r'''


def render_system_autotest() -> None:
    """Diagnóstico inicial e atalho para preparar o fluxo completo de teste."""
    import importlib.util

    from virallab.voice_ui import apply_autotest_defaults

    st.subheader("🧪 Autoteste do sistema")
    st.caption("Verifique o ambiente e prepare automaticamente um projeto curto para testar o pipeline.")

    checks = {
        "Streamlit": importlib.util.find_spec("streamlit") is not None,
        "NumPy": importlib.util.find_spec("numpy") is not None,
        "SoundFile": importlib.util.find_spec("soundfile") is not None,
        "Kokoro": importlib.util.find_spec("kokoro") is not None,
        "FFmpeg": shutil.which("ffmpeg") is not None,
    }
    columns = st.columns(len(checks))
    for column, (label, passed) in zip(columns, checks.items()):
        column.metric(label, "OK" if passed else "Falhou")

    missing = [label for label, passed in checks.items() if not passed]
    if missing:
        st.error("Componentes ausentes: " + ", ".join(missing) + ".")
        st.caption("Após atualizar as dependências, reinicie o aplicativo no Streamlit Cloud.")
    else:
        st.success("Ambiente básico pronto para executar o autoteste completo.")

    with st.container(border=True):
        st.markdown("**Projeto automático de validação**")
        st.caption("Cria roteiro, cenas e parâmetros de voz de teste sem preencher campos manualmente.")
        if st.button(
            "Preparar autoteste completo →",
            type="primary",
            use_container_width=True,
            disabled=bool(missing),
            key="home_prepare_autotest",
        ):
            try:
                brief = VideoBrief(
                    theme="Como a inteligência artificial pode reduzir tarefas burocráticas na fisioterapia",
                    objective="educar",
                    audience="fisioterapeutas brasileiros",
                    duration_seconds=30,
                    format="professor_cinematico",
                    cta="Siga o Professor RP para aprender IA aplicada à saúde.",
                    evidence_level="educacional",
                )
                with st.spinner("Criando o projeto automático de teste..."):
                    package = generate_video_package(brief, provider=select_provider("local"))
                    out = project_dir(st.session_state.project_id)
                    if out.exists():
                        shutil.rmtree(out)
                    export_package(package, out)
                st.session_state.package = package
                st.session_state.package_dir = str(out)
                st.session_state.preferred_hook = package.hook
                apply_autotest_defaults(st.session_state)
                st.session_state.voice_input_mode = "Gerar com IA"
                st.session_state.studio_step = "voice"
                st.rerun()
            except Exception as exc:
                st.error(f"Não foi possível preparar o autoteste: {exc}")

    st.info("O teste de voz será executado na etapa 05 · Voz, já com os controles preenchidos.")
'''
    if BOOT_MARKER not in source:
        raise RuntimeError("Não foi possível localizar a inicialização do Studio 3.0.")
    source = source.replace(BOOT_MARKER, autotest_function + BOOT_MARKER, 1)

    if ROUTER_MARKER not in source:
        raise RuntimeError("Não foi possível localizar o roteador do Studio 3.0.")
    source = source.replace(
        ROUTER_MARKER,
        'if selected == "autotest":\n    render_system_autotest()\nelif selected == "analysis":\n    render_analysis()',
        1,
    )
    return source


def install_voice_ui(source: str) -> str:
    """Substitui somente a etapa de voz do Studio."""
    return _install_voice_step(source)


def install_studio_extensions(source: str) -> str:
    """Instala a tela de voz e o autoteste inicial sem duplicar o Studio."""
    return _install_autotest_step(install_voice_ui(source))


__all__ = ["install_studio_extensions", "install_voice_ui"]
