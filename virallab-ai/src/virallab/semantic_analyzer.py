from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


class SemanticAnalysisError(RuntimeError):
    """Raised when speech transcription or semantic analysis cannot run."""


@dataclass(slots=True)
class TranscriptSegment:
    start: float
    end: float
    text: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class NarrativeBlock:
    label: str
    start: float
    end: float
    text: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class SemanticAnalysis:
    language: str
    transcript: str
    segments: list[TranscriptSegment]
    hook_text: str
    hook_score: int
    cta_text: str | None
    cta_score: int
    words_per_minute: int
    narrative_blocks: list[NarrativeBlock]
    summary: str
    strengths: list[str]
    improvements: list[str]
    available: bool = True
    warning: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def to_srt(self) -> str:
        lines: list[str] = []
        for index, segment in enumerate(self.segments, start=1):
            lines.extend(
                [
                    str(index),
                    f"{_srt_time(segment.start)} --> {_srt_time(segment.end)}",
                    segment.text.strip(),
                    "",
                ]
            )
        return ("\n".join(lines).strip() + "\n") if lines else ""


def unavailable_semantic_analysis(reason: str, language: str = "pt") -> SemanticAnalysis:
    """Create a valid partial result so visual/structural analysis can continue."""
    clean_reason = _normalize(reason)[:600]
    return SemanticAnalysis(
        language=language,
        transcript="",
        segments=[],
        hook_text="",
        hook_score=0,
        cta_text=None,
        cta_score=0,
        words_per_minute=0,
        narrative_blocks=[],
        summary="A análise verbal não ficou disponível; o diagnóstico continuou com estrutura e imagem.",
        strengths=[],
        improvements=["Reprocessar a transcrição quando o motor de áudio estiver disponível."],
        available=False,
        warning=clean_reason,
    )


def _srt_time(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _score_hook(text: str) -> int:
    lowered = text.lower()
    score = 42
    if "?" in text:
        score += 15
    if any(token in lowered for token in ("você", "voce", "sabia", "por que", "como", "erro", "nunca", "verdade", "atenção", "atencao")):
        score += 18
    if any(char.isdigit() for char in text):
        score += 8
    words = text.split()
    if 4 <= len(words) <= 28:
        score += 12
    if len(words) > 40:
        score -= 18
    return max(0, min(100, score))


def _find_cta(segments: list[TranscriptSegment]) -> tuple[str | None, int]:
    markers = (
        "siga", "compartilhe", "comente", "salve", "clique", "acesse", "mande", "envie",
        "inscreva", "saiba mais", "link", "me chama", "fale comigo", "baixe",
    )
    candidates = segments[-4:] if segments else []
    for segment in reversed(candidates):
        lowered = segment.text.lower()
        if any(marker in lowered for marker in markers):
            score = 75 + (10 if len(segment.text.split()) <= 22 else 0)
            return segment.text.strip(), min(100, score)
    return None, 25


def _build_blocks(segments: list[TranscriptSegment]) -> list[NarrativeBlock]:
    if not segments:
        return []
    total_end = max(segment.end for segment in segments)
    boundaries = [0.0, total_end * 0.16, total_end * 0.50, total_end * 0.82, total_end + 0.001]
    labels = ["Hook", "Problema e contexto", "Desenvolvimento", "Conclusão e CTA"]
    blocks: list[NarrativeBlock] = []
    for index, label in enumerate(labels):
        start, end = boundaries[index], boundaries[index + 1]
        selected = [item for item in segments if item.start < end and item.end >= start]
        text = _normalize(" ".join(item.text for item in selected))
        if text:
            blocks.append(NarrativeBlock(label, round(start, 2), round(min(end, total_end), 2), text))
    return blocks


def analyze_transcript(segments: Iterable[TranscriptSegment], language: str = "pt") -> SemanticAnalysis:
    items = list(segments)
    if not items:
        raise SemanticAnalysisError("Nenhuma fala foi reconhecida no vídeo. O arquivo pode estar sem áudio ou com volume muito baixo.")

    transcript = _normalize(" ".join(item.text for item in items))
    duration = max(item.end for item in items)
    word_count = len(transcript.split())
    wpm = round(word_count / max(duration / 60, 0.01))
    hook_segments = [item for item in items if item.start <= 5.0]
    hook_text = _normalize(" ".join(item.text for item in hook_segments)) or items[0].text.strip()
    hook_score = _score_hook(hook_text)
    cta_text, cta_score = _find_cta(items)
    blocks = _build_blocks(items)

    strengths: list[str] = []
    improvements: list[str] = []
    if hook_score >= 70:
        strengths.append("O início apresenta uma promessa, pergunta ou tensão verbal clara.")
    else:
        improvements.append("Tornar os primeiros cinco segundos mais específicos, provocativos e orientados ao público.")
    if 105 <= wpm <= 175:
        strengths.append("A velocidade da fala está em uma faixa adequada para conteúdo educativo curto.")
    elif wpm > 175:
        improvements.append("Reduzir a velocidade ou inserir pausas para melhorar a compreensão.")
    else:
        improvements.append("Aumentar a concisão ou o ritmo para evitar perda de atenção.")
    if cta_text:
        strengths.append("Foi identificada uma chamada para ação no encerramento.")
    else:
        improvements.append("Adicionar uma chamada para ação explícita e coerente com o objetivo do vídeo.")

    summary = (
        f"Foram reconhecidas {word_count} palavras em {duration:.1f}s, com ritmo aproximado de {wpm} palavras/minuto. "
        f"O hook verbal recebeu {hook_score}/100 e o CTA {cta_score}/100."
    )
    return SemanticAnalysis(
        language=language,
        transcript=transcript,
        segments=items,
        hook_text=hook_text,
        hook_score=hook_score,
        cta_text=cta_text,
        cta_score=cta_score,
        words_per_minute=wpm,
        narrative_blocks=blocks,
        summary=summary,
        strengths=strengths,
        improvements=improvements,
    )


def _audio_stream_status(path: Path) -> tuple[bool | None, str]:
    """Return whether an audio stream exists; None means ffprobe could not decide."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None, "FFprobe não está disponível para verificar a faixa de áudio."
    command = [
        ffprobe, "-v", "error", "-select_streams", "a:0", "-show_entries",
        "stream=codec_name,channels", "-of", "json", str(path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
        if result.returncode != 0:
            return None, _normalize(result.stderr)[:300] or "FFprobe não conseguiu ler o arquivo."
        payload = json.loads(result.stdout or "{}")
        streams = payload.get("streams", [])
        return bool(streams), "Faixa de áudio detectada." if streams else "O vídeo não possui faixa de áudio."
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return None, f"Não foi possível verificar o áudio: {exc}"


def _collect_segments(raw_segments: Iterable[Any]) -> list[TranscriptSegment]:
    segments: list[TranscriptSegment] = []
    try:
        for item in raw_segments:
            text = _normalize(getattr(item, "text", ""))
            if not text:
                continue
            start = float(getattr(item, "start", 0.0) or 0.0)
            end = float(getattr(item, "end", start) or start)
            segments.append(TranscriptSegment(round(start, 2), round(max(start, end), 2), text))
    except (IndexError, TypeError, ValueError, RuntimeError) as exc:
        raise SemanticAnalysisError(f"O Whisper interrompeu a leitura dos segmentos: {type(exc).__name__}: {exc}") from exc
    return segments


def _run_whisper(model: Any, video_path: Path, language: str | None, *, safe_mode: bool) -> tuple[list[TranscriptSegment], Any]:
    options: dict[str, Any] = {
        "language": language,
        "vad_filter": not safe_mode,
        "beam_size": 1 if safe_mode else 3,
        "condition_on_previous_text": False,
    }
    raw_segments, info = model.transcribe(str(video_path), **options)
    return _collect_segments(raw_segments), info


def transcribe_video(
    path: str | Path,
    model_size: str = "tiny",
    language: str | None = "pt",
    device: str = "cpu",
) -> SemanticAnalysis:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise SemanticAnalysisError(
            "O módulo faster-whisper não está instalado. Instale a dependência semântica do ViralLab."
        ) from exc

    video_path = Path(path)
    if not video_path.exists() or not video_path.is_file():
        raise SemanticAnalysisError("Arquivo de vídeo não encontrado.")
    if video_path.stat().st_size == 0:
        raise SemanticAnalysisError("O arquivo de vídeo está vazio.")

    has_audio, audio_detail = _audio_stream_status(video_path)
    if has_audio is False:
        raise SemanticAnalysisError(audio_detail)

    compute_type = "int8" if device == "cpu" else "float16"
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
    except Exception as exc:
        raise SemanticAnalysisError(f"Não foi possível iniciar o Whisper ({model_size}/{device}/{compute_type}): {exc}") from exc

    first_error = ""
    try:
        segments, info = _run_whisper(model, video_path, language, safe_mode=False)
    except Exception as exc:
        first_error = f"{type(exc).__name__}: {exc}"
        try:
            segments, info = _run_whisper(model, video_path, language, safe_mode=True)
        except Exception as retry_exc:
            detail = f"tentativa padrão: {first_error}; modo seguro: {type(retry_exc).__name__}: {retry_exc}"
            if has_audio is None:
                detail += f"; diagnóstico de áudio: {audio_detail}"
            raise SemanticAnalysisError(f"Falha ao transcrever o vídeo após nova tentativa. {detail}") from retry_exc

    detected_language = getattr(info, "language", None) or language or "desconhecido"
    try:
        result = analyze_transcript(segments, detected_language)
    except SemanticAnalysisError as exc:
        suffix = f" Diagnóstico de áudio: {audio_detail}" if has_audio is None else ""
        raise SemanticAnalysisError(f"{exc}{suffix}") from exc
    if first_error:
        result.warning = f"A transcrição foi concluída em modo seguro após falha inicial: {first_error[:240]}"
    return result
