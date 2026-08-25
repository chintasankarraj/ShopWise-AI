import requests
from bs4 import BeautifulSoup




# ============================================================
# REVIEW SELECTORS
# ============================================================

REVIEW_SELECTORS = [
    '[data-hook="review"]',
    '[data-hook="review-body"]',
    '.review',
    '.a-section.review',
]


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_review_text(text: str) -> str:
    """
    Clean extracted customer review text.
    """

    if not text:
        return ""

    text = " ".join(
        text.split()
    ).strip()

    return text


# ============================================================
# EXTRACT REVIEWS
# ============================================================

def extract_reviews(
    soup: BeautifulSoup,
    max_reviews: int = 10,
) -> list[str]:
    """
    Extract customer review text from the supplied Amazon HTML.

    Returns only review text that is actually present
    in the supplied HTML.

    If Amazon does not provide review bodies,
    an empty list is returned.
    """

    reviews = []

    review_blocks = soup.select(
        '[data-hook="review"]'
    )

    for block in review_blocks:

        body = block.select_one(
            '[data-hook="review-body"]'
        )

        if not body:
            continue

        text = clean_review_text(
            body.get_text(
                " ",
                strip=True
            )
        )

        if not text:
            continue

        reviews.append(text)

        if len(reviews) >= max_reviews:
            break

    if not reviews:

        review_bodies = soup.select(
            '[data-hook="review-body"]'
        )

        for body in review_bodies:

            text = clean_review_text(
                body.get_text(
                    " ",
                    strip=True
                )
            )

            if not text:
                continue

            reviews.append(text)

            if len(reviews) >= max_reviews:
                break

    unique_reviews = []

    seen = set()

    for review in reviews:

        normalized = review.lower().strip()

        if normalized in seen:
            continue

        seen.add(normalized)

        unique_reviews.append(review)

    return unique_reviews[:max_reviews]

    # --------------------------------------------------------
    # 1. Look for complete Amazon review containers
    # --------------------------------------------------------

    review_blocks = soup.select(
        '[data-hook="review"]'
    )

    for block in review_blocks:

        body = block.select_one(
            '[data-hook="review-body"]'
        )

        if not body:
            continue

        text = clean_review_text(
            body.get_text(
                " ",
                strip=True
            )
        )

        if not text:
            continue

        reviews.append(text)

        if len(reviews) >= max_reviews:
            break

    # --------------------------------------------------------
    # 2. Fallback: directly search review bodies
    # --------------------------------------------------------

    if not reviews:

        review_bodies = soup.select(
            '[data-hook="review-body"]'
        )

        for body in review_bodies:

            text = clean_review_text(
                body.get_text(
                    " ",
                    strip=True
                )
            )

            if not text:
                continue

            reviews.append(text)

            if len(reviews) >= max_reviews:
                break

    # --------------------------------------------------------
    # 3. Remove duplicates
    # --------------------------------------------------------

    unique_reviews = []

    seen = set()

    for review in reviews:

        normalized = review.lower().strip()

        if normalized in seen:
            continue

        seen.add(normalized)

        unique_reviews.append(review)

    # --------------------------------------------------------
    # 4. Return actual reviews only
    # --------------------------------------------------------

    return unique_reviews[:max_reviews]



def debug_review_html(soup: BeautifulSoup) -> None:
    """
    Debug Amazon HTML for possible customer review content.
    """

    print("=" * 80)
    print("REVIEW HTML DIAGNOSTIC")
    print("=" * 80)

    html = str(soup)

    markers = [
        "customer review",
        "customer reviews",
        "review-body",
        "reviewTitle",
        "reviewText",
        "reviewerName",
        "reviewRating",
        "reviewId",
        "cr-list",
    ]

    for marker in markers:

        count = html.lower().count(
            marker.lower()
        )

        print(
            f"{marker:<25} -> {count}"
        )

    print("=" * 80)