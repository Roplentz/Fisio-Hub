from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from virallab.asset_library import AssetLibrary
from virallab.image_provider import GeminiImageProvider, ImageGenerationError
from virallab.workers import VisualWorker

st.set_page_config(
    page_title="Asset Studio · RP ViralLab", page_icon="🖼️", layout="wide"
)

st.markdown(
    """
    <style>
    .block-container { max-width: 1450px; padding-top: 1.2rem; padding-bottom: 4rem; }
    .asset-hero { padding:30px; border-radius:26px; border:1px solid rgba(255,255,255,.10); background:linear-gradient(135deg,#132a38,#07151e); margin-bottom:22px; }
    .asset-kicker { color:#45d6dc; font-size:11px; font-weight:900; letter-spacing:.14em; text-transform:uppercase; }
    .asset-hero h1 { margin:.45rem 0; font-size:40px; color:white; }
    .asset-hero p { color:#a9bbc6; max-width:900px; }
    .status-approved { color:#78dfa5; font-weight:800; }
    .status-candidate { color:#d8b96f; font-weight:800; }
    .status-rejected { color:#ff8f8f; font-weight:800; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="asset-hero">
      <div class="asset-kicker">Sprint 4.4 · Asset Studio</div>
      <h1>Gere, compare e aprove imagens por cena</h1>
      <p>O Visual Brain cria a direção. O Asset Studio transforma essa direção em imagens reais, mantém alternativas e envia somente a versão aprovada para o render.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

package = st.session_state.get("package")
package_dir_value = st.session_state.get("package_dir")
if package is None or not package_dir_value:
    st.warning("Crie um roteiro no Studio antes de abrir o Asset Studio.")
    if st.button("Voltar ao Studio", type="primary"):
        st.session_state.workspace_view = "Studio"
        st.switch_page("app.py")
    st.stop()

project_dir = Path(package_dir_value)
library = AssetLibrary(project_dir)
worker = VisualWorker(brand_name=package.brief.avatar_name)
plans = {scene.index: worker.build(scene, package.brief) for scene in package.scenes}

all_records = library.load()
approved_count = sum(item.status == "approved" for item in all_records)
candidate_count = sum(item.status == "candidate" for item in all_records)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Cenas", len(package.scenes))
m2.metric("Candidatos", candidate_count)
m3.metric("Aprovados", approved_count)
m4.metric("Motor", os.getenv("VIRALLAB_IMAGE_MODEL", "gemini-3.1-flash-image"))

st.caption(
    "A geração por IA requer GEMINI_API_KEY. Uploads manuais continuam funcionando sem chave."
)

for scene in package.scenes:
    plan = plans[scene.index]
    title = scene.on_screen_text or scene.narration[:70] or f"Cena {scene.index}"
    with st.expander(f"Cena {scene.index:02d} · {title}", expanded=scene.index == 1):
        left, right = st.columns([1.05, 0.95], gap="large")
        with left:
            st.markdown("#### Direção visual")
            st.write(plan.main_visual)
            st.caption(plan.creative_intent)
            prompt = st.text_area(
                "Prompt da imagem",
                value=plan.prompts.imagen or plan.prompts.canonical,
                height=180,
                key=f"asset-prompt-{scene.index}",
            )
            c1, c2 = st.columns(2)
            image_size = c1.selectbox(
                "Resolução",
                ["512", "1K", "2K", "4K"],
                index=1,
                key=f"size-{scene.index}",
            )
            aspect_ratio = c2.selectbox(
                "Proporção", ["9:16", "4:5", "1:1", "16:9"], key=f"ratio-{scene.index}"
            )

            if st.button(
                "✨ Gerar com Gemini",
                type="primary",
                use_container_width=True,
                key=f"generate-{scene.index}",
            ):
                try:
                    with st.spinner("Gerando imagem..."):
                        generated = GeminiImageProvider().generate(
                            prompt,
                            aspect_ratio=aspect_ratio,
                            image_size=image_size,
                        )
                        record = library.add_bytes(
                            scene_index=scene.index,
                            data=generated.data,
                            extension=generated.extension,
                            source="ai_generation",
                            provider=generated.model,
                            prompt=prompt,
                            metadata={
                                "aspect_ratio": aspect_ratio,
                                "image_size": image_size,
                            },
                        )
                    st.success(f"Candidato criado: {record.id}")
                    st.rerun()
                except (ValueError, ImageGenerationError) as exc:
                    st.error(str(exc))

            upload = st.file_uploader(
                "Ou envie uma imagem",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"visual-upload-{scene.index}",
            )
            if upload is not None and st.button(
                "Adicionar upload como candidato",
                use_container_width=True,
                key=f"add-upload-{scene.index}",
            ):
                suffix = Path(upload.name).suffix or ".png"
                library.add_bytes(
                    scene_index=scene.index,
                    data=upload.getvalue(),
                    extension=suffix,
                    source="upload",
                    provider="human",
                    prompt=prompt,
                    metadata={"original_name": upload.name},
                )
                st.success("Imagem adicionada à biblioteca da cena.")
                st.rerun()

        with right:
            st.markdown("#### Continuidade")
            for note in plan.continuity_notes:
                st.write(f"• {note}")
            st.markdown("#### Paleta")
            palette_html = "".join(
                f'<span title="{color}" style="display:inline-block;width:38px;height:38px;border-radius:9px;background:{color};margin-right:8px;border:1px solid rgba(255,255,255,.18)"></span>'
                for color in plan.palette
            )
            st.markdown(palette_html, unsafe_allow_html=True)

        records = library.for_scene(scene.index)
        if not records:
            st.info("Nenhuma imagem candidata nesta cena.")
            continue

        st.divider()
        st.markdown("#### Candidatos")
        columns = st.columns(3)
        for position, record in enumerate(records):
            with columns[position % 3]:
                path = library.resolve(record)
                with st.container(border=True):
                    if path.exists():
                        st.image(str(path), use_container_width=True)
                    status_class = f"status-{record.status}"
                    status_label = {
                        "approved": "APROVADA",
                        "rejected": "REJEITADA",
                        "candidate": "CANDIDATA",
                    }.get(record.status, record.status.upper())
                    st.markdown(
                        f'<span class="{status_class}">{status_label}</span>',
                        unsafe_allow_html=True,
                    )
                    st.caption(f"{record.provider} · {record.id}")
                    if record.prompt:
                        with st.expander("Ver prompt"):
                            st.write(record.prompt)
                    a, b = st.columns(2)
                    if a.button(
                        "✓ Aprovar",
                        use_container_width=True,
                        key=f"approve-{record.id}",
                    ):
                        library.set_status(record.id, "approved")
                        st.success("Imagem aprovada e conectada ao render.")
                        st.rerun()
                    if b.button(
                        "✕ Rejeitar",
                        use_container_width=True,
                        key=f"reject-{record.id}",
                    ):
                        library.set_status(record.id, "rejected")
                        st.rerun()

st.divider()
left, middle, right = st.columns(3)
if left.button("← Visual Brain", use_container_width=True):
    st.switch_page("pages/02_Visual_Brain.py")
if middle.button("Voltar ao Studio", use_container_width=True):
    st.session_state.workspace_view = "Studio"
    st.switch_page("app.py")
with right:
    if approved_count:
        st.success(f"{approved_count} cena(s) já usam imagem aprovada no render.")
    else:
        st.info("Aprove uma imagem para conectá-la ao render-plan.json.")
