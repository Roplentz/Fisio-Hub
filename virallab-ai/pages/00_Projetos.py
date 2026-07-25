from __future__ import annotations

from pathlib import Path

import streamlit as st

from virallab.project_store import ProjectStore

APP_ROOT = Path(__file__).resolve().parents[1]
PROJECTS_DIR = APP_ROOT / "workspace" / "projects"
store = ProjectStore(PROJECTS_DIR)

st.set_page_config(page_title="Projetos · RP ViralLab", page_icon="💾", layout="wide")
st.markdown(
    """
    <style>
    .block-container{max-width:1100px;padding-top:1rem;padding-bottom:4rem}
    .project-card{padding:18px;border:1px solid rgba(255,255,255,.12);border-radius:18px;background:linear-gradient(180deg,rgba(19,42,56,.96),rgba(11,27,38,.96));margin-bottom:12px}
    .project-id{font-size:12px;font-weight:900;letter-spacing:.14em;color:#45d6dc}
    .project-title{font-size:23px;font-weight:900;margin:5px 0;color:white}
    .project-meta{font-size:13px;color:#9bb0bd;line-height:1.55}
    .stButton>button,.stDownloadButton>button{min-height:50px;border-radius:13px;font-weight:800}
    @media(max-width:720px){.block-container{padding:.7rem .8rem 3rem}[data-testid="column"]{min-width:100%!important}.project-card{padding:15px;border-radius:16px}}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("💾 Projetos")
st.caption("Salve, reabra e continue seus roteiros, criativos e renders sem misturar trabalhos.")

current_package = st.session_state.get("package")
current_raw_id = str(st.session_state.get("project_id", "")).strip()
current_id = current_raw_id if current_raw_id.isdigit() else store.next_id()

if current_package is not None:
    with st.container(border=True):
        st.subheader("Salvar trabalho atual")
        st.caption(f"O roteiro aberto será salvo como Projeto {int(current_id):03d}, incluindo os criativos já gerados na pasta atual.")
        current_name = st.text_input(
            "Nome do projeto",
            value=getattr(getattr(current_package, "brief", None), "theme", "") or f"Projeto {int(current_id):03d}",
            key="save-current-project-name",
        )
        if st.button("💾 Salvar projeto atual", type="primary", use_container_width=True):
            try:
                clean_id = f"{int(current_id):03d}"
                current_dir_raw = st.session_state.get("package_dir")
                current_dir = Path(current_dir_raw) if current_dir_raw else None
                destination = store.project_dir(clean_id)
                if current_dir and current_dir.exists() and current_dir.resolve() != destination.resolve():
                    if destination.exists():
                        import shutil
                        shutil.rmtree(destination)
                    import shutil
                    shutil.copytree(current_dir, destination)
                saved = store.save(
                    clean_id,
                    name=current_name,
                    package=current_package,
                    preferred_hook=str(st.session_state.get("preferred_hook", "")),
                    status="em produção",
                )
                st.session_state.project_id = saved.project_id
                st.session_state.package_dir = str(store.project_dir(saved.project_id))
                st.success(f"Projeto {saved.project_id} salvo. Você pode sair e reabri-lo pela biblioteca.")
                st.rerun()
            except Exception as exc:
                st.error(f"Não foi possível salvar: {exc}")

with st.container(border=True):
    st.subheader("Criar ou importar")
    left, right = st.columns(2)
    with left:
        next_id = store.next_id()
        st.metric("Próximo código", next_id)
        name = st.text_input("Nome do novo projeto", placeholder="Ex.: IA e prontuários clínicos")
        if st.button("＋ Criar projeto numerado", type="primary", use_container_width=True):
            saved = store.save(next_id, name=name or f"Projeto {next_id}", status="novo")
            st.session_state.project_id = saved.project_id
            st.session_state.package = None
            st.session_state.package_dir = str(store.project_dir(saved.project_id))
            st.session_state.preferred_hook = ""
            st.session_state.nav_view = "Studio"
            st.success(f"Projeto {saved.project_id} criado.")
            st.switch_page("app.py")
    with right:
        backup = st.file_uploader("Importar backup do ViralLab", type=["zip"])
        if backup is not None and st.button("Importar como novo projeto", use_container_width=True):
            try:
                saved = store.import_zip(backup.getvalue())
                st.success(f"Backup importado como Projeto {saved.project_id}.")
                st.rerun()
            except Exception as exc:
                st.error(f"Não foi possível importar: {exc}")

st.info("No Streamlit Cloud, o disco pode ser reiniciado em atualizações ou períodos de inatividade. Use **Baixar backup ZIP** para manter uma cópia permanente no celular.")

projects = store.list_projects()
if not projects:
    st.warning("Nenhum projeto salvo ainda.")
else:
    st.subheader(f"Biblioteca · {len(projects)} projeto(s)")
    for project in projects:
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="project-card">
                  <div class="project-id">PROJETO {project.project_id}</div>
                  <div class="project-title">{project.name}</div>
                  <div class="project-meta">Tema: {project.theme or 'a definir'}<br>Status: {project.status}<br>Cenas: {project.scenes} · Criativos aprovados: {project.approved_assets}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            a, b = st.columns(2)
            if a.button("Abrir e continuar", key=f"open-{project.project_id}", type="primary", use_container_width=True):
                try:
                    saved, package, preferred_hook = store.load(project.project_id)
                    st.session_state.project_id = saved.project_id
                    st.session_state.package = package
                    st.session_state.package_dir = str(store.project_dir(saved.project_id))
                    st.session_state.preferred_hook = preferred_hook or (package.hook if package else "")
                    st.session_state.nav_view = "Studio"
                    st.switch_page("app.py")
                except Exception as exc:
                    st.error(f"Não foi possível abrir: {exc}")
            try:
                backup_bytes = store.export_zip(project.project_id)
                b.download_button(
                    "Baixar backup ZIP",
                    backup_bytes,
                    file_name=f"viralLab-projeto-{project.project_id}.zip",
                    mime="application/zip",
                    key=f"backup-{project.project_id}",
                    use_container_width=True,
                )
            except Exception as exc:
                b.error(str(exc))

            with st.expander("Gerenciar projeto"):
                confirm = st.checkbox("Confirmo que desejo excluir", key=f"confirm-{project.project_id}")
                if st.button("Excluir projeto", key=f"delete-{project.project_id}", disabled=not confirm, use_container_width=True):
                    store.delete(project.project_id)
                    if str(st.session_state.get("project_id", "")) == project.project_id:
                        st.session_state.project_id = store.next_id()
                        st.session_state.package = None
                        st.session_state.package_dir = None
                    st.rerun()
