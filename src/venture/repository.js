const STORAGE_KEY = 'fisiohub.venture.projects.v1';

function readLocal() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
  catch { return {}; }
}

function writeLocal(data) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

function saveLocal(state) {
  const projects = readLocal();
  projects[state.project_id] = state;
  writeLocal(projects);
  return state;
}

async function authenticatedUser(supabase) {
  if (!supabase) return null;
  try {
    const { data, error } = await supabase.auth.getUser();
    if (error) return null;
    return data?.user || null;
  } catch {
    return null;
  }
}

export async function saveProject(state, supabase = null) {
  const user = await authenticatedUser(supabase);
  if (!supabase || !user) return saveLocal(state);

  const persistedState = { ...state, user_id: user.id, updated_at: new Date().toISOString() };
  const payload = {
    id: persistedState.project_id,
    user_id: user.id,
    name: persistedState.project_name,
    current_phase: persistedState.current_phase,
    status: persistedState.status,
    state: persistedState,
    updated_at: persistedState.updated_at
  };

  const { error } = await supabase.from('venture_projects').upsert(payload);
  if (error) {
    console.warn('Supabase indisponível para este projeto; usando persistência local.', error.message);
    return saveLocal(state);
  }
  saveLocal(persistedState);
  return persistedState;
}

export async function loadProject(projectId, supabase = null) {
  const user = await authenticatedUser(supabase);
  if (supabase && user) {
    const { data, error } = await supabase
      .from('venture_projects')
      .select('state')
      .eq('id', projectId)
      .eq('user_id', user.id)
      .maybeSingle();
    if (!error && data?.state) return data.state;
  }
  return readLocal()[projectId] || null;
}

export async function listProjects(supabase = null) {
  const user = await authenticatedUser(supabase);
  if (supabase && user) {
    const { data, error } = await supabase
      .from('venture_projects')
      .select('id,name,current_phase,status,updated_at,state')
      .eq('user_id', user.id)
      .order('updated_at', { ascending: false });
    if (!error && data?.length) return data.map(item => item.state || item);
  }
  return Object.values(readLocal()).sort((a,b) => (b.updated_at || '').localeCompare(a.updated_at || ''));
}
