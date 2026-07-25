from types import SimpleNamespace

from virallab.creative_assets import build_scene_prompt


def test_build_scene_prompt_is_vertical_and_safe_for_text_overlay():
    scene = SimpleNamespace(
        scene_type="screen_capture",
        visual_direction="Interface de relatório clínico em um tablet",
        narration="A IA organiza a documentação sem substituir o fisioterapeuta.",
        on_screen_text="IA como assistente clínico",
    )

    prompt = build_scene_prompt(scene, theme="IA na fisioterapia")

    assert "9:16" in prompt
    assert "IA na fisioterapia" in prompt
    assert "não reproduzir marcas" in prompt
    assert "Não escrever esse texto na imagem" in prompt
    assert "sem logotipos" in prompt
