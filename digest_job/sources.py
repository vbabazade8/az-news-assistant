import re

# Finds "[12]" or "[12, 40, 47]" in the text
NEWS_NUMBERS_PATTERN = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")


def add_source_links(text, news):
    def replace(match):
        links = []
        for number_text in match.group(1).split(","):
            number = int(number_text)
            if 1 <= number <= len(news):
                item = news[number - 1]
                links.append(f"[{item['source']}]({item['url']})")

        if not links:
            return ""
        return "(" + ", ".join(links) + ")"

    return NEWS_NUMBERS_PATTERN.sub(replace, text)