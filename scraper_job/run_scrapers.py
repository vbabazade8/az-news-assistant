import sys

from scraper_job.scrapers import apa_scraper, axar_scraper, report_scraper

# All scrapers: site name -> its run function.
# To add a new site, write its scraper and add one line here.
SCRAPERS = {
    "report.az": report_scraper.run,
    "apa.az": apa_scraper.run,
    "axar.az": axar_scraper.run,
}


def main():
    failed = []

    for name, run in SCRAPERS.items():
        print(f"========== {name} ==========")
        try:
            run()
        except Exception as error:
            print(f"[{name}] FAILED: {error}")
            failed.append(name)

    print()
    print("failed scrapers:", failed if failed else "none")

    # Fail the whole job only if every scraper failed
    if len(failed) == len(SCRAPERS):
        sys.exit(1)


if __name__ == "__main__":
    main()