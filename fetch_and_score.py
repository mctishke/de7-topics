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
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

FEEDS = [
    "https://www.tijd.be/rss/nieuws.xml",
    "https://www.tijd.be/rss/ondernemen.xml",
    "https://www.tijd.be/rss/politiek.xml",
    "https://www.tijd.be/rss/cultuur.xml",
    "https://www.tijd.be/rss/opinie.xml",
    "https://www.tijd.be/rss/sabato.xml",
    "https://www.tijd.be/rss/markten_live.xml",
    "https://www.tijd.be/rss/fondsen.xml",
    "https://www.tijd.be/rss/netto.xml",
]

DE7_FEED = (
    "https://www.omnycontent.com/d/playlist/5978613f-cd11-4352-8f26-adb900fa9a58/"
    "3c1222e5-288f-4047-a2f0-ae1b00a91688/a0389eb5-55da-493d-b7bb-ae1b00d0d95a/podcast.rss"
)

USER_AGENT = "Mozilla/5.0 (compatible; De7TopicsBot/1.0)"
ARTICLE_ID_RE = re.compile(r"(\d+)(?:\.html)?/?(?:[?#].*)?$")
DE7_LINK_RE = re.compile(r'href="https://www\.tijd\.be/[^"]*?/(\d+)\.html"')

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

MAX_AGE = timedelta(hours=30)
MAX_ARTICLES = 40


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

    return score, in_de7


def main():
    now = datetime.now(timezone.utc)
    cutoff = now - MAX_AGE

    de7_ids, de7_title = get_de7_ids()

    articles_by_id = {}
    for feed_url in FEEDS:
        try:
            xml_bytes = fetch(feed_url)
        except Exception as exc:
            print(f"Kon feed niet ophalen ({feed_url}): {exc}")
            continue

        for article in parse_rss_items(xml_bytes):
            if article["id"] in articles_by_id:
                continue
            pub_date = parse_pub_date(article["pubDate"])
            if pub_date and pub_date < cutoff:
                continue
            score, in_de7 = score_article(article, de7_ids)
            article["score"] = score
            article["in_de7"] = in_de7
            articles_by_id[article["id"]] = article

    articles = sorted(articles_by_id.values(), key=lambda a: a["score"], reverse=True)
    articles = articles[:MAX_ARTICLES]

    output = {
        "generated_at": now.isoformat(),
        "de7_title": de7_title,
        "de7_matched_count": sum(1 for a in articles if a["in_de7"]),
        "articles": articles,
    }

    with open("docs/data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Geschreven: {len(articles)} artikels, {output['de7_matched_count']} uit De 7 gematcht")


if __name__ == "__main__":
    main()
