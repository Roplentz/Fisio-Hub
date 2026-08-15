const STORAGE_KEY = 'fisiohub.venture.project';

const hasSupabaseEnv = () => Boolean(
  import.meta.env.VITE_SUPABASE_URL && import.meta.env.VITE_SUPABASE_ANON_KEY
);

async function getSupabase() {
  if (!hasSupabaseEnv()) return null;
  const { createClient } = await import('@supabase/supabase-js');
  return createClient(import.meta.env.VITE_SUPABASE_URL, import.meta.env.VITE_SUPABASE_ANON_KEY);
}

export async function loadProjectState() {
  const local = localStorage.getItem(STORAGE_KEY);
  const fallback = local ? JSON.parse(local) : null;
  const supabase = await getSupabase();
  if (!supabase) return fallback;

  const projectId = fallback?.project_id;
  if (!projectId) return fallback;

  const { data, error } = await supabase
    .from('project_states')
    .select('state')
    .eq('project_id', projectId)
    .maybeSingle();

  if (error) {
    console.warn('Supabase load failed; using local persistence.', error.message);
    return fallback;
  }
  return data?.state || fallback;
}

export async function saveProjectState(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  const supabase = await getSupabase();
  if (!supabase) return { mode: 'local' };

  const payload = {
    project_id: state.project_id,
    state,
    updated_at: new Date().toISOString(),
  };
  const { error } = await supabase.from('project_states').upsert(payload, { onConflict: 'project_id' });
  if (error) {
    console.warn('Supabase save failed; local persistence is still active.', error.message);
    return { mode: 'local', warning: error.message };
  }
  return { mode: 'supabase' };
}

export function clearProjectState() {
  localStorage.removeItem(STORAGE_KEY);
}
