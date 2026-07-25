from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from virallab.workers import VisualWorker

st.set_page_config(
    page_title="Visual Brain · RP ViralLab", page_icon="🎨", layout="wide"
)

st.markdown(
    """
    <style>
    .block-container { max-width: 1420px; padding-top: 1.3rem; padding-bottom: 4rem; }
    .visual-hero { padding: 30px; border-radius: 26px; border: 1px solid rgba(255,255,255,.10); background: linear-gradient(135deg,#132a38,#081822); margin-bottom: 22px; }
    .visual-kicker { color:#45d6dc; font-size:11px; font-weight:900; letter-spacing:.14em; text-transform:uppercase; }
    .visual-hero h1 { margin:.45rem 0; font-size:40px; color:white; }
    .visual-hero p { color:#a9bbc6; max-width:850px; }
    .scene-label { color:#45d6dc; font-size:11px; font-weight:900; letter-spacing:.12em; }
    .prompt-box { padding:14px; border-radius:14px; border:1px solid rgba(255,255,255,.10); background:#091923; color:#c8d7df; font-size:12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="visual-hero">
      <div class="visual-kicker">Sprint 4.3 · Visual Brain</div>
      <h1>Direção visual inteligente por cena</h1>
      <p>Converta o roteiro em decisões de imagem, B-roll, enquadramento, iluminação, movimento, identidade e prompts prontos para diferentes motores de IA.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

package = st.session_state.get("package")
package_dir_value = st.session_state.get("package_dir")

if package is None:
    st.warning("Crie um roteiro no Studio antes de abrir o Visual Brain.")
    if st.button("Voltar ao Studio", type="primary"):
        st.session_state.workspace_view = "Studio"
        st.switch_page("app.py")
    st.stop()

worker = VisualWorker(brand_name=package.brief.avatar_name)
plans = [worker.build(scene, package.brief) for scene in package.scenes]

header_left, header_right = st.columns([1.6, 0.4])
with header_left:
    st.markdown(f"### {package.brief.theme}")
    st.caption(
        f"{len(plans)} cenas · Público: {package.brief.audience} · Objetivo: {package.brief.objective}"
    )
with header_right:
    payload = {
        "project_id": st.session_state.get("project_id"),
        "theme": package.brief.theme,
        "visual_plans": [plan.to_dict() for plan in plans],
    }
    st.download_button(
        "Baixar plano visual",
        json.dumps(payload, ensure_ascii=False, indent=2),
        file_name="visual-brain-plan.json",
        mime="application/json",
        use_container_width=True,
    )

if package_dir_value:
    package_dir = Path(package_dir_value)
    package_dir.mkdir(parents=True, exist_ok=True)
    visual_plan_path = package_dir / "visual-plan.json"
    visual_plan_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    st.caption(f"Plano sincronizado em {visual_plan_path.name}")

for scene, plan in zip(package.scenes, plans):
    title = scene.on_screen_text or scene.narration[:72] or f"Cena {scene.index}"
    with st.expander(f"Cena {scene.index:02d} · {title}", expanded=scene.index == 1):
        st.markdown(
            '<div class="scene-label">INTENÇÃO CRIATIVA</div>', unsafe_allow_html=True
        )
        st.write(plan.creative_intent)

        strategy_tab, direction_tab, assets_tab, prompts_tab, score_tab = st.tabs(
            ["Visão", "Direção", "Assets", "Prompts IA", "Score"]
        )

        with strategy_tab:
            left, right = st.columns([1.15, 0.85], gap="large")
            with left:
                st.markdown("#### Visual principal")
                st.write(plan.main_visual)
                st.markdown("#### Narração")
                st.write(scene.narration)
                if scene.on_screen_text:
                    st.markdown("#### Texto na tela")
                    st.info(scene.on_screen_text)
            with right:
                st.markdown("#### Moodboard")
                st.write(plan.moodboard.concept)
                st.caption(f"Composição: {plan.moodboard.composition}")
                st.caption(f"Iluminação: {plan.moodboard.lighting}")
                st.markdown("**Paleta**")
                palette_html = "".join(
                    f'<span title="{color}" style="display:inline-block;width:42px;height:42px;border-radius:10px;background:{color};margin-right:8px;border:1px solid rgba(255,255,255,.18)"></span>'
                    for color in plan.palette
                )
                st.markdown(palette_html, unsafe_allow_html=True)
                st.caption("Tipografia: " + ", ".join(plan.typography))

        with direction_tab:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Plano", plan.shot)
            c2.metric("Ângulo", plan.angle)
            c3.metric("Movimento", plan.camera_movement)
            c4.metric("Transição", plan.transition)
            st.markdown("#### Cenário e luz")
            st.write(f"**Ambiente:** {plan.setting}")
            st.write(f"**Iluminação:** {plan.lighting}")
            st.write(f"**Motion:** {plan.motion_notes}")
            if plan.continuity_notes:
                st.markdown("#### Continuidade")
                for note in plan.continuity_notes:
                    st.write(f"• {note}")

        with assets_tab:
            a, b, c = st.columns(3)
            with a:
                st.markdown("#### B-roll")
                for item in plan.broll:
                    st.write(f"• {item}")
            with b:
                st.markdown("#### Ícones")
                if plan.icons:
                    for item in plan.icons:
                        st.write(f"• {item}")
                else:
                    st.caption("Nenhum ícone obrigatório.")
            with c:
                st.markdown("#### Gráficos e objetos")
                for item in [*plan.graphics, *plan.props]:
                    st.write(f"• {item}")
                if not plan.graphics and not plan.props:
                    st.caption("Manter a cena limpa e centrada na mensagem.")

        with prompts_tab:
            provider = st.selectbox(
                "Motor",
                [
                    "canonical",
                    "flux",
                    "imagen",
                    "ideogram",
                    "midjourney",
                    "veo",
                    "runway",
                    "kling",
                ],
                key=f"prompt-provider-{scene.index}",
            )
            prompt = getattr(plan.prompts, provider)
            st.code(prompt, language=None, wrap_lines=True)
            st.caption("Prompt negativo")
            st.code(plan.prompts.negative_prompt, language=None, wrap_lines=True)

        with score_tab:
            s1, s2, s3, s4, s5 = st.columns(5)
            s1.metric("Roteiro", plan.score.script_alignment)
            s2.metric("Impacto", plan.score.visual_impact)
            s3.metric("Retenção", plan.score.retention_potential)
            s4.metric("Originalidade", plan.score.originality)
            s5.metric("Marca", plan.score.brand_consistency)
            st.info(plan.score.rationale)

st.divider()
left, right = st.columns(2)
with left:
    if st.button("← Voltar ao Studio", use_container_width=True):
        st.session_state.workspace_view = "Studio"
        st.switch_page("app.py")
with right:
    st.success(
        "Visual Brain ativo. O próximo módulo conectará geração e seleção real de imagens por cena."
    )
