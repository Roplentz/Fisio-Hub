from __future__ import annotations

import argparse

from .generator import export_package, generate_video_package
from .models import VideoBrief


def main() -> None:
    parser = argparse.ArgumentParser(description="ViralLab AI video package generator")
    parser.add_argument("theme", help="Tema central do vídeo")
    parser.add_argument("--objective", default="ganhar seguidores qualificados")
    parser.add_argument("--audience", default="fisioterapeutas brasileiros")
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--format", default="professor_cinematico")
    parser.add_argument("--cta", default="Siga o perfil para aprender mais.")
    parser.add_argument("--output", default="output")
    args = parser.parse_args()

    brief = VideoBrief(
        theme=args.theme,
        objective=args.objective,
        audience=args.audience,
        duration_seconds=args.duration,
        format=args.format,
        cta=args.cta,
    )
    package = generate_video_package(brief)
    path = export_package(package, args.output)
    print(f"Pacote criado em: {path}")


if __name__ == "__main__":
    main()
