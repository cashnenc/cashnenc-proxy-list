"""
Orchestrator that runs scraping, validation, formatting and writes outputs to ./dist
Improved logging and safety checks before writing outputs.
"""

import asyncio
import logging
from pathlib import Path

from scraper import fetch_proxies
from validator import validate_proxies
from formatter import to_json, to_txt, to_csv


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DIST = Path("dist")
DIST.mkdir(exist_ok=True)


async def run_once():
    proxies = await fetch_proxies()
    logger.info("Scraped %d proxies", len(proxies))

    validated = await validate_proxies(proxies)
    good = [p for p in validated if p.get("ok")]
    logger.info("Validated %d working proxies", len(good))

    # write outputs (always write JSON for transparency, other formats only if there are working proxies)
    (DIST / "proxies.json").write_text(to_json(validated), encoding="utf-8")
    if good:
        (DIST / "proxies.txt").write_text(to_txt(validated), encoding="utf-8")
        (DIST / "proxies.csv").write_text(to_csv(validated), encoding="utf-8")
    else:
        # remove stale TXT/CSV if present
        for p in ("proxies.txt", "proxies.csv"):
            fp = DIST / p
            if fp.exists():
                fp.unlink()


if __name__ == "__main__":
    asyncio.run(run_once())
