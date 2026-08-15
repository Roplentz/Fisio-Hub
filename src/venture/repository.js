const STORAGE_KEY = 'fisiohub.venture.projects.v1';

function readLocal() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
  catch { return {}; }
}

function writeLocal(data) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export async function saveProject(state, supabase = null) {
  if (supabase) {
    const payload = {
      id: state.project_id,
      user_id: state.user_id,
      name: state.project_name,
      current_phase: state.current_phase,
      status: state.status,
      state,
      updated_at: state.updated_at
    };
    const { error } = await supabase.from('venture_projects').upsert(payload);
    if (error) throw error;
    return state;
  }
  const projects = readLocal();
  projects[state.project_id] = state;
  writeLocal(projects);
  return state;
}

export async function loadProject(projectId, supabase = null) {
  if (supabase) {
    const { data, error } = await supabase
      .from('venture_projects')
      .select('state')
      .eq('id', projectId)
      .maybeSingle();
    if (error) throw error;
    return data?.state || null;
  }
  return readLocal()[projectId] || null;
}

export async function listProjects(supabase = null) {
  if (supabase) {
    const { data, error } = await supabase
      .from('venture_projects')
      .select('id,name,current_phase,status,updated_at')
      .order('updated_at', { ascending: false });
    if (error) throw error;
    return data || [];
  }
  return Object.values(readLocal()).sort((a,b) => (b.updated_at || '').localeCompare(a.updated_at || ''));
}
