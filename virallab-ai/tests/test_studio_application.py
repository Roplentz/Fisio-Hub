from __future__ import annotations

import sys
from types import ModuleType

from virallab.studio import application


def test_load_runtime_imports_missing_module(monkeypatch) -> None:
    imported = ModuleType("fake_runtime")
    calls: list[str] = []

    def fake_import(name: str) -> ModuleType:
        calls.append(name)
        return imported

    monkeypatch.setattr(application.importlib, "import_module", fake_import)
    monkeypatch.delitem(sys.modules, "fake_runtime", raising=False)

    result = application.load_runtime("fake_runtime")

    assert result is imported
    assert calls == ["fake_runtime"]


def test_load_runtime_reloads_existing_module(monkeypatch) -> None:
    existing = ModuleType("fake_runtime")
    reloaded = ModuleType("fake_runtime")
    calls: list[ModuleType] = []

    def fake_reload(module: ModuleType) -> ModuleType:
        calls.append(module)
        return reloaded

    monkeypatch.setitem(sys.modules, "fake_runtime", existing)
    monkeypatch.setattr(application.importlib, "reload", fake_reload)

    result = application.load_runtime("fake_runtime")

    assert result is reloaded
    assert calls == [existing]


def test_run_studio_uses_public_runtime_boundary(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(application, "load_runtime", lambda: calls.append("loaded"))

    application.run_studio()

    assert calls == ["loaded"]
