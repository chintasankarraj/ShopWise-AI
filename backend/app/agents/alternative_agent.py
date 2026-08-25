import os
import json
import re

from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.data.curated_alternatives import get_curated_alternatives


load_dotenv()


# ============================================================
# GEMINI CLIENT
# ============================================================

api_key = os.getenv("GEMINI_API_KEY")

client = None

if api_key:
    client = genai.Client(
        api_key=api_key
    )


# ============================================================
# CONSTANTS
# ============================================================

SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    )
}


TRUSTED_DOMAINS = {
    "amazon.in",
    "flipkart.com",
    "croma.com",
    "reliancedigital.in",
    "vijaysales.com",
    "samsung.com",
    "oneplus.in",
    "motorola.in",
    "mi.com",
    "poco.in",
    "realme.com",
    "iqoo.com",
    "vivo.com",
    "oppo.com",
    "nothing.tech",
    "store.google.com",
}


RETAILER_DOMAINS = {
    "amazon.in",
    "flipkart.com",
    "croma.com",
    "reliancedigital.in",
    "vijaysales.com",
}


# ============================================================
# HELPERS
# ============================================================

def _serialize_specs(specs):
    """
    Convert Pydantic specification objects into dictionaries.
    """

    result = []

    for spec in specs or []:

        if hasattr(spec, "model_dump"):

            result.append(
                spec.model_dump()
            )

        elif isinstance(spec, dict):

            result.append(
                spec
            )

        else:

            result.append(
                {
                    "name": getattr(
                        spec,
                        "name",
                        ""
                    ),
                    "value": getattr(
                        spec,
                        "value",
                        ""
                    ),
                }
            )

    return result


def _clean_json(text):
    """
    Remove markdown fences from Gemini JSON.
    """

    if not text:
        return ""

    text = text.strip()

    if text.startswith("```json"):

        text = text[7:]

    elif text.startswith("```"):

        text = text[3:]

    if text.endswith("```"):

        text = text[:-3]

    return text.strip()


def _valid_url(url):
    """
    Basic URL validation.
    """

    if not url:
        return False

    try:

        parsed = urlparse(
            url.strip()
        )

        return (
            parsed.scheme in {
                "http",
                "https",
            }
            and bool(parsed.netloc)
        )

    except Exception:

        return False


def _domain(url):
    """
    Extract normalized domain.
    """

    try:

        hostname = urlparse(
            url
        ).hostname

        if not hostname:
            return ""

        hostname = hostname.lower()

        if hostname.startswith("www."):

            hostname = hostname[4:]

        return hostname

    except Exception:

        return ""


def _is_trusted_domain(url):
    """
    Check whether URL belongs to a known retailer
    or manufacturer.
    """

    domain = _domain(
        url
    )

    return any(
        domain == trusted
        or domain.endswith(
            "." + trusted
        )
        for trusted in TRUSTED_DOMAINS
    )


def _is_retailer_domain(url):
    """
    Check whether URL belongs to a major Indian retailer.
    """

    domain = _domain(
        url
    )

    return any(
        domain == retailer
        or domain.endswith(
            "." + retailer
        )
        for retailer in RETAILER_DOMAINS
    )


def _normalize_name(name):
    """
    Normalize product names for duplicate checking.
    """

    name = re.sub(
        r"[^a-z0-9]+",
        " ",
        str(name).lower()
    )

    return " ".join(
        name.split()
    ).strip()


def _looks_like_search_page(url):
    """
    Reject obvious search/listing URLs.
    """

    lowered = (
        url or ""
    ).lower()

    blocked_patterns = [
        "/s?",
        "/search",
        "/search?",
        "/search/",
        "/srch",
        "/searchresult",
        "?q=",
        "?query=",
        "/gp/bestsellers",
    ]

    return any(
        pattern in lowered
        for pattern in blocked_patterns
    )


def _is_probably_product_page(url):
    """
    Basic product-page heuristic.
    """

    if not _valid_url(
        url
    ):

        return False

    if _looks_like_search_page(
        url
    ):

        return False

    return True


# ============================================================
# PRODUCT CATEGORY
# ============================================================

def _detect_category(product):
    """
    Determine a broad product category.
    """

    title = (
        product.title or ""
    ).lower()

    category = getattr(
        product,
        "category",
        None
    )

    if category:

        return str(
            category
        ).lower()

    if any(
        word in title
        for word in [
            "phone",
            "smartphone",
            "mobile",
            "galaxy",
            "iphone",
            "redmi",
            "pixel",
            "oneplus",
            "poco",
            "motorola",
            "realme",
            "vivo",
            "oppo",
            "iqoo",
        ]
    ):

        return "smartphone"

    if any(
        word in title
        for word in [
            "laptop",
            "notebook",
            "macbook",
            "chromebook",
        ]
    ):

        return "laptop"

    if any(
        word in title
        for word in [
            "tablet",
            "ipad",
        ]
    ):

        return "tablet"

    if any(
        word in title
        for word in [
            "headphone",
            "earbuds",
            "earphone",
        ]
    ):

        return "audio"

    return "electronics"


# ============================================================
# SEARCH QUERY BUILDER
# ============================================================

def _build_search_queries(
    product,
    specification_data
):
    """
    Build current-product discovery queries.
    """

    category = _detect_category(
        product
    )

    title = (
        product.title or ""
    )

    clean_title = re.sub(
        r"\|.*$",
        "",
        title
    ).strip()

    clean_title = re.sub(
        r": Amazon.*$",
        "",
        clean_title,
        flags=re.IGNORECASE
    ).strip()

    queries = []

    if category == "smartphone":

        queries.extend(
            [
                f"{clean_title} alternatives India 2026",
                f"best alternatives to {clean_title} India",
                f"best smartphones around {product.price or ''} India 2026",
            ]
        )

    elif category == "laptop":

        queries.extend(
            [
                f"{clean_title} alternatives India 2026",
                f"best laptops around {product.price or ''} India 2026",
                f"laptop alternatives {clean_title} India",
            ]
        )

    else:

        queries.extend(
            [
                f"{clean_title} alternatives India 2026",
                f"best alternatives to {clean_title} India",
                f"{category} alternatives India 2026",
            ]
        )

    return queries


# ============================================================
# DUCKDUCKGO WEB SEARCH
# ============================================================

def _search_web(query):
    """
    Search the public web using DuckDuckGo HTML.

    DuckDuckGo may occasionally return HTTP 202 while still
    providing valid search-result HTML, so we intentionally
    parse the response regardless of the status code.
    """

    url = (
        "https://html.duckduckgo.com/html/?q="
        + quote(query)
    )

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/151.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8"
                ),
                "Accept-Language": "en-IN,en;q=0.9",
            },
            timeout=15,
        )

        print(
            "DuckDuckGo HTTP status:",
            response.status_code
        )

        print(
            "DuckDuckGo response length:",
            len(response.text)
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        raw_results = soup.select(
            ".result"
        )

        print(
            "DuckDuckGo raw result blocks:",
            len(raw_results)
        )

        # ----------------------------------------------------
        # Fallback selector
        # ----------------------------------------------------

        if not raw_results:

            links = soup.select(
                ".result__a"
            )

            print(
                "Fallback result links:",
                len(links)
            )

            results = []

            for link in links:

                href = link.get(
                    "href",
                    ""
                ).strip()

                name = link.get_text(
                    " ",
                    strip=True
                )

                if not _valid_url(
                    href
                ):

                    continue

                if not _is_probably_product_page(
                    href
                ):

                    continue

                results.append(
                    {
                        "name": name,
                        "url": href,
                        "description": "",
                    }
                )

            print(
                "DuckDuckGo usable results:",
                len(results)
            )

            return results

        # ----------------------------------------------------
        # Normal result parsing
        # ----------------------------------------------------

        results = []

        for result in raw_results:

            link = result.select_one(
                ".result__a"
            )

            snippet = result.select_one(
                ".result__snippet"
            )

            if not link:

                continue

            href = link.get(
                "href",
                ""
            ).strip()

            name = link.get_text(
                " ",
                strip=True
            )

            description = (
                snippet.get_text(
                    " ",
                    strip=True
                )
                if snippet
                else ""
            )

            if not _valid_url(
                href
            ):

                continue

            if not _is_probably_product_page(
                href
            ):

                continue

            results.append(
                {
                    "name": name,
                    "url": href,
                    "description": description,
                }
            )

        print(
            "DuckDuckGo usable results:",
            len(results)
        )

        return results

    except Exception as error:

        print(
            "Web search failed:",
            str(error)
        )

        return []
# ============================================================
# CANDIDATE NAME EXTRACTION
# ============================================================

def _extract_candidate_name(
    result
):
    """
    Turn a search result title into a useful product name.
    """

    name = (
        result.get(
            "name",
            ""
        )
        or ""
    ).strip()

    name = re.sub(
        r"\s*[-|]\s*Amazon\.in.*$",
        "",
        name,
        flags=re.IGNORECASE
    )

    name = re.sub(
        r"\s*[-|]\s*Flipkart.*$",
        "",
        name,
        flags=re.IGNORECASE
    )

    return name.strip()


# ============================================================
# SAME PRODUCT DETECTION
# ============================================================

def _looks_like_same_product(
    candidate_name,
    current_title
):
    """
    Prevent recommending the exact same product.
    """

    candidate = _normalize_name(
        candidate_name
    )

    current = _normalize_name(
        current_title
    )

    if not candidate or not current:

        return False

    if candidate == current:

        return True

    current_tokens = set(
        current.split()
    )

    candidate_tokens = set(
        candidate.split()
    )

    important_tokens = {
        token
        for token in current_tokens
        if len(token) >= 4
    }

    if not important_tokens:

        return False

    overlap = (
        important_tokens
        & candidate_tokens
    )

    return (
        len(overlap)
        >= max(
            3,
            int(
                len(important_tokens)
                * 0.65
            )
        )
    )


# ============================================================
# RANK SEARCH RESULTS
# ============================================================

def _rank_search_results(
    results,
    product
):
    """
    Rank current web results.
    """

    ranked = []

    rejected_same = 0
    rejected_empty = 0

    for result in results:

        url = result.get(
            "url",
            ""
        )

        name = _extract_candidate_name(
            result
        )

        if not name:

            rejected_empty += 1
            continue

        if _looks_like_same_product(
            name,
            product.title or ""
        ):

            rejected_same += 1
            continue

        score = 0

        if _is_retailer_domain(
            url
        ):

            score += 50

        elif _is_trusted_domain(
            url
        ):

            score += 40

        if _is_probably_product_page(
            url
        ):

            score += 20

        description = (
            result.get(
                "description",
                ""
            )
            or ""
        ).lower()

        for keyword in [
            "buy",
            "price",
            "in stock",
            "available",
            "add to cart",
            "₹",
        ]:

            if keyword in description:

                score += 3

        ranked.append(
            {
                "name": name,
                "url": url,
                "description": description,
                "score": score,
            }
        )

    ranked.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    print(
        "Rejected as same product:",
        rejected_same
    )

    print(
        "Rejected because name was empty:",
        rejected_empty
    )

    return ranked


# ============================================================
# GEMINI ALTERNATIVES
# ============================================================

def _find_with_gemini(
    product,
    specification_data
):
    """
    Primary alternative-generation method.

    Uses Gemini + Google Search grounding when available.
    """

    if client is None:

        return []

    prompt = f"""
You are ShopWise AI's current-product research agent.

Find realistic CURRENT alternatives in India for the
following product.

PRODUCT
=======

Name:
{product.title}

Brand:
{product.brand}

Current Price:
{product.price}

Category:
{_detect_category(product)}

Specifications:
{json.dumps(
    specification_data,
    indent=2,
    ensure_ascii=False
)}

RULES
=====

1. Search the current web before answering.

2. Return only real products.

3. Prefer products currently sold in India in 2026.

4. Prefer official manufacturer pages or major Indian
   retailers.

5. Do not recommend discontinued products when current
   alternatives exist.

6. Do not invent product names.

7. Do not invent URLs.

8. Do not invent exact prices.

9. If price cannot be verified, return:
   "Price unavailable"

10. Every alternative must have a real product page URL.

11. Do not return a search-results URL.

12. Do not return the exact product being analyzed.

13. Return up to 3 alternatives.

14. Return fewer than 3 if reliable alternatives cannot
    be verified.

15. Explain the specific advantage over the current product.

16. Do not use generic statements such as "better overall".

17. Keep reasons short.

OUTPUT JSON ONLY:

{{
    "alternatives": [
        {{
            "name": "Product name",
            "price": "Price unavailable",
            "url": "https://real-product-page",
            "availability": "Currently listed",
            "reason": "Specific advantage over current product"
        }}
    ]
}}
"""

    try:

        grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )

        config = types.GenerateContentConfig(
            tools=[
                grounding_tool
            ],
            response_mime_type="application/json",
        )

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=config,
        )

        print(
            "\n================ GEMINI ALTERNATIVE RESPONSE ================\n"
        )

        print(
            response.text
        )

        print(
            "\n================ GROUNDING METADATA ================\n"
        )

        try:

            print(
                response.candidates[
                    0
                ].grounding_metadata
            )

        except Exception as error:

            print(
                "No grounding metadata:",
                error
            )

        print(
            "\n===============================================================\n"
        )

        text = _clean_json(
            response.text
        )

        data = json.loads(
            text
        )

        alternatives = data.get(
            "alternatives",
            []
        )

        if not isinstance(
            alternatives,
            list
        ):

            return []

        return alternatives

    except Exception as error:

        print(
            "Gemini alternative search unavailable:",
            str(error)
        )

        return []


# ============================================================
# VALIDATE GEMINI RESULTS
# ============================================================

def _validate_alternatives(
    alternatives,
    product
):
    """
    Validate and normalize alternative objects.
    """

    valid = []

    seen = set()

    current_title = (
        product.title or ""
    )

    for item in alternatives:

        if not isinstance(
            item,
            dict
        ):

            continue

        name = str(
            item.get(
                "name",
                ""
            )
        ).strip()

        price = str(
            item.get(
                "price",
                "Price unavailable"
            )
        ).strip()

        url = str(
            item.get(
                "url",
                ""
            )
        ).strip()

        availability = str(
            item.get(
                "availability",
                "Currently listed"
            )
        ).strip()

        reason = str(
            item.get(
                "reason",
                ""
            )
        ).strip()

        if not name:

            continue

        if not reason:

            continue

        if _looks_like_same_product(
            name,
            current_title
        ):

            continue

        if not _valid_url(
            url
        ):

            continue

        if _looks_like_search_page(
            url
        ):

            continue

        key = _normalize_name(
            name
        )

        if key in seen:

            continue

        seen.add(
            key
        )

        valid.append(
            {
                "name": name,
                "price": (
                    price
                    or "Price unavailable"
                ),
                "url": url,
                "availability": (
                    availability
                    or "Currently listed"
                ),
                "reason": reason,
            }
        )

    return valid[:3]


# ============================================================
# FREE WEB SEARCH FALLBACK
# ============================================================

def _find_with_web_fallback(
    product,
    specification_data
):
    """
    Find current alternatives without Gemini.

    Uses DuckDuckGo as a free fallback.
    """

    queries = _build_search_queries(
        product,
        specification_data
    )

    all_results = []

    for query in queries:

        print(
            "Alternative fallback search:",
            query
        )

        results = _search_web(
            query
        )

        print(
            "Search results returned:",
            len(results)
        )

        all_results.extend(
            results
        )

        if len(all_results) >= 12:

            break

    print(
        "Total fallback search results:",
        len(all_results)
    )

    ranked = _rank_search_results(
        all_results,
        product
    )

    print(
        "Ranked fallback results:",
        len(ranked)
    )

    for item in ranked[:5]:

        print(
            "Candidate:",
            item["name"],
            "|",
            item["url"],
            "| score:",
            item["score"]
        )

    alternatives = []

    seen = set()

    for item in ranked:

        name = item[
            "name"
        ]

        url = item[
            "url"
        ]

        key = _normalize_name(
            name
        )

        if key in seen:

            continue

        seen.add(
            key
        )

        alternatives.append(
            {
                "name": name,
                "price": "Price unavailable",
                "url": url,
                "availability": "Current listing found",
                "reason": (
                    "A current product listing was found "
                    "for comparison. Verify the latest "
                    "price and specifications before purchase."
                ),
            }
        )

        if len(alternatives) >= 3:

            break

    return alternatives


# ============================================================
# MAIN FUNCTION
# ============================================================

def find_alternatives(
    product,
    specs
):
    """
    Find up to 3 current alternatives.

    Strategy:

    1. Try Gemini + Google Search grounding.
    2. Validate Gemini results.
    3. If Gemini fails or quota is exhausted,
       use free DuckDuckGo fallback.
    4. If the web fallback also returns nothing (e.g.
       DuckDuckGo anti-bot-gated the request), fall back to
       a small curated, clearly-labeled local dataset so the
       feature is never silently empty.
    5. Never fabricate prices or claim unverified
       availability.
    """

    specification_data = _serialize_specs(
        specs
    )

    print(
        "\n============================================================"
    )

    print(
        "SHOPWISE ALTERNATIVE AGENT"
    )

    print(
        "============================================================"
    )

    # ========================================================
    # PRIMARY: GEMINI + GOOGLE SEARCH
    # ========================================================

    gemini_results = _find_with_gemini(
        product,
        specification_data
    )

    valid_gemini_results = _validate_alternatives(
        gemini_results,
        product
    )

    if valid_gemini_results:

        print(
            "Using Gemini-grounded alternatives:",
            len(valid_gemini_results)
        )

        return {
            "alternatives":
                valid_gemini_results[:3]
        }

    # ========================================================
    # FALLBACK: FREE WEB SEARCH
    # ========================================================

    print(
        "Gemini alternatives unavailable."
    )

    print(
        "Using web-search fallback."
    )

    fallback_results = _find_with_web_fallback(
        product,
        specification_data
    )

    if fallback_results:

        print(
            "Fallback alternatives found:",
            len(fallback_results)
        )

        print(
            "============================================================\n"
        )

        return {
            "alternatives":
                fallback_results[:3]
        }

    # ========================================================
    # FINAL FALLBACK: CURATED LOCAL DATASET
    # ========================================================

    print(
        "Web-search fallback unavailable."
    )

    print(
        "Using curated local dataset."
    )

    curated_results = get_curated_alternatives(
        product,
        category=_detect_category(product)
    )

    if curated_results:

        print(
            "Curated alternatives found:",
            len(curated_results)
        )

    else:

        print(
            "No curated alternatives available "
            "for this category."
        )

    print(
        "============================================================\n"
    )

    return {
        "alternatives":
            curated_results[:3]
    }