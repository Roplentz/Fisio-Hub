create table if not exists public.venture_evidence (
  id uuid primary key,
  project_id uuid not null references public.venture_projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  type text not null default 'observation',
  source text not null default '',
  evidence_date date not null default current_date,
  description text not null,
  hypothesis text not null default '',
  strength text not null check (strength in ('weak','moderate','strong')),
  rationale text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists venture_evidence_project_id_idx on public.venture_evidence(project_id);
create index if not exists venture_evidence_user_id_idx on public.venture_evidence(user_id);
create index if not exists venture_evidence_strength_idx on public.venture_evidence(strength);

alter table public.venture_evidence enable row level security;

create policy "Users can read own venture evidence"
on public.venture_evidence for select
using (auth.uid() = user_id);

create policy "Users can insert own venture evidence"
on public.venture_evidence for insert
with check (
  auth.uid() = user_id
  and exists (
    select 1 from public.venture_projects p
    where p.id = project_id and p.user_id = auth.uid()
  )
);

create policy "Users can update own venture evidence"
on public.venture_evidence for update
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can delete own venture evidence"
on public.venture_evidence for delete
using (auth.uid() = user_id);

comment on table public.venture_evidence is 'Evidence Engine: evidências relacionadas a projetos e hipóteses do Venture Copilot.';
