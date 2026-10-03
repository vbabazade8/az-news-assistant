import csv
import requests
from scraper_job.config import HEADERS


def fetch_html(url, params=None):
    response = requests.get(url, headers=HEADERS, params=params, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def save_csv(news, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(news[0].keys()))
        writer.writeheader()
        writer.writerows(news)
    print(f"saved {len(news)} news to {path}")