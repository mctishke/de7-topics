-- Migratie: voegt de ignored_articles-tabel toe aan een bestaand project.
-- Plak dit in Supabase: Project > SQL Editor > New query > Run.

create table if not exists ignored_articles (
  id bigint generated always as identity primary key,
  article_id text not null unique,
  ignored_by text not null,
  created_at timestamptz not null default now()
);

alter table ignored_articles enable row level security;

create policy "ignored_articles: select all" on ignored_articles for select using (true);
create policy "ignored_articles: insert all" on ignored_articles for insert with check (true);
