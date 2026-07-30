-- Migratie: van up/downvote (-1/1) naar een enkele ster-knop (0/1).
-- Enkel nodig als je al eerder supabase_schema.sql draaide met de oude
-- constraint. Plak dit in Supabase: Project > SQL Editor > New query > Run.

alter table votes drop constraint if exists votes_value_check;

-- Bestaande downvotes (-1) hebben in het nieuwe ster-model geen equivalent;
-- we zetten ze om naar "niet gesterd" (0). Moet gebeuren terwijl de
-- constraint nog niet actief is, dus na de drop hierboven.
update votes set value = 0 where value = -1;

alter table votes add constraint votes_value_check check (value in (0, 1));

-- Ruim de teststemmen/comments op die tijdens de ontwikkeling zijn ingevoerd.
delete from votes where voter_id in ('claude-mechanism-check', 'claude-check');
delete from votes where article_id = 'verification-test';
delete from comments where body = 'Dit is een test comment';
