create table if not exists public.venture_projects (
  id uuid primary key,
  user_id uuid references auth.users(id) on delete cascade,
  name text not null,
  current_phase integer not null default 0,
  status text not null default 'active',
  state jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists venture_projects_user_id_idx on public.venture_projects(user_id);
create index if not exists venture_projects_updated_at_idx on public.venture_projects(updated_at desc);

alter table public.venture_projects enable row level security;

create policy "Users can read own venture projects"
on public.venture_projects for select
using (auth.uid() = user_id);

create policy "Users can insert own venture projects"
on public.venture_projects for insert
with check (auth.uid() = user_id);

create policy "Users can update own venture projects"
on public.venture_projects for update
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can delete own venture projects"
on public.venture_projects for delete
using (auth.uid() = user_id);

comment on table public.venture_projects is 'Project State persistente do FisioHub Venture Copilot.';
