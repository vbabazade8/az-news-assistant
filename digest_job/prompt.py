LEAD_MAX_CHARS = 300  # how much of the article text to keep


def make_lead(content):
    if not content:
        return ""
    first_paragraph = content.split("\n")[0]
    return first_paragraph[:LEAD_MAX_CHARS]


def build_news_block(news):
    lines = []
    for i, item in enumerate(news, start=1):
        published = item["published_at"].strftime("%Y-%m-%d %H:%M")
        lines.append(f"[{i}] {item['source']} | {published}")
        lines.append(item["title"])
        lines.append(make_lead(item["content"]))
        lines.append("")
    return "\n".join(lines)


def build_digest_prompt(news_block, digest_date):
    return f"""You are a senior analyst at an investment fund in Azerbaijan.
Your reader is the CEO of a venture / investment fund who has no time to read the news.

Below are news from Azerbaijani news sites published in the 24 hours before {digest_date}.
Each news item has a number in square brackets, the source, the time, the title and the beginning of the text.

YOUR TASK
1. Select only the news that matter for investment and business: economy, finance, banking,
   energy, oil and gas, trade, markets, companies, startups, technology, government economic policy.
   Ignore sports, crime, accidents, entertainment and routine diplomatic meetings
   unless they clearly affect the economy.
2. Write a short, high-level digest with these sections:
   - Top stories: 3-7 most important items. For each: a bold one-line headline,
     1-2 sentences on why it matters for investors, and the news numbers in brackets, like [12].
   - Market signals: 2-4 short bullet points about trends.
   - Risks to watch: 1-3 short bullet points.
   - Actionable insights: 3-5 concrete things a fund CEO could do or check this week.
3. Use only facts from the news below. Do not invent numbers, names or events.
   If there are few relevant news, write a shorter digest and say so.
4. Write the same digest in three languages: English, Azerbaijani and Russian.
   Use Markdown formatting inside each digest.

ANSWER FORMAT
Return only JSON with exactly these keys:
- "en": the digest in English
- "az": the digest in Azerbaijani
- "ru": the digest in Russian
- "news_used": a list of the news numbers you used, for example [3, 12, 40]

NEWS
{news_block}
"""