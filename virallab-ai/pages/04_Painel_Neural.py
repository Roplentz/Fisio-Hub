from __future__ import annotations

from pathlib import Path

import streamlit as st

from virallab.neural_status import collect_neural_status

APP_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = APP_ROOT / "workspace"

st.set_page_config(page_title="Painel Neural · RP ViralLab", page_icon="🧠", layout="wide")

st.markdown(
    """
    <style>
    :root { --bg:#061018; --panel:#102430; --line:rgba(255,255,255,.10); --text:#f4f8fa; --muted:#90a8b5; --cyan:#45d6dc; }
    .stApp { background:var(--bg); color:var(--text); }
    .block-container { max-width:1180px; padding-top:1.2rem; padding-bottom:4rem; }
    .neural-hero { padding:28px; border:1px solid var(--line); border-radius:26px; background:linear-gradient(135deg,#153341,#081820); margin-bottom:18px; }
    .neural-hero h1 { margin:.25rem 0; font-size:40px; letter-spacing:-1.7px; }
    .neural-hero p { margin:0; color:var(--muted); }
    .status-card { height:100%; padding:18px; border:1px solid var(--line); border-radius:19px; background:linear-gradient(180deg,#112834,#0a1b24); }
    .status-top { display:flex; justify-content:space-between; gap:10px; align-items:center; }
    .status-name { font-weight:850; font-size:17px; }
    .status-pill { padding:5px 9px; border-radius:999px; font-size:10px; font-weight:850; text-transform:uppercase; }
    .ready { background:rgba(85,210,140,.15); color:#76e1a5; }
    .learning { background:rgba(69,214,220,.14); color:#6ce7ec; }
    .setup { background:rgba(238,187,93,.13); color:#e7c477; }
    .offline { background:rgba(246,104,104,.13); color:#ff9191; }
    .status-detail { margin-top:12px; color:#d2e0e6; font-size:13px; }
    .status-action { margin-top:9px; color:var(--muted); font-size:11px; }
    @media(max-width:720px){
      .block-container{padding-left:.85rem;padding-right:.85rem}
      .neural-hero{padding:21px;border-radius:20px}
      .neural-hero h1{font-size:29px;letter-spacing:-1px}
      [data-testid="stMetric"]{padding:10px!important}
      [data-testid="stMetricValue"]{font-size:22px!important}
      .status-card{padding:15px;border-radius:16px}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="neural-hero">
      <div style="color:#45d6dc;font-size:11px;font-weight:900;letter-spacing:.13em;text-transform:uppercase">Sprint 5.1 · observabilidade</div>
      <h1>Painel Neural</h1>
      <p>Veja pelo celular quais motores estão ativos, o que o sistema já aprendeu e o que precisa de configuração.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

if st.button("Atualizar diagnóstico", type="primary", use_container_width=True):
    st.cache_data.clear()


@st.cache_data(ttl=30, show_spinner=False)
def get_status() -> dict:
    return collect_neural_status(WORKSPACE)


status = get_status()
col1, col2, col3 = st.columns(3)
col1.metric("Motores prontos", f"{status['ready_count']}/{status['total_count']}")
col2.metric("Aprendizados", status["feedback_count"])
col3.metric("Projetos", status["project_count"])

st.markdown("### Estado dos serviços")
services = status["services"]
for start in range(0, len(services), 2):
    columns = st.columns(2)
    for column, service in zip(columns, services[start:start + 2]):
        state = service["state"]
        label = {"ready": "Ativo", "learning": "Aprendendo", "setup": "Configurar", "offline": "Offline"}.get(state, state)
        action = service.get("action", "")
        with column:
            st.markdown(
                f"""
                <div class="status-card">
                  <div class="status-top">
                    <div class="status-name">{service['label']}</div>
                    <div class="status-pill {state}">{label}</div>
                  </div>
                  <div class="status-detail">{service['detail']}</div>
                  <div class="status-action">{action}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")

with st.expander("Entenda o modo celular"):
    st.markdown(
        """
        **No celular**, você acessa o ViralLab pelo navegador ou aplicativo, mas os modelos locais não rodam dentro do telefone por meio do Streamlit Cloud.

        - Gemini funciona pela nuvem.
        - Qwen e BGE-M3 funcionam quando o servidor do ViralLab consegue acessar um Ollama remoto.
        - `localhost` aponta para o próprio servidor onde o app está rodando, não para o seu computador em casa.
        - O fallback local determinístico mantém a geração disponível quando os demais motores falham.
        """
    )

if status["ollama_models"]:
    with st.expander("Modelos detectados no Ollama"):
        for model in status["ollama_models"]:
            st.code(model)
