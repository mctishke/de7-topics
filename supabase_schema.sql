-- De 7 Topics -- schema voor stemmen en comments
-- Plak dit volledig in Supabase: Project > SQL Editor > New query > Run

create table if not exists votes (
  id bigint generated always as identity primary key,
  article_id text not null,
  voter_id text not null,
  value smallint not null check (value in (-1, 1)),
  created_at timestamptz not null default now()
);

create table if not exists comments (
  id bigint generated always as identity primary key,
  article_id text not null,
  author text not null default 'Anoniem',
  body text not null,
  created_at timestamptz not null default now()
);

-- Row Level Security: dit is een intern team-tool zonder echte login, dus
-- we staan iedereen met de (publieke) anon-key toe om te lezen en te
-- schrijven. Er is bewust geen update/delete-recht: een gewijzigde stem is
-- gewoon een nieuwe rij (de frontend houdt per stemmer enkel de laatste
-- stem per artikel bij).
alter table votes enable row level security;
alter table comments enable row level security;

create policy "votes: select all" on votes for select using (true);
create policy "votes: insert all" on votes for insert with check (true);

create policy "comments: select all" on comments for select using (true);
create policy "comments: insert all" on comments for insert with check (true);
