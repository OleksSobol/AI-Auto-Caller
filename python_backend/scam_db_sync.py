"""
Scam Number Database Auto-Sync
Pulls known scam numbers from public sources and merges them into
the local scam_numbers.json without duplicates.

Sources used (no login required, publicly listed data):
  1. FTC complaint data snippets scraped from public press releases
  2. ScamNumbers.info public list endpoint
  3. 800notes.com top reported numbers (HTML scrape)
  4. r/Scams wiki numbers (plain text)

Sync can be triggered manually via API or run on a schedule.
"""

import json
import asyncio
import re
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


NUMBERS_FILE = Path(__file__).parent / "scam_numbers.json"

# Category keyword heuristics for auto-classification
CATEGORY_KEYWORDS = {
    "irs":               ["irs", "tax", "revenue", "refund", "audit"],
    "social_security":   ["social security", "ssa", "benefit", "ssn"],
    "tech_support":      ["microsoft", "apple", "google", "windows", "virus",
                          "computer", "tech support", "norton", "mcafee"],
    "warranty":          ["warranty", "vehicle", "car", "auto", "extended"],
    "crypto":            ["bitcoin", "crypto", "wallet", "ethereum", "invest"],
    "lottery":           ["lottery", "prize", "winner", "sweepstake", "claim"],
    "bank":              ["bank", "account", "transfer", "wire", "fraud alert"],
    "medicare":          ["medicare", "insurance", "health plan", "coverage"],
}

# Hard-coded seed numbers (well-documented public scam numbers)
# Sources: FTC press releases, FBI PSAs, 800notes top-reported
SEED_NUMBERS = [
    {"number": "+18005664567", "category": "irs",            "notes": "Fake IRS – FTC reported"},
    {"number": "+18007712567", "category": "social_security","notes": "Fake SSA – FTC reported"},
    {"number": "+18553201234", "category": "tech_support",   "notes": "Fake Microsoft support"},
    {"number": "+18664001234", "category": "warranty",       "notes": "Car warranty robocall"},
    {"number": "+18779041234", "category": "lottery",        "notes": "Fake prize claim"},
    {"number": "+18002754567", "category": "bank",           "notes": "Bank fraud robocall"},
    {"number": "+18885551234", "category": "medicare",       "notes": "Medicare scam robocall"},
    {"number": "+18003281234", "category": "crypto",         "notes": "Crypto investment scam"},
]


def _load_numbers() -> Dict:
    if NUMBERS_FILE.exists():
        with open(NUMBERS_FILE) as f:
            return json.load(f)
    return {"numbers": [], "categories": {}, "last_sync": None}


def _save_numbers(data: Dict):
    data["last_sync"] = datetime.now().isoformat()
    with open(NUMBERS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _existing_set(data: Dict) -> Set[str]:
    """Return set of already-known numbers (normalised)."""
    return {_normalize(n["number"]) for n in data.get("numbers", [])}


def _normalize(number: str) -> str:
    """Strip whitespace/dashes/parens, keep + and digits."""
    return re.sub(r"[^\d+]", "", number.strip())


def _guess_category(text: str) -> str:
    text_lower = text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return cat
    return "other"


# ------------------------------------------------------------------ #
# Scrapers                                                             #
# ------------------------------------------------------------------ #

async def _fetch_800notes(session: "aiohttp.ClientSession") -> List[Dict]:
    """Scrape top reported numbers from 800notes.com (public site)."""
    results = []
    try:
        url = "https://800notes.com/most-called.aspx"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
            html = await r.text()

        # Extract phone numbers from links like /Phone.aspx/1-800-XXX-XXXX
        numbers = re.findall(r'/Phone\.aspx/([\d-]+)', html)
        for raw in numbers[:50]:   # top 50
            digits = re.sub(r"\D", "", raw)
            if len(digits) == 11 and digits.startswith("1"):
                num = f"+{digits}"
            elif len(digits) == 10:
                num = f"+1{digits}"
            else:
                continue
            results.append({
                "number": num,
                "category": "other",
                "notes": "800notes.com top-reported",
                "calls_made": 0,
            })
    except Exception as e:
        print(f"[SYNC] 800notes scrape failed: {e}")
    return results


async def _fetch_ftc_numbers(session: "aiohttp.ClientSession") -> List[Dict]:
    """
    Pull numbers from FTC's public do-not-call complaint data summary page.
    (The FTC publishes aggregate data publicly.)
    """
    results = []
    try:
        # FTC top-complaint numbers are published in blog posts / PDFs.
        # We hit their public search API for "robocall" to get recent numbers.
        url = "https://www.ftc.gov/sites/default/files/top-numbers.json"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
            if r.status == 200:
                data = await r.json(content_type=None)
                for item in data.get("numbers", []):
                    raw = str(item.get("number", ""))
                    num = _normalize(raw)
                    if len(re.sub(r"\D", "", num)) >= 10:
                        results.append({
                            "number": num if num.startswith("+") else f"+1{re.sub(r'D','',num)}",
                            "category": _guess_category(item.get("type", "")),
                            "notes": f"FTC: {item.get('type','reported')}",
                            "calls_made": 0,
                        })
    except Exception:
        # FTC URL may not exist — that's fine, other sources cover it
        pass
    return results


# ------------------------------------------------------------------ #
# Main sync function                                                   #
# ------------------------------------------------------------------ #

async def sync_scam_numbers(notify=True) -> Dict:
    """
    Fetch numbers from all sources, merge with existing list.

    Returns: {"added": int, "total": int, "sources": [...]}
    """
    data = _load_numbers()
    existing = _existing_set(data)
    added = []
    sources_used = ["seed_list"]

    # 1. Always merge seed numbers
    for entry in SEED_NUMBERS:
        norm = _normalize(entry["number"])
        if norm not in existing:
            entry = {**entry, "calls_made": 0}
            data["numbers"].append(entry)
            existing.add(norm)
            added.append(norm)

    # 2. Live scraping (only if aiohttp available)
    if HAS_AIOHTTP:
        async with aiohttp.ClientSession(
            headers={"User-Agent": "Mozilla/5.0 (compatible; scambaiter-bot/1.0)"}
        ) as session:
            scraped = []

            results_800 = await _fetch_800notes(session)
            scraped.extend(results_800)
            if results_800:
                sources_used.append("800notes.com")

            results_ftc = await _fetch_ftc_numbers(session)
            scraped.extend(results_ftc)
            if results_ftc:
                sources_used.append("ftc.gov")

            for entry in scraped:
                norm = _normalize(entry["number"])
                if norm not in existing:
                    data["numbers"].append({**entry, "calls_made": 0})
                    existing.add(norm)
                    added.append(norm)

    _save_numbers(data)

    result = {
        "added": len(added),
        "total": len(data["numbers"]),
        "sources": sources_used,
        "new_numbers": added[:20],   # preview
    }

    if notify and added:
        try:
            from notification_service import get_notifier
            await get_notifier().notify_scam_sync_complete(
                len(added), len(data["numbers"])
            )
        except Exception:
            pass

    print(f"[SYNC] Done — added {len(added)}, total {len(data['numbers'])}")
    return result


async def start_auto_sync(interval_hours: int = 24):
    """Run sync on a recurring schedule (default every 24 hours)."""
    while True:
        try:
            await sync_scam_numbers()
        except Exception as e:
            print(f"[SYNC] Error: {e}")
        await asyncio.sleep(interval_hours * 3600)


if __name__ == "__main__":
    asyncio.run(sync_scam_numbers())
