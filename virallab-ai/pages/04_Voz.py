from __future__ import annotations

from pathlib import Path

import streamlit as st

from virallab.renderer import RenderError
from virallab.voice import (
    VoiceError,
    load_voice_plan,
    narration_path,
    save_narration,
    update_voice_plan_with_scenes,
)
from virallab.voice_renderer import render_video_with_voice

st.set_page_config(page_title="Voz · ViralLab", page_icon="🎙️", layout="wide")

st.title("🎙️ Voz do projeto")
st.caption(
    "Grave a narração diretamente no celular ou envie um áudio. O ViralLab alinha a voz ao roteiro e usa a gravação no vídeo final."
)

package = st.session_state.get("package")
package_dir_value = st.session_state.get("package_dir")
package_dir = Path(package_dir_value) if package_dir_value else None

if package is None or package_dir is None:
    st.warning("Crie um roteiro no Studio antes de gravar a narração.")
    st.stop()

script_text = "\n\n".join(
    f"Cena {scene.index}\n{scene.narration}"
    for scene in package.scenes
    if scene.narration
)

with st.expander("📜 Teleprompter", expanded=True):
    st.text_area(
        "Roteiro para leitura",
        value=script_text,
        height=320,
        disabled=True,
        label_visibility="collapsed",
    )
    st.caption("Leia em ritmo natural e faça uma pausa curta entre as cenas.")

record_tab, upload_tab = st.tabs(["🎙️ Gravar agora", "📁 Enviar áudio"])

new_audio = None
new_name = "narration.wav"
with record_tab:
    recorded = st.audio_input("Grave o roteiro completo")
    if recorded is not None:
        new_audio = recorded.getvalue()
        new_name = recorded.name or "narration.wav"
        st.audio(new_audio)

with upload_tab:
    uploaded = st.file_uploader(
        "Envie uma gravação pronta",
        type=["wav", "mp3", "m4a", "aac", "ogg", "webm"],
    )
    if uploaded is not None:
        new_audio = uploaded.getvalue()
        new_name = uploaded.name
        st.audio(new_audio)

if new_audio is not None and st.button(
    "Salvar narração e sincronizar →", type="primary", use_container_width=True
):
    try:
        initial = save_narration(package_dir, new_audio, filename=new_name)
        plan = update_voice_plan_with_scenes(
            package_dir,
            package.scenes,
            duration=initial.duration,
            audio_file=initial.audio_file,
        )
        st.success("Narração salva e distribuída entre as cenas.")
        st.session_state["voice_saved"] = True
        st.rerun()
    except VoiceError as exc:
        st.error(str(exc))

plan = load_voice_plan(package_dir)
audio_path = narration_path(package_dir)
if plan and audio_path:
    st.divider()
    st.subheader("Narração ativa")
    c1, c2, c3 = st.columns(3)
    c1.metric("Duração", f"{plan.duration:.1f} s" if plan.duration else "Não medida")
    c2.metric("Cenas sincronizadas", f"{len(plan.scenes)}/{len(package.scenes)}")
    expected = float(getattr(package.brief, "duration_seconds", 0) or 0)
    difference = plan.duration - expected if plan.duration and expected else 0.0
    c3.metric("Diferença do planejado", f"{difference:+.1f} s" if expected else "—")
    st.audio(str(audio_path))

    if expected and abs(difference) > 4:
        if difference > 0:
            st.warning(
                "A gravação está mais longa que o vídeo planejado. O final pode ser cortado; reduza pausas, regrave ou aumente a duração do projeto."
            )
        else:
            st.info(
                "A gravação está mais curta que o vídeo planejado. O vídeo terminará quando a narração acabar."
            )

    st.markdown("### Alinhamento estimado por cena")
    for item in plan.scenes:
        with st.container(border=True):
            st.markdown(
                f"**Cena {item.scene_index} · {item.start:.1f}–{item.end:.1f}s**"
            )
            st.write(item.text or "Sem narração definida.")

    st.divider()
    st.subheader("Renderizar com sua voz")
    burn_captions = st.checkbox("Legendas incorporadas", value=True)
    music_level = st.slider("Trilha de fundo (dB)", -40, -12, -25)
    narration_gain = st.slider("Volume da voz (dB)", -6, 6, 0)
    if st.button(
        "🎬 Gerar vídeo com narração", type="primary", use_container_width=True
    ):
        try:
            with st.spinner("Renderizando vídeo e aplicando sua voz..."):
                video = render_video_with_voice(
                    package_dir,
                    burn_captions=burn_captions,
                    music_level_db=music_level,
                    narration_gain_db=narration_gain,
                )
            st.success("Vídeo com narração concluído.")
            st.video(str(video))
            st.download_button(
                "Baixar vídeo final",
                video.read_bytes(),
                file_name="video-final-com-voz.mp4",
                mime="video/mp4",
                use_container_width=True,
            )
        except (RenderError, VoiceError) as exc:
            st.error(str(exc))
else:
    st.info("Grave ou envie o primeiro áudio para ativar a sincronização.")
