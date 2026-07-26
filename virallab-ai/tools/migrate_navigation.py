from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_V3 = ROOT / "app_v3.py"
APP = ROOT / "app.py"
NAV = ROOT / "src" / "virallab" / "streamlit_navigation.py"
TEST_ENTRYPOINT = ROOT / "tests" / "test_app_entrypoint.py"
TEST_NAVIGATION = ROOT / "tests" / "test_navigation_state.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: esperado 1 trecho, encontrado {count}")
    return text.replace(old, new, 1)


def migrate_app_v3() -> None:
    text = APP_V3.read_text(encoding="utf-8")

    text = replace_once(
        text,
        '        "studio_step": "analysis",\n',
        '        "studio_step": "analysis",\n        "step_selector": "analysis",\n',
        "estado inicial do seletor",
    )

    text = replace_once(
        text,
        "\ndef project_dir(project_id: str) -> Path:\n",
        "\ndef go_to_step(step: str) -> None:\n"
        "    if step not in STEPS:\n"
        "        raise ValueError(f\"Etapa inválida: {step}\")\n"
        "    st.session_state.studio_step = step\n"
        "    st.rerun()\n\n\n"
        "def sync_step_from_selector() -> None:\n"
        "    selected = st.session_state.get(\"step_selector\", \"analysis\")\n"
        "    st.session_state.studio_step = selected if selected in STEPS else \"analysis\"\n\n\n"
        "def project_dir(project_id: str) -> Path:\n",
        "helpers de navegação",
    )

    text = replace_once(
        text,
        '    st.session_state.studio_step = "analysis"\n    st.session_state.avatar_candidate = None\n',
        '    st.session_state.studio_step = "analysis"\n    st.session_state.step_selector = "analysis"\n    st.session_state.avatar_candidate = None\n',
        "reset do projeto",
    )

    pattern = re.compile(
        r'(?P<indent>\s*)st\.session_state\.studio_step = "(?P<step>analysis|strategy|script|avatar|voice|creatives|render|publication|learning)"\n(?P=indent)st\.rerun\(\)'
    )

    def repl(match: re.Match[str]) -> str:
        return f'{match.group("indent")}go_to_step("{match.group("step")}")'

    text, replacements = pattern.subn(repl, text)
    if replacements < 5:
        raise RuntimeError(f"transições substituídas insuficientes: {replacements}")

    old_selector = (
        'selected = st.selectbox("Etapa do projeto", options=list(STEPS), '
        'format_func=lambda key: STEPS[key], key="studio_step")'
    )
    new_selector = (
        'current_step = st.session_state.studio_step if st.session_state.studio_step in STEPS else "analysis"\n'
        'st.session_state.step_selector = current_step\n'
        'st.selectbox(\n'
        '    "Etapa do projeto",\n'
        '    options=list(STEPS),\n'
        '    format_func=lambda key: STEPS[key],\n'
        '    key="step_selector",\n'
        '    on_change=sync_step_from_selector,\n'
        ')\n'
        'selected = st.session_state.studio_step'
    )
    text = replace_once(text, old_selector, new_selector, "selectbox principal")

    if 'key="studio_step"' in text:
        raise RuntimeError("a chave lógica studio_step ainda está ligada a um widget")
    if "install_safe_step_selectbox" in text:
        raise RuntimeError("referência ao monkey-patch ainda presente")

    APP_V3.write_text(text, encoding="utf-8")


def migrate_entrypoint() -> None:
    APP.write_text(
        '"""Ponto de entrada estável do RP ViralLab Studio 3.0.\n\n'
        'O Streamlit Cloud executa este arquivo diretamente. A aplicação é carregada\n'
        'como módulo Python normal, sem ``exec()``, injeção de código ou monkey-patch.\n'
        '"""\n\n'
        'from __future__ import annotations\n\n'
        'import app_v3  # noqa: F401,E402\n',
        encoding="utf-8",
    )


def migrate_tests() -> None:
    entrypoint = TEST_ENTRYPOINT.read_text(encoding="utf-8")
    entrypoint = replace_once(
        entrypoint,
        '    assert "quality_patch" not in source\n',
        '    assert "quality_patch" not in source\n    assert "streamlit_navigation" not in source\n    assert "install_safe_step_selectbox" not in source\n',
        "teste do entrypoint",
    )
    TEST_ENTRYPOINT.write_text(entrypoint, encoding="utf-8")

    TEST_NAVIGATION.write_text(
        'from pathlib import Path\n\n\n'
        'def test_navigation_uses_distinct_logical_and_widget_keys() -> None:\n'
        '    app_path = Path(__file__).resolve().parents[1] / "app_v3.py"\n'
        '    source = app_path.read_text(encoding="utf-8")\n\n'
        '    assert \"\\\"studio_step\\\": \\\"analysis\\\"\" in source\n'
        '    assert \"\\\"step_selector\\\": \\\"analysis\\\"\" in source\n'
        '    assert \"key=\\\"step_selector\\\"\" in source\n'
        '    assert \"key=\\\"studio_step\\\"\" not in source\n'
        '    assert \"on_change=sync_step_from_selector\" in source\n'
        '    assert \"def go_to_step(step: str)\" in source\n'
        '    compile(source, str(app_path), "exec")\n',
        encoding="utf-8",
    )


def main() -> None:
    migrate_app_v3()
    migrate_entrypoint()
    migrate_tests()
    NAV.unlink(missing_ok=True)
    print("Migração de navegação concluída.")


if __name__ == "__main__":
    main()
