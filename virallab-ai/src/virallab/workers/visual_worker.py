from __future__ import annotations

from dataclasses import dataclass

from virallab.core import Moodboard, PromptBundle, VisualPlan, VisualScore
from virallab.models import Scene, VideoBrief


@dataclass
class VisualWorker:
    """Build a provider-neutral visual plan for one scripted scene."""

    brand_name: str = "Professor RP"

    def build(self, scene: Scene, brief: VideoBrief) -> VisualPlan:
        role = self._role(scene)
        palette = self._palette(brief.creative_style)
        main_visual = self._main_visual(scene)
        intent = (
            f"Comunicar {role} com clareza para {brief.audience}, preservando "
            f"o estilo {brief.creative_style} e o objetivo de {brief.objective}."
        )
        canonical = self._canonical_prompt(scene, brief, main_visual, palette)
        score = VisualScore(
            script_alignment=88,
            visual_impact=82,
            retention_potential=84 if scene.index <= 2 else 78,
            originality=76,
            brand_consistency=90,
            rationale="Plano inicial heurístico; deve ser recalculado após seleção ou geração dos assets.",
        )
        return VisualPlan(
            scene_id=f"scene_{scene.index:02d}",
            creative_intent=intent,
            main_visual=main_visual,
            setting=self._setting(scene),
            characters=[brief.avatar_name] if scene.scene_type == "avatar" else [],
            props=self._props(scene),
            broll=self._broll(scene, brief),
            icons=self._icons(scene),
            graphics=self._graphics(scene),
            palette=palette,
            typography=["Inter Bold", "Inter Regular"],
            shot=self._shot(scene),
            angle="eye level",
            camera_movement="slow push-in"
            if scene.scene_type in {"avatar", "proof"}
            else "static with subtle parallax",
            lighting="soft frontal key light with controlled contrast",
            transition="hard cut" if scene.index <= 2 else "short match cut",
            motion_notes="Animate only the key phrase; avoid decorative motion without narrative function.",
            prompts=PromptBundle(
                canonical=canonical,
                flux=canonical
                + ", editorial photography, vertical 9:16, natural skin, no text",
                imagen=canonical
                + ", premium educational campaign, vertical composition, no watermark",
                ideogram=canonical
                + ", reserve clean negative space for Portuguese headline",
                midjourney=canonical
                + " --ar 9:16 --style raw --no text, watermark, distorted hands",
                veo=self._video_prompt(scene, brief, main_visual),
                runway=self._video_prompt(scene, brief, main_visual),
                kling=self._video_prompt(scene, brief, main_visual),
                negative_prompt="low resolution, clutter, illegible text, distorted anatomy, generic stock-photo smile",
            ),
            moodboard=Moodboard(
                name=f"{self.brand_name} — {brief.creative_style}",
                concept="Autoridade científica humana, contemporânea e acessível.",
                palette=palette,
                typography=["Inter"],
                lighting="clean, soft and credible",
                texture="subtle glass and clinical-tech surfaces",
                composition="strong subject, negative space, one focal idea per frame",
                references=[
                    "editorial health technology",
                    "premium educational content",
                    "cinematic professor",
                ],
            ),
            score=score.normalized(),
            continuity_notes=[
                f"Manter a paleta principal {', '.join(palette[:3])}.",
                f"Preservar figurino, luz e aparência de {brief.avatar_name} entre cenas consecutivas.",
                "Usar no máximo uma metáfora visual principal por cena.",
            ],
        )

    @staticmethod
    def _role(scene: Scene) -> str:
        return {
            "avatar": "autoridade e conexão",
            "title_card": "impacto e retenção",
            "broll": "contexto e demonstração",
            "screen_capture": "prova funcional",
            "proof": "credibilidade e evidência",
        }.get(scene.scene_type, "clareza narrativa")

    @staticmethod
    def _palette(style: str) -> list[str]:
        if style == "viral":
            return ["#061018", "#45D6DC", "#F6F9FB", "#D8B96F"]
        if style == "conservadora":
            return ["#0B1B26", "#E7EEF2", "#91A6B4", "#2D6F7A"]
        return ["#061018", "#45D6DC", "#D8B96F", "#F6F9FB"]

    @staticmethod
    def _main_visual(scene: Scene) -> str:
        return scene.visual_direction or {
            "avatar": "Professor speaking directly to camera in a modern professional studio",
            "title_card": "Minimal high-impact typographic composition",
            "broll": "Contextual documentary-style supporting footage",
            "screen_capture": "Clean product screen demonstration with guided highlight",
            "proof": "Concrete evidence, result or before-and-after comparison",
        }.get(scene.scene_type, "Clear visual representation of the narration")

    @staticmethod
    def _setting(scene: Scene) -> str:
        return (
            "professional studio or real clinical-educational environment"
            if scene.scene_type == "avatar"
            else "context appropriate to the narration"
        )

    @staticmethod
    def _props(scene: Scene) -> list[str]:
        text = f"{scene.narration} {scene.visual_direction}".lower()
        candidates = {
            "computador": "notebook",
            "software": "software interface",
            "paciente": "clinical assessment context",
            "artigo": "scientific paper",
            "dados": "data dashboard",
            "celular": "smartphone",
        }
        return [value for key, value in candidates.items() if key in text]

    @staticmethod
    def _broll(scene: Scene, brief: VideoBrief) -> list[str]:
        suggestions = [scene.asset_query] if scene.asset_query else []
        suggestions.extend(
            [
                f"{brief.audience} em situação real de trabalho",
                f"detalhe visual que comprove: {scene.narration[:80]}",
            ]
        )
        return suggestions

    @staticmethod
    def _icons(scene: Scene) -> list[str]:
        text = scene.narration.lower()
        mapping = {
            "ia": "brain-circuit",
            "tempo": "clock",
            "dados": "chart",
            "dor": "body-pain",
            "resultado": "trend-up",
        }
        return [icon for term, icon in mapping.items() if term in text]

    @staticmethod
    def _graphics(scene: Scene) -> list[str]:
        return ["kinetic keyword"] if scene.on_screen_text else []

    @staticmethod
    def _shot(scene: Scene) -> str:
        return {
            "avatar": "medium close-up",
            "title_card": "full-frame graphic",
            "broll": "medium detail shot",
            "screen_capture": "full-screen capture with crop zoom",
            "proof": "close-up on evidence",
        }.get(scene.scene_type, "medium shot")

    @staticmethod
    def _canonical_prompt(
        scene: Scene, brief: VideoBrief, main_visual: str, palette: list[str]
    ) -> str:
        return (
            f"Create a vertical visual for scene {scene.index} of a short educational video about {brief.theme}. "
            f"Main visual: {main_visual}. Narration meaning: {scene.narration}. "
            f"Audience: {brief.audience}. Style: {brief.creative_style}, credible, human, premium, concise. "
            f"Palette: {', '.join(palette)}. Preserve visual continuity with the Professor RP brand."
        )

    @staticmethod
    def _video_prompt(scene: Scene, brief: VideoBrief, main_visual: str) -> str:
        return (
            f"Vertical 9:16 cinematic shot, 4 to 6 seconds. {main_visual}. "
            f"Support this narration: {scene.narration}. Controlled camera movement, realistic motion, "
            f"professional health-education tone for {brief.audience}, no embedded text, no watermark."
        )
