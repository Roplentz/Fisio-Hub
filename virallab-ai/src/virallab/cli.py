from __future__ import annotations

import argparse

from .generator import export_package, generate_video_package
from .models import VideoBrief
from .providers import select_provider
from .renderer import RenderError, render_video


def main() -> None:
    parser = argparse.ArgumentParser(description="ViralLab AI video package generator")
    parser.add_argument("theme", help="Tema central do vídeo")
    parser.add_argument("--objective", default="ganhar seguidores qualificados")
    parser.add_argument("--audience", default="fisioterapeutas brasileiros")
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--format", default="professor_cinematico")
    parser.add_argument("--cta", default="Siga o perfil para aprender mais.")
    parser.add_argument("--evidence-level", default="educacional")
    parser.add_argument("--provider", choices=["auto", "local", "gemini"], default="auto")
    parser.add_argument("--output", default="output")
    parser.add_argument(
        "--render",
        action="store_true",
        help="Renderiza video-final.mp4 com FFmpeg depois de gerar o pacote.",
    )
    parser.add_argument(
        "--render-dry-run",
        action="store_true",
        help="Gera os comandos FFmpeg sem executar a renderização.",
    )
    parser.add_argument("--ffmpeg-bin", default="ffmpeg")
    args = parser.parse_args()

    brief = VideoBrief(
        theme=args.theme,
        objective=args.objective,
        audience=args.audience,
        duration_seconds=args.duration,
        format=args.format,
        cta=args.cta,
        evidence_level=args.evidence_level,
    )
    provider = select_provider(args.provider)
    package = generate_video_package(brief, provider=provider)
    path = export_package(package, args.output)
    print(f"Pacote criado em: {path}")
    print(f"Provedor de roteiro: {package.metadata['script_provider']}")

    if args.render or args.render_dry_run:
        try:
            video_path = render_video(
                args.output,
                ffmpeg_bin=args.ffmpeg_bin,
                dry_run=args.render_dry_run,
            )
        except RenderError as exc:
            parser.error(str(exc))
        if args.render_dry_run:
            print(f"Comandos FFmpeg criados em: {args.output}/generated/ffmpeg-commands.json")
        else:
            print(f"Vídeo renderizado em: {video_path}")
    else:
        print("Use --render para gerar o primeiro vídeo vertical com FFmpeg.")


if __name__ == "__main__":
    main()
