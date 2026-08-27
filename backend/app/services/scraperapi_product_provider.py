import os
import re
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

from app.schemas.product import Product, Specification
from app.services.product_extractor import extract_asin
from app.services.title_spec_parser import extract_title_specifications


load_dotenv()


# ============================================================
# FALLBACK PRODUCT PROVIDER — ScraperAPI Amazon Product API
#
# Used only when the direct Amazon extraction in
# product_extractor.py raises AmazonBlockedError (Amazon served
# a homepage/redirect/bot-check page instead of the product
# page). This module fetches the same product from ScraperAPI's
# structured Amazon Product API instead of scraping Amazon
# directly, and maps the result onto the exact same Product
# schema so nothing downstream needs to know or care which
# provider supplied the data.
# ============================================================

SCRAPERAPI_ENDPOINT = "https://api.scraperapi.com/structured/amazon/product"


class ScraperAPIProviderError(Exception):
    """
    Raised when the ScraperAPI fallback can't be used: missing
    API key, no ASIN in the URL, the request itself failed, or
    ScraperAPI returned data that doesn't look like a real
    product (e.g. no title).
    """


# ============================================================
# MARKETPLACE RESOLUTION
#
# ScraperAPI needs separate `tld` and `country_code` params.
# This project's primary/tested scope is Amazon.in; the other
# entries just mirror the domains already allowed in
# schemas/product.py so a submitted non-.in Amazon URL doesn't
# silently get treated as India.
# ============================================================

_MARKETPLACE_BY_HOSTNAME_SUFFIX = {
    "amazon.in": ("in", "in"),
    "amazon.co.uk": ("co.uk", "gb"),
    "amazon.de": ("de", "de"),
    "amazon.ca": ("ca", "ca"),
    "amazon.com.au": ("com.au", "au"),
    "amazon.com": ("com", "us"),
}


def _resolve_marketplace(url):
    """
    Return (tld, country_code) for ScraperAPI based on the
    submitted URL's hostname. Defaults to India, since that is
    this project's supported marketplace (amzn.in short links
    also resolve to India).
    """

    hostname = (urlparse(url).hostname or "").lower()

    if hostname.startswith("www."):
        hostname = hostname[4:]

    for suffix, marketplace in _MARKETPLACE_BY_HOSTNAME_SUFFIX.items():

        if hostname == suffix or hostname.endswith("." + suffix):
            return marketplace

    return "in", "in"


# ============================================================
# SPECIFICATION NAME NORMALIZATION
#
# Used only to decide whether a structured spec pulled from the
# title/feature_bullets duplicates one ScraperAPI already gave
# us in `product_information`. Deliberately local to this
# module -- product_extractor.py/parser.py have their own
# alias tables and are left untouched.
# ============================================================

_SPEC_NAME_ALIASES = {
    "ram memory installed size": "ram",
    "ram memory installed": "ram",
    "ram memory": "ram",
    "memory storage capacity": "storage",
    "hard disk size": "storage",
    "connectivity technology": "connectivity",
    "wireless communication technologies": "connectivity",
    "operating system": "operating system",
    "battery power rating": "battery",
    "battery power": "battery",
    "item weight": "weight",
    "product dimensions": "dimensions",
}


def _normalize_spec_name(name):

    normalized = " ".join(str(name).lower().split())

    return _SPEC_NAME_ALIASES.get(normalized, normalized)


# ============================================================
# STRUCTURED SPEC EXTRACTION FROM FREE TEXT (feature_bullets)
#
# Reuses title_spec_parser.extract_title_specifications() for
# the fields it already covers (RAM, Storage, Battery,
# Charging, Display Size, Refresh Rate, Processor, Camera,
# Screen Protection, narrow IP-rating) instead of duplicating
# those regexes. The patterns below only add coverage for
# fields that parser doesn't attempt, tuned for the fuller
# prose found in feature bullets rather than terse titles.
# Category-agnostic on purpose: none of this is gated on
# product type, so it applies equally to phones, laptops, TVs,
# headphones, smartwatches, cameras, keyboards, mice, etc.
# ============================================================

# Most-specific-first: a smartwatch bullet like "Runs on Wear
# OS ... paired with Android 11" mentions both terms, but "Wear
# OS"/"Tizen"/"iPadOS" are the actual on-device OS while a
# co-mentioned "Android"/"iOS" there refers to the paired
# phone -- so specialized OS names must be tried before the
# generic ones they tend to appear alongside.
_OS_PATTERNS = [
    r"(Wear\s*OS(?:\s*\d+)?)",
    r"(Tizen(?:\s*OS)?)",
    r"(iPadOS\s*\d+(?:\.\d+)?)",
    r"(Android\s*\d+(?:\.\d+)?)",
    r"(iOS\s*\d+(?:\.\d+)?)",
    r"(Windows\s*1[01])",
    r"(macOS(?:\s*[A-Za-z]+)?)",
]

# Unlike OS, a single product commonly supports several of
# these simultaneously (e.g. "Bluetooth v5.3 ... with NFC"), so
# every group below is checked independently against the text
# rather than stopping at the first hit overall. Within a group,
# a plain "Bluetooth"/"Wi-Fi" mention (no version -- common in
# real listings, e.g. "Connectivity: Wi-Fi, Bluetooth, ...")
# is only used as a fallback when the versioned form isn't
# present, so "Bluetooth v5.3" is never reported as both
# "Bluetooth v5.3" and a redundant bare "Bluetooth".
_CONNECTIVITY_PATTERN_GROUPS = [
    [r"(Bluetooth\s*v?\d+(?:\.\d+)?)", r"\b(Bluetooth)\b"],
    [r"(Wi-?Fi\s*\d+)", r"\b(Wi-?Fi)\b"],
    [r"\b(NFC)\b"],
    [r"\b(USB\s*Type-?C|USB-?C)\b"],
    [r"\b(5G)\b"],
    [r"\b(4G(?:\s*LTE)?)\b"],
]

# Tried in priority order rather than as one leftmost-match
# alternation -- a text can mention both a generic marketing
# term and a precise pixel resolution (e.g. "4K Ultra HD
# Resolution (3840 x 2160)"), and the specific "WxH" figure is
# the more useful/confident value even when "4K" appears first
# in the string.
_RESOLUTION_PATTERNS = [
    r"(\d{3,4}\s*x\s*\d{3,4}(?:\s*(?:pixels?|resolution))?)",
    r"(\d{3,4}p\b)",
    r"(\b[248]K\b)",
]

# Two patterns instead of one "\d+\s*g" pattern -- a bare "g"
# unit right after a lone single digit would otherwise also
# match the "5G"/"4G" cellular-generation notation (e.g. "Test
# Phone 5G"). Spelled-out/kg units are unambiguous. The bare
# "g" abbreviation is only trusted when the number has 2+
# digits or a decimal point -- real weights are written that
# way ("180g", "33.3g"); "5G"/"4G" never are, so this still
# excludes them without requiring a space real listings often
# omit ("33.3g" has none).
_WEIGHT_PATTERNS = [
    r"(?<![\d.])(\d+(?:\.\d+)?)\s*(grams?|kilograms?|kg)\b",
    r"(?<![\d.])(\d{2,4}(?:\.\d+)?|\d\.\d+)\s*(g)\b(?!\w)",
]

_DIMENSIONS_PATTERN = (
    r"(\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?\s*"
    r"(?:mm|cm|inch(?:es)?|in))"
)

_WATER_DUST_PATTERN = r"\b(IPX?\d{1,2})\b"


def _first_match(patterns, text):

    for pattern in patterns:

        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(1).strip()

    return None


def _extract_weight(text):

    for pattern in _WEIGHT_PATTERNS:

        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return f"{match.group(1)} {match.group(2)}"

    return None


def _extract_connectivity(text):
    """
    Unlike other extended fields, connectivity technologies
    routinely co-occur in one sentence (e.g. "Bluetooth v5.3 ...
    with NFC", or "Connectivity: Wi-Fi, Bluetooth, ..."), so
    every group in _CONNECTIVITY_PATTERN_GROUPS is checked
    independently and matches are joined, instead of stopping at
    the first hit overall. Each group itself still stops at its
    own first hit, so a versioned match (e.g. "Bluetooth v5.3")
    is preferred over that same group's bare fallback
    ("Bluetooth") rather than reporting both.
    """

    values = []
    seen = set()

    for group in _CONNECTIVITY_PATTERN_GROUPS:

        value = _first_match(group, text)

        if not value:
            continue

        key = value.lower()

        if key in seen:
            continue

        seen.add(key)
        values.append(value)

    return ", ".join(values) if values else None


def _extract_extended_specs_from_text(text):
    """
    New, additive structured-field extraction (Operating
    System, Connectivity, Resolution, Weight, Dimensions,
    broader Water/Dust rating) that title_spec_parser.py does
    not attempt. Pure regex, no inference -- an unmatched field
    is simply omitted rather than guessed.
    """

    specs = []

    def add(name, value):

        if value:
            specs.append({"name": name, "value": value.strip()})

    add("Operating System", _first_match(_OS_PATTERNS, text))
    add("Connectivity", _extract_connectivity(text))

    add("Resolution", _first_match(_RESOLUTION_PATTERNS, text))

    add("Weight", _extract_weight(text))

    dimensions = re.search(_DIMENSIONS_PATTERN, text, re.IGNORECASE)

    if dimensions:
        add("Dimensions", dimensions.group(1))

    water_dust = re.search(_WATER_DUST_PATTERN, text, re.IGNORECASE)

    if water_dust:
        add("Water/Dust Resistance", water_dust.group(1).upper())

    return specs


# Fields where a product can genuinely have more than one
# distinct, simultaneously-true value (e.g. a phone supporting
# both "5G" and "Bluetooth v5.2") -- for these, a later match
# with a new value is appended rather than discarded as a
# duplicate. Every other field is treated as single-valued:
# first match wins (title, then bullets in order).
_MERGEABLE_SPEC_NAMES = {"connectivity"}


def _merge_connectivity_values(existing_value, new_value):
    """
    Merge a new comma-separated connectivity value into an
    existing one, token by token. A bare mention of a technology
    (e.g. "Bluetooth", found in the title) and a later versioned
    mention of the *same* technology (e.g. "Bluetooth v5.2",
    found in a bullet) are not two distinct technologies -- the
    more specific one replaces the bare one instead of both
    being listed. Only genuinely different technologies (e.g.
    "5G" and "Bluetooth v5.2") are appended side by side.
    """

    tokens = [
        token.strip()
        for token in existing_value.split(",")
        if token.strip()
    ]

    for candidate in (
        token.strip()
        for token in new_value.split(",")
        if token.strip()
    ):

        candidate_lower = candidate.lower()
        already_covered = False

        for index, token in enumerate(tokens):

            token_lower = token.lower()

            if token_lower == candidate_lower:
                already_covered = True
                break

            if token_lower.startswith(candidate_lower):
                # existing token is already this technology, and
                # at least as specific -- nothing to do.
                already_covered = True
                break

            if candidate_lower.startswith(token_lower):
                # candidate is a more specific form of the same
                # technology (e.g. "Bluetooth" -> "Bluetooth
                # v5.2") -- upgrade in place.
                tokens[index] = candidate
                already_covered = True
                break

        if not already_covered:
            tokens.append(candidate)

    return ", ".join(tokens)


def _extract_structured_specs(title, feature_bullets):
    """
    Run both the reused title-spec regexes and the new extended
    regexes over the product title and every feature bullet.
    Returns a de-duplicated (by normalized name) list. For most
    fields, first match wins -- title before bullets, bullets in
    their given order. Fields in _MERGEABLE_SPEC_NAMES instead
    accumulate distinct values (e.g. "5G, Bluetooth v5.2").
    """

    texts = [title] if title else []

    texts.extend(
        str(bullet).strip()
        for bullet in (feature_bullets or [])
        if str(bullet).strip()
    )

    collected = []
    seen = {}

    for text in texts:

        candidates = (
            extract_title_specifications(text)
            + _extract_extended_specs_from_text(text)
        )

        for spec in candidates:

            key = _normalize_spec_name(spec["name"])

            if key in seen:

                if key not in _MERGEABLE_SPEC_NAMES:
                    continue

                existing = collected[seen[key]]

                existing["value"] = _merge_connectivity_values(
                    existing["value"],
                    spec["value"],
                )

                continue

            seen[key] = len(collected)

            collected.append(dict(spec))

    return collected


# ============================================================
# SPECIFICATION MAPPING
# ============================================================

def _build_specifications(data, title=None):
    """
    Build the final List[Specification] for a ScraperAPI
    product:

    1. `product_information` -- mapped as before. This is the
       most authoritative source and is never overwritten by
       anything derived below.
    2. Structured fields (RAM, Storage, Battery, Charging,
       Display Size, Refresh Rate, Processor, Camera, Screen
       Protection, Water/Dust Resistance, Operating System,
       Connectivity, Resolution, Weight, Dimensions) parsed out
       of the title and feature_bullets, added only for names
       not already present from step 1.
    3. All feature bullets, unchanged, collapsed into one
       "Key Features" entry -- regardless of what was promoted
       to a structured field in step 2, so no bullet content is
       ever discarded.
    """

    specifications = []

    seen_names = set()

    product_information = data.get("product_information")

    if isinstance(product_information, dict):

        for raw_name, raw_value in product_information.items():

            value = str(raw_value).strip()

            if not value:
                continue

            name = raw_name.replace("_", " ").strip().title()

            key = _normalize_spec_name(name)

            if key in seen_names:
                continue

            seen_names.add(key)

            specifications.append(
                Specification(name=name, value=value)
            )

    feature_bullets = data.get("feature_bullets")

    structured_from_text = _extract_structured_specs(
        title,
        feature_bullets,
    )

    for spec in structured_from_text:

        key = _normalize_spec_name(spec["name"])

        if key in seen_names:
            continue

        seen_names.add(key)

        specifications.append(
            Specification(name=spec["name"], value=spec["value"])
        )

    if isinstance(feature_bullets, list) and feature_bullets:

        cleaned_bullets = [
            str(bullet).strip()
            for bullet in feature_bullets
            if str(bullet).strip()
        ]

        if cleaned_bullets and "key features" not in seen_names:

            specifications.append(
                Specification(
                    name="Key Features",
                    value=" | ".join(cleaned_bullets[:5]),
                )
            )

    return specifications


def _extract_price(data):
    """
    ScraperAPI omits price entirely for out-of-stock listings
    (confirmed during validation), so a missing price is a
    normal, expected outcome -- not an error. Checks a couple of
    plausible key shapes rather than assuming one exact field.
    """

    for key in ("price", "current_price", "list_price"):

        value = data.get(key)

        if value:
            return str(value).strip()

    pricing = data.get("pricing")

    if isinstance(pricing, dict):

        for key in ("price", "current_price"):

            value = pricing.get(key)

            if value:
                return str(value).strip()

    return None


def _extract_rating(data):

    rating = data.get("average_rating")

    try:
        return float(rating) if rating is not None else None
    except (TypeError, ValueError):
        return None


def _extract_reviews(data):

    reviews = data.get("total_reviews")

    try:
        return int(reviews) if reviews is not None else None
    except (TypeError, ValueError):
        return None


def _extract_image(data):

    images = data.get("images")

    if isinstance(images, list) and images:

        image = str(images[0]).strip()

        return image or None

    return None


def _extract_availability(data):

    availability = data.get("availability_status")

    if not availability:
        return None

    # Collapse the odd runs of whitespace ScraperAPI sometimes
    # returns in this field (confirmed during validation).
    return " ".join(str(availability).split())


# ============================================================
# MAIN FUNCTION
# ============================================================

def fetch_product_from_scraperapi(url: str, timeout: int = 60) -> Product:
    """
    Fallback product provider used when direct Amazon
    extraction raises AmazonBlockedError. Raises
    ScraperAPIProviderError if it can't produce a usable
    Product either.

    `timeout` defaults to 60s (unchanged from before) for this
    function's primary use as the main extraction fallback.
    Callers doing secondary/best-effort work against this same
    function (e.g. alternative_agent.py's candidate availability
    verification) can pass a shorter override so that work can't
    contribute an outsized share of total request latency.
    """

    api_key = os.getenv("SCRAPERAPI_KEY")

    if not api_key:

        raise ScraperAPIProviderError(
            "SCRAPERAPI_KEY is not configured; the ScraperAPI "
            "fallback is unavailable."
        )

    asin = extract_asin(url)

    if not asin:

        raise ScraperAPIProviderError(
            f"Could not extract an ASIN from URL: {url}"
        )

    tld, country_code = _resolve_marketplace(url)

    params = {
        "api_key": api_key,
        "asin": asin,
        "tld": tld,
        "country_code": country_code,
    }

    print("=" * 80)
    print("SCRAPERAPI FALLBACK PROVIDER")
    print("ASIN         :", asin)
    print("TLD          :", tld)
    print("COUNTRY CODE :", country_code)
    print("=" * 80)

    try:

        # NOTE: never log `response.url` or `params` here --
        # both contain the raw API key.
        response = requests.get(
            SCRAPERAPI_ENDPOINT,
            params=params,
            timeout=timeout,
        )

    except requests.exceptions.RequestException as error:

        raise ScraperAPIProviderError(
            f"ScraperAPI request failed: {error}"
        ) from error

    print("SCRAPERAPI STATUS CODE:", response.status_code)

    if response.status_code != 200:

        raise ScraperAPIProviderError(
            "ScraperAPI returned HTTP "
            f"{response.status_code} for ASIN {asin}."
        )

    try:
        data = response.json()
    except ValueError as error:

        raise ScraperAPIProviderError(
            f"ScraperAPI returned a non-JSON response: {error}"
        ) from error

    if not isinstance(data, dict):

        raise ScraperAPIProviderError(
            "ScraperAPI returned an unexpected response shape "
            f"for ASIN {asin}."
        )

    title = str(data.get("name") or "").strip()

    if not title:

        raise ScraperAPIProviderError(
            f"ScraperAPI returned no product title for ASIN "
            f"{asin} -- treating this as unusable product data."
        )

    brand = data.get("brand")
    brand = str(brand).strip() if brand else None

    product = Product(
        title=title,
        brand=brand,
        price=_extract_price(data),
        rating=_extract_rating(data),
        reviews=_extract_reviews(data),
        image=_extract_image(data),
        availability=_extract_availability(data),
        specifications=_build_specifications(data, title=title),
        review_texts=[],
    )

    print("SCRAPERAPI FALLBACK: usable product data received.")
    print("=" * 80)

    return product
