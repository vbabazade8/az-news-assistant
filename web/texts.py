"""Texts for the website in three languages, and date formatting.

To add a new language: add it to LANGUAGES and add its texts, months and weekdays below.
"""

LANGUAGES = ["en", "az", "ru"]

TEXTS = {
    "en": {
        "tagline": "Daily investment brief from Azerbaijani news",
        "archive": "Archive",
        "empty": "There is no digest for this day yet. A new digest appears every morning.",
        "footer": "Collected from report.az, apa.az and axar.az. Written by Gemini — every fact links to the original article, so you can check it.",
    },
    "az": {
        "tagline": "Azərbaycan xəbərlərindən gündəlik investisiya icmalı",
        "archive": "Arxiv",
        "empty": "Bu gün üçün hələ icmal yoxdur. Yeni icmal hər səhər çıxır.",
        "footer": "Mənbələr: report.az, apa.az və axar.az. İcmalı Gemini yazır — hər fakt orijinal xəbərə keçid ilə verilir, yoxlaya bilərsiniz.",
    },
    "ru": {
        "tagline": "Ежедневный инвестиционный обзор новостей Азербайджана",
        "archive": "Архив",
        "empty": "Дайджеста за этот день пока нет. Новый дайджест появляется каждое утро.",
        "footer": "Источники: report.az, apa.az и axar.az. Дайджест пишет Gemini — каждый факт ведёт на исходную статью, его можно проверить.",
    },
}

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
    "az": ["yanvar", "fevral", "mart", "aprel", "may", "iyun",
           "iyul", "avqust", "sentyabr", "oktyabr", "noyabr", "dekabr"],
    "ru": ["января", "февраля", "марта", "апреля", "мая", "июня",
           "июля", "августа", "сентября", "октября", "ноября", "декабря"],
}

# Monday first, like date.weekday()
WEEKDAYS = {
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "az": ["Bazar ertəsi", "Çərşənbə axşamı", "Çərşənbə", "Cümə axşamı", "Cümə", "Şənbə", "Bazar"],
    "ru": ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"],
}


def format_day_month(day, language):
    """10 October / 10 oktyabr / 10 октября"""
    return f"{day.day} {MONTHS[language][day.month - 1]}"


def format_full_date(day, language):
    """10 October 2026"""
    return f"{format_day_month(day, language)} {day.year}"


def format_weekday(day, language):
    """Saturday / Şənbə / суббота"""
    return WEEKDAYS[language][day.weekday()]