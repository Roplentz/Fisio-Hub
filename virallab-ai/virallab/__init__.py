"""Compatibility package for cloud deployments.

This shim exposes the source-layout package in ``src/virallab`` without
requiring an editable installation. It keeps Streamlit Community Cloud
deployments simple and reliable.
"""

from __future__ import annotations

from pathlib import Path

_SOURCE_PACKAGE = Path(__file__).resolve().parent.parent / "src" / "virallab"
__path__ = [str(_SOURCE_PACKAGE)]

# Keep the public version available from the source package when present.
_source_init = _SOURCE_PACKAGE / "__init__.py"
if _source_init.exists():
    namespace: dict[str, object] = {}
    exec(compile(_source_init.read_text(encoding="utf-8"), str(_source_init), "exec"), namespace)
    for name, value in namespace.items():
        if not name.startswith("__") or name in {"__version__"}:
            globals()[name] = value
