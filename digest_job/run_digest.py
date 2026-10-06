import json
import sys
from datetime import datetime
from pathlib import Path

from digest_job.gemini import GEMINI_MODEL, ask_gemini
from digest_job.prompt import build_digest_prompt, build_news_block
from digest_job.sources import add_source_links
from scraper_job.config import BAKU_TZ
from scraper_job.utils.database import get_recent_news, save_digests, save_llm_call

sys.stdout.reconfigure(encoding="utf-8")

HOURS_BACK = 24
TASK = "digest"
INDUSTRY = "investment"
RAW_ANSWER_FILE = Path("data/last_gemini_answer.json")

DIGEST_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "en": {"type": "STRING"},
        "az": {"type": "STRING"},
        "ru": {"type": "STRING"},
        "news_used": {"type": "ARRAY", "items": {"type": "INTEGER"}},
    },
    "required": ["en", "az", "ru", "news_used"],
}

news = get_recent_news(HOURS_BACK)
print("news from the database:", len(news))

digest_date = datetime.now(BAKU_TZ).date()
prompt = build_digest_prompt(build_news_block(news), digest_date)
print("prompt characters:", len(prompt))

print("asking Gemini...")
answer = ask_gemini(prompt, schema=DIGEST_SCHEMA)

# Save the raw answer, so we can look at it if something goes wrong
RAW_ANSWER_FILE.parent.mkdir(parents=True, exist_ok=True)
RAW_ANSWER_FILE.write_text(answer, encoding="utf-8")

# Save the prompt and the raw answer to the database, before parsing,
# so even a broken answer is kept for debugging
llm_call_id = save_llm_call(TASK, INDUSTRY, GEMINI_MODEL, prompt, answer, len(news))

result = json.loads(answer)
print("news used:", len(result["news_used"]))

# Replace news numbers like [12, 40] with links to the original articles
texts = {
    "en": add_source_links(result["en"], news),
    "az": add_source_links(result["az"], news),
    "ru": add_source_links(result["ru"], news),
}
save_digests(digest_date, INDUSTRY, texts, len(result["news_used"]), GEMINI_MODEL, llm_call_id)

print()
print("===== EN =====")
print(texts["en"])