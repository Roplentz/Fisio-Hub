from __future__ import annotations

from .models import Scene, VideoBrief


def professor_cinematico(brief: VideoBrief, hook: str, thesis: str) -> list[Scene]:
    """Formato 01: alterna avatar, telas de impacto, prova e contexto visual."""
    duration = max(30, brief.duration_seconds)
    blocks = [
        (0.00, 0.05, "title_card", hook, hook, "Fundo escuro, tipografia grande e contraste alto.", "Impacto sonoro curto; entrada rápida."),
        (0.05, 0.16, "avatar", thesis, "", f"{brief.avatar_name} em plano médio, olhando para a câmera.", "Zoom digital suave de 4%."),
        (0.16, 0.25, "broll", "A tecnologia acelera tarefas, mas não substitui contexto, responsabilidade e julgamento.", "TECNOLOGIA NÃO É JULGAMENTO", "B-roll de clínica, aula, artigo e computador.", "Cortes a cada 2 segundos."),
        (0.25, 0.43, "avatar", "Quem aprende a usar inteligência artificial consegue pesquisar, organizar ideias e produzir melhor em menos tempo.", "", f"{brief.avatar_name} com gestos discretos.", "Legendas cinéticas com palavras-chave."),
        (0.43, 0.57, "proof", "Mas decisões clínicas exigem conhecimento, ética e avaliação humana.", "A DECISÃO CONTINUA HUMANA", "Mostrar prontuário fictício sem dados pessoais, interação profissional-paciente e evidência científica.", "Desacelerar por um segundo antes da frase central."),
        (0.57, 0.76, "screen_capture", "Use a IA como copiloto: para comparar hipóteses, resumir estudos e preparar perguntas melhores.", "IA COMO COPILOTO", "Captura de tela limpa com três tarefas surgindo em sequência.", "Animação de lista; um item por vez."),
        (0.76, 0.90, "avatar", "O profissional do futuro não será o que entrega tudo à máquina. Será o que combina tecnologia com conhecimento humano.", "CONHECIMENTO + TECNOLOGIA", f"{brief.avatar_name} em enquadramento ligeiramente mais fechado.", "Pausa antes de 'conhecimento humano'."),
        (0.90, 1.00, "title_card", brief.cta, brief.cta.upper(), "Tela final com identidade visual RP/ViralLab.", "Final seco; manter texto por pelo menos 1,5 segundo."),
    ]

    scenes: list[Scene] = []
    for idx, (start_p, end_p, kind, narration, text, visual, edit) in enumerate(blocks, start=1):
        start = round(start_p * duration, 2)
        end = round(end_p * duration, 2)
        scenes.append(
            Scene(
                index=idx,
                start=start,
                end=end,
                scene_type=kind,  # type: ignore[arg-type]
                narration=narration,
                on_screen_text=text,
                visual_direction=visual,
                edit_direction=edit,
                asset_query=_asset_query(kind, brief.theme),
            )
        )
    return scenes


def _asset_query(kind: str, theme: str) -> str:
    if kind == "broll":
        return f"vertical cinematic b-roll about {theme}, healthcare education, no patient identification"
    if kind == "screen_capture":
        return f"clean mobile screen demonstration about {theme}"
    if kind == "proof":
        return f"scientific evidence healthcare professional reviewing research about {theme}"
    return ""


TEMPLATES = {"professor_cinematico": professor_cinematico}
