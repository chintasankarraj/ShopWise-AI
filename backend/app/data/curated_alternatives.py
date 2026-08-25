import re

from urllib.parse import quote


# ============================================================
# CURATED FALLBACK ALTERNATIVES
#
# This is the LAST-RESORT tier used by
# app/agents/alternative_agent.py, only when both the Gemini
# grounded search and the DuckDuckGo web-search fallback
# return zero usable results (e.g. Gemini quota exhausted AND
# DuckDuckGo anti-bot-gated the request -- a combination that
# happens routinely from a cloud/datacenter deploy IP).
#
# These entries are NOT live-verified listings:
#   - Prices are intentionally NOT included/guessed. The
#     "price" field is always "Price unavailable".
#   - "availability" and "reason" are explicitly labeled as a
#     curated suggestion, not a confirmed live listing.
#   - "url" points to an Amazon.in SEARCH results page for the
#     model name (not a specific product URL we can't verify),
#     so the "View Alternative" link always resolves to real,
#     current listings the user can check themselves.
#
# This dataset is free (no paid API), static, and will drift
# out of date as models age out of availability in India --
# it should be refreshed periodically. It only covers the
# smartphone category, matching the current MVP scope.
# ============================================================

CURATED_LABEL = "Curated suggestion"

_SMARTPHONE_TIERS = {
    "budget": [
        {
            "name": "Redmi Note 13 5G",
            "reason": (
                "Popular budget 5G alternative worth "
                "comparing on camera and battery."
            ),
        },
        {
            "name": "realme 12x 5G",
            "reason": (
                "Popular budget 5G alternative worth "
                "comparing on display and performance."
            ),
        },
        {
            "name": "POCO M6 Pro 5G",
            "reason": (
                "Popular budget 5G alternative worth "
                "comparing on processor and storage options."
            ),
        },
    ],
    "mid": [
        {
            "name": "OnePlus Nord 4",
            "reason": (
                "Popular mid-range alternative worth "
                "comparing on build quality and performance."
            ),
        },
        {
            "name": "Samsung Galaxy S24 FE",
            "reason": (
                "Popular mid-range alternative worth "
                "comparing on camera and software support."
            ),
        },
        {
            "name": "iQOO Neo 9 Pro",
            "reason": (
                "Popular mid-range alternative worth "
                "comparing on processor and charging speed."
            ),
        },
    ],
    "flagship": [
        {
            "name": "OnePlus 12",
            "reason": (
                "Popular flagship alternative worth "
                "comparing on display and charging speed."
            ),
        },
        {
            "name": "Samsung Galaxy S24 Ultra",
            "reason": (
                "Popular flagship alternative worth "
                "comparing on camera system and display."
            ),
        },
        {
            "name": "iPhone 15",
            "reason": (
                "Popular flagship alternative worth "
                "comparing on ecosystem and long-term "
                "software support."
            ),
        },
    ],
}


# ============================================================
# HELPERS
# ============================================================

def _normalize_name(name):

    name = re.sub(
        r"[^a-z0-9]+",
        " ",
        str(name).lower()
    )

    return " ".join(
        name.split()
    ).strip()


def _extract_price_number(price):

    if not price:
        return None

    digits = re.sub(
        r"[^\d.]",
        "",
        str(price)
    )

    if not digits:
        return None

    try:
        return float(digits)
    except ValueError:
        return None


def _pick_tier(product):
    """
    Rough price-band selection so the curated suggestions are
    at least in the right ballpark. Defaults to "mid" when the
    current price could not be parsed.
    """

    price_value = _extract_price_number(
        getattr(product, "price", None)
    )

    if price_value is None:
        return "mid"

    if price_value < 20000:
        return "budget"

    if price_value < 45000:
        return "mid"

    return "flagship"


def _is_same_product(candidate_name, current_title):

    candidate = _normalize_name(candidate_name)
    current = _normalize_name(current_title)

    if not candidate or not current:
        return False

    return candidate == current or candidate in current


# ============================================================
# MAIN
# ============================================================

def get_curated_alternatives(product, category="smartphone"):
    """
    Final, always-available fallback tier. Returns up to 3
    curated (not live-verified) alternatives, or an empty list
    if the category isn't covered by the curated dataset yet.
    """

    if category != "smartphone":
        return []

    tier = _pick_tier(product)

    entries = _SMARTPHONE_TIERS.get(
        tier,
        _SMARTPHONE_TIERS["mid"]
    )

    current_title = getattr(product, "title", "") or ""

    alternatives = []

    for entry in entries:

        name = entry["name"]

        if _is_same_product(name, current_title):
            continue

        search_url = (
            "https://www.amazon.in/s?k="
            + quote(name)
        )

        alternatives.append(
            {
                "name": name,
                "price": "Price unavailable",
                "url": search_url,
                "availability": (
                    f"{CURATED_LABEL} — not live-verified, "
                    "check current listing"
                ),
                "reason": (
                    f"{CURATED_LABEL}: {entry['reason']} "
                    "Verify current specs, price, and "
                    "availability before purchase."
                ),
            }
        )

        if len(alternatives) >= 3:
            break

    return alternatives
