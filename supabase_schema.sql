-- De 7 Topics -- schema voor stemmen en comments
-- Plak dit volledig in Supabase: Project > SQL Editor > New query > Run

create table if not exists votes (
  id bigint generated always as identity primary key,
  article_id text not null,
  voter_id text not null,
  value smallint not null check (value in (0, 1)), -- 0 = ontsterd, 1 = ster
  created_at timestamptz not null default now()
);

create table if not exists comments (
  id bigint generated always as identity primary key,
  article_id text not null,
  author text not null default 'Anoniem',
  body text not null,
  created_at timestamptz not null default now()
);

-- 1 rij per dag: welk artikel de "daily" video wordt en wie eraan meewerkt.
-- Bewaart een kopie van titel/link/afbeelding, zodat het archief later nog
-- toont wat er gekozen was ook al staat het artikel niet meer in data.json
-- (dat reset elke kalenderdag).
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

-- Row Level Security: dit is een intern team-tool zonder echte login, dus
-- we staan iedereen met de (publieke) anon-key toe om te lezen en te
-- schrijven. votes/comments zijn bewust insert-only: een gewijzigde stem is
-- gewoon een nieuwe rij (de frontend houdt per stemmer enkel de laatste
-- stem per artikel bij). daily_picks heeft wel update/delete nodig (de
-- daily wijzigen/intrekken, makers toevoegen/verwijderen).
alter table votes enable row level security;
alter table comments enable row level security;
alter table daily_picks enable row level security;

create policy "votes: select all" on votes for select using (true);
create policy "votes: insert all" on votes for insert with check (true);

create policy "comments: select all" on comments for select using (true);
create policy "comments: insert all" on comments for insert with check (true);

create policy "daily_picks: select all" on daily_picks for select using (true);
create policy "daily_picks: insert all" on daily_picks for insert with check (true);
create policy "daily_picks: update all" on daily_picks for update using (true) with check (true);
create policy "daily_picks: delete all" on daily_picks for delete using (true);
