from datetime import timedelta, timezone

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
}
BAKU_TZ = timezone(timedelta(hours=4))
HOURS_BACK = 24
MAX_PAGES = 100