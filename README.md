# De 7 Topics

Testversie van een tool die elke ochtend automatisch een geordend overzicht
biedt van mogelijke onderwerpen voor de dagelijkse videoredactie van De Tijd.
Draait volledig los van je laptop.

## Hoe het werkt

- Een GitHub Action haalt elke 15 min (ma-vr, 7:00-13:45 lokale tijd) de
  RSS-feeds van tijd.be en de "De 7"-podcastfeed op, scoort de artikels
  (basis-score + boost als het topic in De 7 zit + keyword-heuristiek), en
  commit het resultaat als `docs/data.json`.
- GitHub Pages serveert `docs/index.html`, een statische pagina die dat
  bestand toont als ranked lijst.
- Stemmen (up/down) en comments worden opgeslagen in Supabase (gratis tier) —
  dat is het enige stukje dat een "backend" nodig heeft, want GitHub Pages
  kan zelf niets opslaan.

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
3. Project > Settings > API: kopieer de "Project URL" en de "anon public" key.
4. Vul beide in bovenaan in `docs/index.html`:
   ```
   const SUPABASE_URL = "https://xxxx.supabase.co";
   const SUPABASE_ANON_KEY = "eyJ...";
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

## Bekende beperkingen (MVP)

- Geen login: iedereen met de link kan stemmen/reageren; stemmen per
  browser worden onthouden via een lokaal ID (geen echte accounts).
- "De 7" wordt gematcht op basis van links in de podcast-omschrijving —
  niet elk van de 7 besproken topics heeft altijd een gelinkt artikel.
- Leescijfers/kliekdata zijn niet geïntegreerd (intern platform vereist
  login en heeft mogelijk geen bruikbare API) — mogelijke volgende stap.
- Geen ochtendmelding (Slack/e-mail) in deze testversie — kan later als
  losse GitHub Action stap toegevoegd worden zodra de rest bruikbaar blijkt.
