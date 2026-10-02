import csv
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "https://report.az"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
}
BAKU_TZ = timezone(timedelta(hours=4))
HOURS_BACK = 24
MAX_PAGES = 100  
OUTPUT_FILE = Path("data/report_az.csv")


def fetch_html(url, params=None):
    response = requests.get(url, headers=HEADERS, params=params, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def parse_timestamp(text):
    return datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=BAKU_TZ)


def parse_cards(html):
    soup = BeautifulSoup(html, "html.parser")
    news = []

    for block in soup.find_all("div", class_="index-post-block"):
        card = block.find("a", class_="news__item")
        if card is None:
            continue

        title = card.find("h2", class_="news__title")
        category = card.find("span", class_="news__category")
        date_items = card.find("ul", class_="news__date").find_all("li")

        news.append({
            "title": title.get_text(strip=True),
            "url": BASE_URL + card["href"],
            "category": category.get_text(strip=True) if category else None,
            "date": date_items[0].get_text(strip=True),
            "time": date_items[1].get_text(strip=True),
            "timestamp": block["data-timestamp"],
        })

    return news


def fetch_article_text(url):
    soup = BeautifulSoup(fetch_html(url), "html.parser")

    desc = soup.find("div", class_="news-detail__desc")
    if desc is None:
        return ""

    paragraphs = []
    for p in desc.find_all("p"):
        text = p.get_text(" ", strip=True)
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def save_csv(news, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(news[0].keys()))
        writer.writeheader()
        writer.writerows(news)
    print(f"saved {len(news)} news to {path}")


cutoff = datetime.now(BAKU_TZ) - timedelta(hours=HOURS_BACK)
print("collecting news newer than:", cutoff.strftime("%Y-%m-%d %H:%M:%S"))

all_news = []
seen_urls = set()

page_news = parse_cards(fetch_html(BASE_URL + "/son-xeberler"))

for page in range(1, MAX_PAGES + 1):
    new_count = 0
    for item in page_news:
        if parse_timestamp(item["timestamp"]) < cutoff:
            continue
        if item["url"] not in seen_urls:
            seen_urls.add(item["url"])
            all_news.append(item)
            new_count += 1

    print(f"page {page}: got {len(page_news)}, new {new_count}, total {len(all_news)}")

    if not page_news:
        print("empty page - stop")
        break

    oldest_on_page = parse_timestamp(page_news[-1]["timestamp"])
    if oldest_on_page < cutoff:
        print(f"reached news older than {HOURS_BACK} hours - stop")
        break

    if page == MAX_PAGES:
        print("reached MAX_PAGES safety limit - stop")
        break

    cursor = page_news[-1]["timestamp"]
    time.sleep(1)
    page_news = parse_cards(fetch_html(
        BASE_URL + "/infinity/index",
        params={"date": cursor, "oldest": 1},
    ))

print("total news:", len(all_news))

for i, item in enumerate(all_news, start=1):
    try:
        item["content"] = fetch_article_text(item["url"])
    except requests.RequestException as error:
        print(f"failed: {item['url']} ({error})")
        item["content"] = ""

    print(f"article {i}/{len(all_news)}: {len(item['content'])} chars - {item['title']}")
    time.sleep(1)

if all_news:
    save_csv(all_news, OUTPUT_FILE)

empty = sum(1 for item in all_news if not item["content"])
print("articles without text:", empty)