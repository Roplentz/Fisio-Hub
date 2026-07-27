from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from virallab.studio.steps.analysis import AnalysisAction, render_analysis
from virallab.studio.steps.strategy import StrategyResult, render_strategy


class Context:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class Uploaded:
    name = "referencia.mp4"

    def getbuffer(self):
        return memoryview(b"video")

    def getvalue(self):
        return b"video"


class AnalysisUI:
    def __init__(self, *, clicked: str, uploaded=None, url: str = ""):
        self.clicked = clicked
        self.uploaded = uploaded
        self.url = url
        self.errors: list[str] = []

    def subheader(self, *_args, **_kwargs): pass
    def caption(self, *_args, **_kwargs): pass
    def tabs(self, _labels): return Context(), Context()
    def file_uploader(self, *_args, **_kwargs): return self.uploaded
    def video(self, *_args, **_kwargs): pass
    def text_input(self, *_args, **_kwargs): return self.url
    def divider(self): pass
    def error(self, message): self.errors.append(str(message))

    def button(self, label, **_kwargs):
        return label == self.clicked


def test_analysis_upload_is_saved_and_forwarded(tmp_path: Path) -> None:
    ui = AnalysisUI(clicked="Analisar este vídeo →", uploaded=Uploaded())
    received = []

    result = render_analysis(
        ui,
        tmp_path,
        lambda path, name, source: received.append((path, name, source)),
        id_factory=lambda: "abc123",
    )

    assert result is None
    assert (tmp_path / "abc123.mp4").read_bytes() == b"video"
    assert received == [(tmp_path / "abc123.mp4", "referencia.mp4", "upload")]


def test_analysis_url_uses_injected_downloader(tmp_path: Path) -> None:
    ui = AnalysisUI(clicked="Importar e analisar →", url="https://example.test/video")
    received = []
    imported = SimpleNamespace(path=tmp_path / "url.mp4", title="Título", source_url="https://example.test/video")

    result = render_analysis(
        ui,
        tmp_path,
        lambda path, name, source: received.append((path, name, source)),
        downloader=lambda url, destination: imported,
    )

    assert result is None
    assert received == [(imported.path, "Título", imported.source_url)]


def test_analysis_create_from_scratch_returns_navigation_intent(tmp_path: Path) -> None:
    ui = AnalysisUI(clicked="✨ Criar do zero, sem vídeo")

    result = render_analysis(ui, tmp_path, lambda *_args: None)

    assert result is AnalysisAction.CREATE_FROM_SCRATCH


class StrategyUI:
    def __init__(self, *, generate: bool = True):
        self.generate = generate
        self.errors: list[str] = []

    def subheader(self, *_args, **_kwargs): pass
    def columns(self, *_args, **_kwargs): return Context(), Context()

    def text_input(self, label, **kwargs):
        return {"Tema": "IA na fisioterapia", "Público": "fisioterapeutas"}[label]

    def selectbox(self, label, _options):
        return {
            "Objetivo": "educar",
            "Formato": "tutorial",
            "Base": "cientifico",
            "Motor de IA": "local",
        }[label]

    def slider(self, *_args, **_kwargs): return 60
    def text_area(self, *_args, **_kwargs): return "Siga o perfil."
    def button(self, *_args, **_kwargs): return self.generate
    def error(self, message): self.errors.append(str(message))


def test_strategy_returns_package_without_mutating_session(tmp_path: Path) -> None:
    ui = StrategyUI()
    provider = object()
    package = SimpleNamespace(hook="Gancho")
    calls = {}

    result = render_strategy(
        ui,
        project_id="projeto-1",
        project_dir_factory=lambda project_id: tmp_path / project_id,
        provider_selector=lambda name: calls.setdefault("provider", (name, provider))[1],
        package_generator=lambda brief, provider: calls.setdefault("generated", (brief, provider)) and package,
        package_exporter=lambda generated, destination: calls.setdefault("exported", (generated, destination)),
    )

    assert result == StrategyResult(package=package, output_directory=tmp_path / "projeto-1")
    assert calls["provider"] == ("local", provider)
    assert calls["generated"][1] is provider
    assert calls["exported"] == (package, tmp_path / "projeto-1")
    assert not hasattr(ui, "session_state")


def test_strategy_reports_generation_failure(tmp_path: Path) -> None:
    ui = StrategyUI()

    result = render_strategy(
        ui,
        project_id="projeto-1",
        project_dir_factory=lambda project_id: tmp_path / project_id,
        package_generator=lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("falha controlada")),
    )

    assert result is None
    assert ui.errors == ["Não foi possível gerar: falha controlada"]
