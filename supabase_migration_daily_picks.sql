-- Migratie: voegt de daily_picks-tabel toe aan een bestaand project.
-- Plak dit in Supabase: Project > SQL Editor > New query > Run.

create table if not exists daily_picks (
  id bigint generated always as identity primary key,
  pick_date date not null unique,
  article_id text not null,
  title text not null,
  link text not null,
  image text,
  category text,
  picked_by text not null,
  makers text[] not null default '{}',
  created_at timestamptz not null default now()
);

alter table daily_picks enable row level security;

create policy "daily_picks: select all" on daily_picks for select using (true);
create policy "daily_picks: insert all" on daily_picks for insert with check (true);
create policy "daily_picks: update all" on daily_picks for update using (true) with check (true);
create policy "daily_picks: delete all" on daily_picks for delete using (true);
