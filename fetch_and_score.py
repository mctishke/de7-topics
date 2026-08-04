#!/usr/bin/env python3
"""
Haalt De Tijd RSS-feeds en de 'De 7'-podcastfeed op, matcht artikels die in
De 7 aan bod komen, scoort alle artikels en schrijft het resultaat naar
docs/data.json (dat door de statische frontend wordt ingelezen).

Geen externe dependencies (alleen Python stdlib), zodat dit zowel lokaal
als in GitHub Actions zonder pip-install kan draaien.
"""
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

BRUSSELS = ZoneInfo("Europe/Brussels")

FEEDS = [
    "https://www.tijd.be/rss/nieuws.xml",
    "https://www.tijd.be/rss/ondernemen.xml",
    "https://www.tijd.be/rss/politiek.xml",
    "https://www.tijd.be/rss/cultuur.xml",
    "https://www.tijd.be/rss/opinie.xml",
    "https://www.tijd.be/rss/sabato.xml",
    "https://www.tijd.be/rss/fondsen.xml",
    "https://www.tijd.be/rss/netto.xml",
]

DE7_FEED = (
    "https://www.omnycontent.com/d/playlist/5978613f-cd11-4352-8f26-adb900fa9a58/"
    "3c1222e5-288f-4047-a2f0-ae1b00a91688/a0389eb5-55da-493d-b7bb-ae1b00d0d95a/podcast.rss"
)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
# tijd.be blokkeert cloud/datacenter-IP-reeksen (zoals GitHub Actions) voor
# artikelpagina's, ongeacht User-Agent -- geverifieerd via directe 403's.
# r.jina.ai is een publieke "reader"-proxy (bedoeld voor dit soort gebruik)
# die vanaf een andere, niet-geblokkeerde IP fetcht en desgevraagd de ruwe
# HTML teruggeeft, zodat we gewoon dezelfde og:image-regex kunnen hergebruiken.
# Die proxy blokkeert op zijn beurt UA-strings die een browser nabootsen
# (waarschijnlijk net omdat een "Chrome"-UA zonder bijhorende browser-
# fingerprint verdacht overkomt) maar laat een gewone curl-UA wel door --
# geverifieerd door meerdere UA's naast elkaar te testen.
READER_PROXY = "https://r.jina.ai/"
READER_USER_AGENT = "curl/8.4.0"
ARTICLE_ID_RE = re.compile(r"(\d+)(?:\.html)?/?(?:[?#].*)?$")
DE7_LINK_RE = re.compile(r'href="https://www\.tijd\.be/[^"]*?/(\d+)\.html"')
OG_IMAGE_RE = re.compile(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"')
IMAGE_PREVIEW_BYTES = 20000
IMAGE_FETCH_WORKERS = 3  # laag houden: gratis/anonieme r.jina.ai heeft een rate-limit

# Simpele heuristiek voor "leent zich goed als video op social" -- vrij aan te
# passen op basis van wat het team in de praktijk goede/slechte topics vindt.
KEYWORDS = [
    "schok", "crisis", "record", "explosie", "verrassend", "onthult",
    "waarschuwt", "banen", "ontslag", "faillissement", "rechtszaak",
    "boete", "schandaal", "opmars", "fraude", "hackers", "cyberaanval",
    "staking", "akkoord", "protest",
]
NUMBER_RE = re.compile(r"\d+([.,]\d+)?\s*(%|procent|miljoen|miljard|euro)", re.IGNORECASE)
QUOTE_RE = re.compile(r"['‘’\"“”]")

# "Markten Live" wordt vaak als extra tag op allerlei artikels geplakt (niet
# enkel korte marktupdates), dus we sluiten het niet uit -- wel een kleine
# score-penalisatie zodat het iets lager komt te staan, zonder het risico om
# relevante artikels helemaal over het hoofd te zien.
CATEGORY_SCORE_PENALTY = {"Markten Live": -2}

MAX_ARTICLES = 40

DATA_FILE = "docs/data.json"

# Los van de dagelijkse reset van data.json: een rollend archief van de
# laatste RECENT_MAX_AGE dagen, enkel gebruikt door de "kies de daily"
# zoekbalk in de frontend -- zodat op een magere nieuwsdag ook een ouder
# artikel nog gevonden/gelinkt kan worden.
RECENT_FILE = "docs/recent_articles.json"
RECENT_MAX_AGE_DAYS = 14


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def extract_id(url):
    if not url:
        return None
    match = ARTICLE_ID_RE.search(url)
    return match.group(1) if match else None


def parse_pub_date(raw):
    try:
        return parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None


def parse_rss_items(xml_bytes):
    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or link).strip()
        article_id = extract_id(guid) or extract_id(link)
        if not article_id:
            continue
        items.append({
            "id": article_id,
            "title": title,
            "link": link,
            "category": (item.findtext("category") or "").strip(),
            "description": (item.findtext("description") or "").strip(),
            "pubDate": (item.findtext("pubDate") or "").strip(),
        })
    return items


def get_de7_ids():
    """Haalt de meest recente aflevering van De 7 op en geeft (ids, titel) terug."""
    try:
        xml_bytes = fetch(DE7_FEED)
    except Exception as exc:
        print(f"Kon De 7-feed niet ophalen: {exc}")
        return set(), None

    root = ET.fromstring(xml_bytes)
    item = root.find(".//item")
    if item is None:
        return set(), None

    description = item.findtext("description") or ""
    ids = set(DE7_LINK_RE.findall(description))
    title = (item.findtext("title") or "").strip()
    return ids, title


def load_previous_articles():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {a["id"]: a for a in data.get("articles", [])}


def load_recent_articles():
    try:
        with open(RECENT_FILE, "r", encoding="utf-8") as f:
            return {a["id"]: a for a in json.load(f).get("articles", [])}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_recent_articles(recent_pool, today):
    pruned = {
        article_id: a for article_id, a in recent_pool.items()
        if article_day(a) and (today - article_day(a)).days <= RECENT_MAX_AGE_DAYS
    }

    def sort_key(a):
        return parse_pub_date(a["pubDate"]) or datetime.min.replace(tzinfo=timezone.utc)

    with open(RECENT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"articles": sorted(pruned.values(), key=sort_key, reverse=True)},
            f, ensure_ascii=False, indent=2,
        )


def article_day(article):
    """Kalenderdag (Europe/Brussels) waarop een artikel gepubliceerd is."""
    pub_date = parse_pub_date(article.get("pubDate", ""))
    if pub_date is None:
        return None
    return pub_date.astimezone(BRUSSELS).date()


def fetch_og_image(url):
    """Haalt de og:image van een artikel op via de r.jina.ai reader-proxy
    (tijd.be blokkeert cloud-IP's rechtstreeks) en leest enkel de eerste
    paar KB, zodat we niet de volledige (zware) pagina moeten verwerken."""
    try:
        req = urllib.request.Request(
            f"{READER_PROXY}{url}",
            headers={"User-Agent": READER_USER_AGENT, "X-Return-Format": "html"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            chunk = resp.read(IMAGE_PREVIEW_BYTES).decode("utf-8", errors="ignore")
    except Exception as exc:
        print(f"[image debug] fetch faalde voor {url}: {exc!r}")
        return None

    match = OG_IMAGE_RE.search(chunk)
    if not match:
        print(f"[image debug] geen og:image gevonden voor {url} (eerste 200 tekens: {chunk[:200]!r})")
        return None
    image_url = match.group(1).replace("&amp;", "&")
    return re.sub(r"width=\d+", "width=480", image_url)


def score_article(article, de7_ids):
    score = 1
    in_de7 = article["id"] in de7_ids
    if in_de7:
        score += 10

    text = f"{article['title']} {article['description']}".lower()
    if NUMBER_RE.search(text):
        score += 2
    if QUOTE_RE.search(article["title"]):
        score += 2
    if len(article["title"]) <= 90:
        score += 1
    keyword_hits = sum(1 for kw in KEYWORDS if kw in text)
    score += min(keyword_hits, 3)
    score += CATEGORY_SCORE_PENALTY.get(article["category"], 0)

    return score, in_de7


def main():
    now = datetime.now(timezone.utc)
    today = now.astimezone(BRUSSELS).date()

    # "Vandaag"-pool voor de gewone suggestielijst (data.json): bevroren
    # scores, reset elke kalenderdag (Brussel-tijd) -- ongewijzigd t.o.v.
    # eerder.
    today_pool = {
        article_id: article
        for article_id, article in load_previous_articles().items()
        if article_day(article) == today
    }

    # Bredere pool voor de "kies de daily"-zoekfunctie (recent_articles.json):
    # alles wat de RSS-feeds ooit tonen, los van kalenderdag, aangevuld met
    # wat er al in het rollend archief zat. Zo hangt vindbaarheid niet af van
    # toevallig timing van de cronjob t.o.v. het publicatiemoment (bv. een
    # artikel van gisterenavond laat) -- enkel van de 14-dagen-bewaartermijn.
    recent_pool = load_recent_articles()

    de7_ids, de7_title = get_de7_ids()

    for feed_url in FEEDS:
        try:
            xml_bytes = fetch(feed_url)
        except Exception as exc:
            print(f"Kon feed niet ophalen ({feed_url}): {exc}")
            continue

        for article in parse_rss_items(xml_bytes):
            article_id = article["id"]
            if article_id not in recent_pool:
                recent_pool[article_id] = article

            if article_id in today_pool:
                continue
            if article_day(article) != today:
                continue
            score, in_de7 = score_article(article, de7_ids)
            article["score"] = score
            article["in_de7"] = in_de7
            today_pool[article_id] = article

    # 1 gezamenlijke image-fetch-ronde voor alles wat in een van beide pools
    # nog geen afbeelding heeft (gededupliceerd op artikel-ID). Een mislukte
    # fetch wordt niet blijvend onthouden: elke volgende run wordt opnieuw
    # geprobeerd voor wat nog steeds geen afbeelding heeft.
    link_by_id = {}
    for pool in (today_pool, recent_pool):
        for article_id, article in pool.items():
            if not article.get("image"):
                link_by_id[article_id] = article["link"]

    with ThreadPoolExecutor(max_workers=IMAGE_FETCH_WORKERS) as pool:
        fetched_images = dict(zip(link_by_id.keys(), pool.map(fetch_og_image, link_by_id.values())))

    fetched = 0
    for article_id, image in fetched_images.items():
        if image:
            fetched += 1
        if article_id in today_pool:
            today_pool[article_id]["image"] = image
        if article_id in recent_pool:
            recent_pool[article_id]["image"] = image

    articles = sorted(today_pool.values(), key=lambda a: a["score"], reverse=True)[:MAX_ARTICLES]

    output = {
        "generated_at": now.isoformat(),
        "date": today.isoformat(),
        "de7_title": de7_title,
        "de7_matched_count": sum(1 for a in articles if a["in_de7"]),
        "articles": articles,
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    write_recent_articles(recent_pool, today)

    print(
        f"Geschreven: {len(articles)} artikels, {output['de7_matched_count']} uit De 7 gematcht, "
        f"{fetched}/{len(link_by_id)} afbeeldingen deze run opgehaald"
    )


if __name__ == "__main__":
    main()
