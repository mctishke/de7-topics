# De 7 Topics

Testversie van een tool die elke ochtend automatisch een geordend overzicht
biedt van mogelijke onderwerpen voor de dagelijkse videoredactie van De Tijd.
Draait volledig los van je laptop.

## Hoe het werkt

- Een GitHub Action haalt elke 15 min (ma-vr, 7:00-13:45 lokale tijd) de
  RSS-feeds van tijd.be en de "De 7"-podcastfeed op, scoort de artikels
  (basis-score + boost als het topic in De 7 zit + keyword-heuristiek), en
  commit het resultaat als `docs/data.json`. Enkel artikels van de huidige
  kalenderdag (Europe/Brussels) worden getoond -- elke dag start met een
  schone lei.
- GitHub Pages serveert `docs/index.html`, een statische pagina die dat
  bestand toont als ranked lijst, met een "Beste"/"Meest recent"-toggle.
- Stemmen (ster) en comments worden opgeslagen in Supabase (gratis tier) —
  dat is het enige stukje dat een "backend" nodig heeft, want GitHub Pages
  kan zelf niets opslaan.
- Eén artikel per dag kan als "de daily" gepind worden (prominente banner
  bovenaan); wie daaraan meewerkt kan zichzelf toevoegen. Dat blijft, in
  tegenstelling tot de rest, wél bewaard in `docs/archief.html` -- ook na de
  dagelijkse reset.

Niemand hoeft hiervoor een server te draaien of aan te laten staan.

## Setup (eenmalig)

### 1. Naar GitHub pushen

```
cd ~/Developer/de7-topics
git init
git add .
git commit -m "Eerste versie"
```

Maak dan op github.com een nieuwe (private of public) repo aan, bv.
`de7-topics`, **zonder** README/gitignore aan te vinken. Volg daarna de
instructies die GitHub toont om een bestaande lokale repo te pushen, iets als:

```
git remote add origin git@github.com:<jouw-gebruikersnaam>/de7-topics.git
git branch -M main
git push -u origin main
```

### 2. GitHub Pages inschakelen

Repo > Settings > Pages > Source: "Deploy from a branch" > Branch: `main`,
map `/docs`. Na een minuutje krijg je een URL zoals
`https://<gebruikersnaam>.github.io/de7-topics/`.

### 3. Supabase-project aanmaken

1. Ga naar supabase.com, maak een gratis account/project.
2. Project > SQL Editor > plak de inhoud van `supabase_schema.sql` > Run.
3. Project > Settings > API: kopieer de "Project URL" en de "anon public"
   (of "publishable") key.
4. Vul beide in bovenaan in `docs/common.js`:
   ```
   const SUPABASE_URL = "https://xxxx.supabase.co";
   const SUPABASE_ANON_KEY = "eyJ..." of "sb_publishable_...";
   ```
5. Commit en push die wijziging.

### 4. Eerste keer data genereren

De workflow draait automatisch volgens het schema, maar je kan hem ook meteen
handmatig triggeren: repo > Actions > "Ververs topics" > Run workflow.

## Lokaal testen

```
python3 fetch_and_score.py   # genereert docs/data.json
cd docs && python3 -m http.server 8731
```
Open `http://localhost:8731`.

## Wie ben jij / avatars

Bovenaan de pagina kies je je naam (onthouden via je browser, geen login).
Die naam wordt gebruikt voor je stemmen en comments. Voor Bert, Roan, Lara,
Peter, Niels, Thijs, Seppe en Robbe staat er een echte foto (uit de
Obsidian-vault van Thijs); voor Maarten, Julie en elke andere naam wordt een
gekleurde initialen-avatar gegenereerd. Nieuwe foto's toevoegen: zet een
vierkante PNG in `docs/avatars/<naam>.png` en voeg de persoon toe aan de
`PEOPLE`-lijst in `docs/common.js`.

De "wie werkt mee"-selectie op de daily gebruikt een kleinere subset
(`MAKER_PEOPLE` in `docs/common.js`) -- Robbe, Maarten en Julie zijn daar
bewust uitgesloten, ook al kunnen ze wel gewoon zichzelf kiezen bovenaan om
te stemmen/reageren.

## Migraties

Bij een bestaand Supabase-project (nieuwe projecten hebben dit niet nodig,
die gebruiken gewoon het volledige `supabase_schema.sql`):

- `supabase_migration_star.sql` — up/downvote (-1/1) -> 1 ster-knop (0/1).
- `supabase_migration_daily_picks.sql` — voegt de `daily_picks`-tabel toe
  (nodig voor de "dit wordt de daily"-knop en het archief).
- `supabase_migration_ignored_articles.sql` — voegt de `ignored_articles`-
  tabel toe (nodig voor de "negeer dit artikel"-knop).

Gewoon plakken en runnen in Supabase SQL Editor.

## Bekende beperkingen (MVP)

- Geen login: iedereen met de link kan stemmen/reageren onder eender welke
  naam (geen wachtwoord/verificatie).
- "De 7" wordt gematcht op basis van links in de podcast-omschrijving —
  niet elk van de 7 besproken topics heeft altijd een gelinkt artikel.
- Leescijfers/kliekdata zijn niet geïntegreerd (intern platform vereist
  login en heeft mogelijk geen bruikbare API) — mogelijke volgende stap.
- Geen ochtendmelding (Slack/e-mail) in deze testversie — kan later als
  losse GitHub Action stap toegevoegd worden zodra de rest bruikbaar blijkt.
- De repo staat publiek op GitHub (vereist voor gratis Pages) — ook de
  avatarfoto's zijn dus wereldwijd zichtbaar, niet enkel voor het team.
