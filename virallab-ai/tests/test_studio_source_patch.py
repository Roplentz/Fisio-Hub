from virallab.studio_source_patch import install_voice_ui


def test_install_voice_ui_replaces_only_voice_block() -> None:
    source = (
        "before\n"
        "def render_voice(package, package_path: Path) -> None:\n"
        "    legacy()\n\n"
        "def render_creatives(package, package_path: Path) -> None:\n"
        "    creatives()\n"
    )
    patched = install_voice_ui(source)
    assert "legacy()" not in patched
    assert "render_voice_engine(st, package, package_path)" in patched
    assert "def render_creatives" in patched
