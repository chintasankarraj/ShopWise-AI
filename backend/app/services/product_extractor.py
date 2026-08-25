import sys
import time

import requests
from bs4 import BeautifulSoup
import re
from app.schemas.product import Product
from app.services.parser import extract_specifications
from app.services.title_spec_parser import extract_title_specifications
from app.services.review_parser import extract_reviews
import json


# ============================================================
# STDOUT ENCODING
#
# Scraped Amazon HTML frequently contains non-ASCII characters
# (e.g. U+200E left-to-right marks, trademark/registered
# symbols, non-Latin brand names). The debug print()s below
# write that text to stdout, which on Windows defaults to the
# cp1252 console codepage and raises UnicodeEncodeError on
# those characters, crashing the request. Force UTF-8 output
# with a safe fallback instead of dropping the debug logging.
# ============================================================

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ============================================================
# HTTP HEADERS
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Encoding": "gzip, deflate, br",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Connection": "keep-alive",
    "Referer": "https://www.google.com/",
}

# Biases Amazon toward the India marketplace/currency regardless
# of the requesting server's own IP geography, since a server
# hosted outside India can otherwise be shown a country-selector
# / marketplace-redirect page instead of the actual product page.
COOKIES = {
    "i18n-prefs": "INR",
}


# ============================================================
# NON-PRODUCT RESPONSE DETECTION
#
# Amazon can return HTTP 200 for a page that isn't the product
# page at all -- a bare marketplace homepage, a country/locale
# redirect splash, or a bot-check/consent interstitial. Without
# detecting this, extract_product() would silently return a
# "successful" Product with a fake title and no real data.
# ============================================================

class AmazonBlockedError(Exception):
    """
    Raised when Amazon returned a non-product response (e.g. a
    homepage, marketplace/locale redirect, or bot-check page)
    instead of the requested product page.
    """


_BLOCK_PAGE_TEXT_MARKERS = [
    "api-services-support@amazon.com",
    "type the characters you see in this image",
    "enter the characters you see below",
    "to discuss automated access to amazon data",
    "sorry, we just need to make sure you're not a robot",
]

# Matches a bare marketplace title with nothing else in it,
# e.g. "Amazon.in", "Amazon.com", "Amazon.co.uk" -- exactly
# what a homepage/locale-redirect page's <title> looks like.
# A real product page's title is never just the site name.
_BARE_MARKETPLACE_TITLE = re.compile(
    r"^amazon(\.[a-z]{2,3}){1,2}$",
    re.IGNORECASE,
)


def _looks_like_blocked_response(title, html):
    """
    Fast check used right after fetching: does this response
    look like a non-product Amazon page?
    """

    normalized_title = (title or "").strip()

    if not normalized_title:
        return True

    if _BARE_MARKETPLACE_TITLE.match(normalized_title):
        return True

    html_lower = (html or "").lower()

    if any(
        marker in html_lower
        for marker in _BLOCK_PAGE_TEXT_MARKERS
    ):
        return True

    return False


def _fetch_amazon_page(url, max_attempts=2):
    """
    Fetch an Amazon URL, retrying once if the response looks
    like a non-product page (homepage/redirect/bot-check)
    rather than a genuine fetch failure. Genuine HTTP errors
    still raise via response.raise_for_status() and are left
    for the caller to handle as a normal request failure.
    """

    last_title = None

    for attempt in range(1, max_attempts + 1):

        response = requests.get(
            url,
            headers=HEADERS,
            cookies=COOKIES,
            timeout=15,
            allow_redirects=True,
        )

        print("=" * 80)
        print("FETCH ATTEMPT :", attempt)
        print("REQUESTED URL :", url)
        print("FINAL URL     :", response.url)
        print("STATUS CODE   :", response.status_code)
        print("RESPONSE SIZE :", len(response.text))
        print(
            "CONTENT TYPE  :",
            response.headers.get("content-type"),
        )
        print("=" * 80)

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        title = (
            soup.title.string.strip()
            if soup.title and soup.title.string
            else ""
        )

        if not _looks_like_blocked_response(
            title,
            response.text,
        ):
            return response, soup, title

        last_title = title

        print(
            f"Attempt {attempt}: response looks like a "
            f"non-product Amazon page (title={title!r})."
        )

        if attempt < max_attempts:
            time.sleep(1)

    raise AmazonBlockedError(
        f"Amazon returned a non-product response "
        f"(title={last_title!r}) after {max_attempts} "
        "attempt(s). This usually means Amazon blocked, "
        "redirected, or geo-gated the request from this "
        "server's IP rather than serving the actual "
        "product page."
    )


# ============================================================
# ASIN EXTRACTION
# ============================================================

def extract_asin(url: str):
    """
    Extract Amazon ASIN from a product URL.
    """

    patterns = [
        r"/dp/([A-Z0-9]{10})",
        r"/gp/product/([A-Z0-9]{10})",
        r"/product/([A-Z0-9]{10})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            url,
            re.IGNORECASE
        )

        if match:
            return match.group(1).upper()

    return None


# ============================================================
# REVIEW METADATA EXTRACTION
# ============================================================

def extract_review_metadata(
    soup: BeautifulSoup,
    html: str,
):
    """
    Extract product rating and review count.

    Extraction order:

    1. JSON-LD
    2. Visible Amazon HTML
    3. Amazon embedded page data:
       averageCustomerReviews
    """

    rating = None
    reviews = None

    # ========================================================
    # 1. JSON-LD
    # ========================================================

    for script in soup.select(
        'script[type="application/ld+json"]'
    ):

        try:

            raw = (
                script.string
                or script.get_text()
            )

            if not raw.strip():
                continue

            data = json.loads(raw)

            items = (
                data
                if isinstance(data, list)
                else [data]
            )

            for item in items:

                if not isinstance(item, dict):
                    continue

                aggregate = item.get(
                    "aggregateRating"
                )

                if not isinstance(
                    aggregate,
                    dict
                ):
                    continue

                rating_value = aggregate.get(
                    "ratingValue"
                )

                review_count = (
                    aggregate.get(
                        "reviewCount"
                    )
                    or aggregate.get(
                        "ratingCount"
                    )
                )

                if rating_value is not None:

                    try:

                        rating = float(
                            rating_value
                        )

                    except (
                        ValueError,
                        TypeError
                    ):
                        pass

                if review_count is not None:

                    try:

                        reviews = int(
                            str(review_count)
                            .replace(",", "")
                            .strip()
                        )

                    except (
                        ValueError,
                        TypeError
                    ):
                        pass

                if (
                    rating is not None
                    or reviews is not None
                ):

                    print(
                        "REVIEW METADATA SOURCE: JSON-LD"
                    )

                    return rating, reviews

        except (
            json.JSONDecodeError,
            TypeError
        ):
            continue

    # ========================================================
    # 2. Visible Amazon rating
    # ========================================================

    rating_selectors = [
        "#acrPopover",
        "[data-hook='rating-out-of-text']",
        "span.a-icon-alt",
    ]

    for selector in rating_selectors:

        tag = soup.select_one(
            selector
        )

        if not tag:
            continue

        text = tag.get_text(
            " ",
            strip=True
        )

        match = re.search(
            r"(\d+(?:\.\d+)?)\s*out of 5",
            text,
            re.IGNORECASE
        )

        if match:

            try:

                rating = float(
                    match.group(1)
                )

                break

            except ValueError:
                pass

    # ========================================================
    # 3. Visible Amazon review count
    # ========================================================

    review_count_selectors = [
        "#acrCustomerReviewText",
        "[data-hook='total-review-count']",
        "#averageCustomerReviews .a-size-base",
    ]

    for selector in review_count_selectors:

        tag = soup.select_one(
            selector
        )

        if not tag:
            continue

        text = tag.get_text(
            " ",
            strip=True
        )

        match = re.search(
            r"([\d,]+)\s+(?:customer\s+)?reviews?",
            text,
            re.IGNORECASE
        )

        if match:

            try:

                reviews = int(
                    match.group(1)
                    .replace(",", "")
                )

                break

            except ValueError:
                pass

    # ========================================================
    # 4. AMAZON EMBEDDED DATA
    # ========================================================
    #
    # Your page contains:
    #
    # "averageCustomerReviews":{
    #     "reviewCount":296,
    #     "fullStarCount":4,
    #     "displayString":"4.0 out of 5 stars",
    #     "value":4,
    #     "hasHalfStar":false
    # }
    #
    # ========================================================

    if (
        rating is None
        or reviews is None
    ):

        # ----------------------------------------------------
        # First try the escaped Amazon format
        # ----------------------------------------------------

        escaped_pattern = re.compile(
            r'averageCustomerReviews'
            r'.{0,1000}?'
            r'reviewCount'
            r'\\?["&;]*\s*:\s*'
            r'(\d+)'
            r'.{0,1000}?'
            r'displayString'
            r'\\?["&;]*\s*:\s*'
            r'\\?["&;]*'
            r'(\d+(?:\.\d+)?)'
            r'\s+out\s+of\s+5\s+stars',
            re.IGNORECASE | re.DOTALL
        )

        match = escaped_pattern.search(
            html
        )

        if match:

            try:

                if reviews is None:

                    reviews = int(
                        match.group(1)
                    )

                if rating is None:

                    rating = float(
                        match.group(2)
                    )

                print(
                    "REVIEW METADATA SOURCE: "
                    "AMAZON EMBEDDED DATA"
                )

            except (
                ValueError,
                TypeError
            ):
                pass

    # ========================================================
    # 5. Simpler fallback for reviewCount
    # ========================================================

    if reviews is None:

        review_count_pattern = re.compile(
            r'averageCustomerReviews'
            r'.{0,1000}?'
            r'reviewCount'
            r'.{0,100}?'
            r'(\d+)',
            re.IGNORECASE | re.DOTALL
        )

        match = review_count_pattern.search(
            html
        )

        if match:

            try:

                reviews = int(
                    match.group(1)
                )

            except (
                ValueError,
                TypeError
            ):
                pass

    # ========================================================
    # 6. Simpler fallback for rating
    # ========================================================

    if rating is None:

        rating_pattern = re.compile(
            r'averageCustomerReviews'
            r'.{0,1500}?'
            r'(?:value|displayString)'
            r'.{0,100}?'
            r'(\d+(?:\.\d+)?)'
            r'(?:\s*out\s+of\s+5\s+stars)?',
            re.IGNORECASE | re.DOTALL
        )

        match = rating_pattern.search(
            html
        )

        if match:

            try:

                possible_rating = float(
                    match.group(1)
                )

                if 0 <= possible_rating <= 5:

                    rating = possible_rating

            except (
                ValueError,
                TypeError
            ):
                pass

    return rating, reviews
# ============================================================
# PRODUCT EXTRACTION
# ============================================================

def extract_product(url: str) -> Product:

    # ========================================================
    # 1. Normalize URL
    # ========================================================

    if not url.startswith("http"):
        url = "https://" + url

    # ========================================================
    # 2. Fetch product page (retries once if the response
    #    looks like a non-product page) and 4. Parse HTML
    # ========================================================

    response, soup, _fetched_title = _fetch_amazon_page(url)

    # ========================================================
    # 3. Extract ASIN
    # ========================================================

    asin = extract_asin(
        response.url
    )

    print(
        "ASIN:",
        asin
    )

    # ========================================================
    # DEBUG REVIEW METADATA HTML
    # ========================================================

    print("=" * 80)
    print("REVIEW METADATA DEBUG")

    metadata_markers = [
        "acrCustomerReviewText",
        "acrPopover",
        "averageCustomerReviews",
        "rating-out-of-text",
        "ratingValue",
        "reviewCount",
        "ratingCount",
    ]

    html_lower = response.text.lower()

    for marker in metadata_markers:

        positions = [
            match.start()
            for match in re.finditer(
                re.escape(
                    marker.lower()
                ),
                html_lower
            )
        ]

        print(
            f"{marker:<30} -> "
            f"{len(positions)}"
        )

        # ----------------------------------------------------
        # Show first occurrence
        # ----------------------------------------------------

        if positions:

            position = positions[0]

            start = max(
                0,
                position - 500
            )

            end = min(
                len(response.text),
                position + 1500
            )

            print(
                "-" * 80
            )

            print(
                response.text[
                    start:end
                ]
            )

            print(
                "-" * 80
            )

    print("=" * 80)

    # ========================================================
    # DEBUG AMAZON REVIEW HTML
    # ========================================================

    review_markers = [
        'data-hook="review"',
        'data-hook="review-body"',
        "customer review",
        "customer reviews",
        "review-body",
        "cr-list",
    ]

    print("=" * 80)

    print(
        "REVIEW HTML DEBUG"
    )

    for marker in review_markers:

        count = response.text.lower().count(
            marker.lower()
        )

        print(
            f"{marker:<35} -> "
            f"{count}"
        )

    print("=" * 80)

    # ========================================================
    # DEBUG REVIEW-RELATED HTML
    # ========================================================

    print("=" * 80)

    print(
        "REVIEW RELATED HTML SAMPLES"
    )

    html_lower = response.text.lower()

    for marker in [
        "review-body",
        "customer reviews",
        "customer review",
    ]:

        position = html_lower.find(
            marker
        )

        if position == -1:
            continue

        print()
        print(
            f"MARKER: {marker}"
        )

        print(
            "-" * 80
        )

        start = max(
            0,
            position - 1000
        )

        end = min(
            len(response.text),
            position + 3000
        )

        print(
            response.text[
                start:end
            ]
        )

    print("=" * 80)

    # ========================================================
    # 5. Product title
    # ========================================================

    title = (
        soup.title.string.strip()
        if soup.title
        else "Unknown Product"
    )

    print(
        "SCRAPED TITLE:",
        title
    )

    # ========================================================
    # 6. Brand
    # ========================================================

    brand = None

    brand_tag = soup.select_one(
        "#bylineInfo"
    )

    if brand_tag:

        brand = brand_tag.get_text(
            strip=True
        )

    # ========================================================
    # 7. Price
    # ========================================================

    price = None

    price_tag = soup.select_one(
        ".a-price-whole"
    )

    if price_tag:

        price = (
            "₹"
            + price_tag.get_text(
                strip=True
            )
        )

    # ========================================================
    # 8. Rating + Review Count
    # ========================================================

    rating, reviews = extract_review_metadata(
        soup,
        response.text
    )

    print(
        "RATING:",
        rating
    )

    print(
        "REVIEWS:",
        reviews
    )

    # ========================================================
    # 9. Product image
    # ========================================================

    image = None

    image_tag = soup.select_one(
        "#landingImage"
    )

    if image_tag:

        image = image_tag.get(
            "src"
        )

    # ========================================================
    # 10. Availability
    # ========================================================

    availability = None

    stock = soup.select_one(
        "#availability"
    )

    if stock:

        availability = stock.get_text(
            strip=True
        )

    # ========================================================
    # 11. Extract structured specifications
    # ========================================================

    structured_specs = (
        extract_specifications(
            soup
        )
    )

    # ========================================================
    # 12. Extract customer reviews
    # ========================================================

    review_texts = extract_reviews(
        soup,
        max_reviews=10
    )

    # ========================================================
    # 13. Extract title specifications
    # ========================================================

    title_specs = (
        extract_title_specifications(
            title
        )
    )

    # ========================================================
    # 14. Combine specifications
    # ========================================================

    combined_specs = (
        structured_specs
        + title_specs
    )

    # ========================================================
    # 15. Remove duplicate specifications
    # ========================================================

    specifications = []

    seen_names = set()

    aliases = {

        "ram memory":
            "ram",

        "ram memory installed":
            "ram",

        "ram memory installed size":
            "ram",

        "memory storage capacity":
            "storage",

        "display type":
            "display",

        "battery power":
            "battery",

        "cellular technology":
            "cellular",

        "brand name":
            "brand",
    }

    for spec in combined_specs:

        if not isinstance(
            spec,
            dict
        ):
            continue

        name = str(
            spec.get(
                "name",
                ""
            )
        ).strip()

        value = str(
            spec.get(
                "value",
                ""
            )
        ).strip()

        if not name or not value:
            continue

        normalized_name = (
            name.lower().strip()
        )

        normalized_name = aliases.get(
            normalized_name,
            normalized_name
        )

        if normalized_name in seen_names:
            continue

        seen_names.add(
            normalized_name
        )

        specifications.append(
            {
                "name": name,
                "value": value,
            }
        )

    # ========================================================
    # 16. Debug extracted data
    # ========================================================

    print("=" * 80)

    print(
        "TITLE:",
        title
    )

    print(
        "BRAND:",
        brand
    )

    print(
        "PRICE:",
        price
    )

    print(
        "RATING:",
        rating
    )

    print(
        "REVIEWS:",
        reviews
    )

    print(
        "IMAGE:",
        image
    )

    print(
        "AVAILABILITY:",
        availability
    )

    print(
        "REVIEWS EXTRACTED:",
        len(review_texts)
    )

    for index, review in enumerate(
        review_texts,
        start=1
    ):

        print(
            f"  REVIEW {index}: "
            f"{review}"
        )

    print(
        "SPECIFICATIONS:"
    )

    for spec in specifications:

        print(
            f"  {spec['name']}: "
            f"{spec['value']}"
        )

    print("=" * 80)

    # ========================================================
    # FINAL SAFETY NET: composite non-product detection
    #
    # The fast title/marker check in _fetch_amazon_page()
    # catches the common cases (bare homepage title, known
    # bot-check text). This is a second, broader check for a
    # page that didn't trip those markers but still yielded
    # nothing usable -- no brand, no price, no rating, no
    # specifications, no reviews. A genuine Amazon product
    # page essentially never extracts to nothing on every
    # field simultaneously.
    # ========================================================

    if (
        not brand
        and not price
        and rating is None
        and reviews is None
        and not specifications
        and not review_texts
    ):

        raise AmazonBlockedError(
            f"Amazon returned a page (title={title!r}) with "
            "no extractable brand, price, rating, "
            "specifications, or reviews. This looks like a "
            "non-product response rather than a real "
            "extraction failure."
        )

    # ========================================================
    # 17. Return Product
    # ========================================================

    return Product(
        title=title,
        brand=brand,
        price=price,
        rating=rating,
        reviews=reviews,
        image=image,
        availability=availability,
        specifications=specifications,
        review_texts=review_texts,
    )