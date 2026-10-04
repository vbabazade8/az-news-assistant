import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from scraper_job.config import BAKU_TZ, HOURS_BACK, MAX_PAGES
from scraper_job.utils.database import save_news
from scraper_job.utils.helpers import fetch_html, save_csv

sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "https://apa.az"
OUTPUT_FILE = Path("data/apa_az.csv")

MONTHS = {
    "yanvar": 1,
    "fevral": 2,
    "mart": 3,
    "aprel": 4,
    "may": 5,
    "iyun": 6,
    "iyul": 7,
    "avqust": 8,
    "sentyabr": 9,
    "oktyabr": 10,
    "noyabr": 11,
    "dekabr": 12,
}


def parse_datetime(date_text, time_text):
    day, month_name, year = date_text.split()
    hour, minute = time_text.split(":")
    month = MONTHS[month_name.lower()]
    return datetime(int(year), month, int(day), int(hour), int(minute), tzinfo=BAKU_TZ)


def parse_cards(html):
    soup = BeautifulSoup(html, "html.parser")
    news = []

    for card in soup.find_all("a", class_="news-item"):
        title = card.find("h2", class_="title")
        date_spans = card.find("div", class_="date").find_all("span")
        time_text = date_spans[0].get_text(strip=True)
        date_text = date_spans[1].get_text(strip=True)

        news.append({
            "title": title.get_text(" ", strip=True),
            "url": card["href"],
            "time": time_text,
            "date": date_text,
            "published_at": parse_datetime(date_text, time_text),
        })

    return news


def fetch_article_text(url):
    soup = BeautifulSoup(fetch_html(url), "html.parser")

    texts = soup.find("div", class_="texts")
    if texts is None:
        return ""

    paragraphs = []
    for p in texts.find_all("p"):
        text = p.get_text(" ", strip=True)
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


# --- 1. Collect the list of news for the last 24 hours ---
cutoff = datetime.now(BAKU_TZ) - timedelta(hours=HOURS_BACK)
print("collecting news newer than:", cutoff.strftime("%Y-%m-%d %H:%M:%S"))

all_news = []
seen_urls = set()

for page in range(1, MAX_PAGES + 1):
    page_news = parse_cards(fetch_html(BASE_URL + "/all-news", params={"page": page}))

    new_count = 0
    for item in page_news:
        if item["published_at"] < cutoff:
            continue
        if item["url"] not in seen_urls:
            seen_urls.add(item["url"])
            all_news.append(item)
            new_count += 1

    print(f"page {page}: got {len(page_news)}, new {new_count}, total {len(all_news)}")

    if not page_news:
        print("empty page - stop")
        break

    if page_news[-1]["published_at"] < cutoff:
        print(f"reached news older than {HOURS_BACK} hours - stop")
        break

    if page == MAX_PAGES:
        print("reached MAX_PAGES safety limit - stop")
        break

    time.sleep(1)

print("total news:", len(all_news))

# --- 2. Open each article and get its text ---
for i, item in enumerate(all_news, start=1):
    try:
        item["content"] = fetch_article_text(item["url"])
    except requests.RequestException as error:
        print(f"failed: {item['url']} ({error})")
        item["content"] = ""

    print(f"article {i}/{len(all_news)}: {len(item['content'])} chars - {item['title']}")
    time.sleep(1)

# --- 3. Save to CSV and to the database ---
if all_news:
    save_csv(all_news, OUTPUT_FILE)
    save_news(all_news, "apa.az")

empty = sum(1 for item in all_news if not item["content"])
print("articles without text:", empty)