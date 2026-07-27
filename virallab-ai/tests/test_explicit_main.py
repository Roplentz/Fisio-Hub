from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_entrypoint_calls_explicit_main() -> None:
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert "from app_v3 import main" in source
    assert any(
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "main"
        for node in tree.body
    )
    assert "exec(" not in source
    assert "compile(" not in source


def test_app_v3_import_has_no_top_level_main_call() -> None:
    source = (ROOT / "app_v3.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "main"
        for node in tree.body
    )
    assert not any(
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "main"
        for node in tree.body
    )


def test_legacy_source_patch_is_removed() -> None:
    assert not (ROOT / "src" / "virallab" / "studio_source_patch.py").exists()
    assert (ROOT / "studio_runtime.py").exists()
