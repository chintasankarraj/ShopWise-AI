"""
Round 3 root-cause fix regression tests: the review pipeline was
silently returning zero reviews on 100% of real products because
Amazon's review-body element moved from data-hook="review-body" to
data-hook="reviewText" (confirmed live against 10 real products
across 8 brands, smartphones and laptops), and the ScraperAPI
fallback path hardcoded review_texts=[] despite ScraperAPI's own
structured endpoint returning real review text under a top-level
"reviews" list (confirmed live against 2 real products).

Fixtures below are shaped after the two real structures actually
observed this round -- not invented shapes.
"""

from bs4 import BeautifulSoup

from app.services.review_parser import (
    extract_reviews,
    normalize_review_list,
    _strip_accessibility_prefix,
    _strip_read_more_less_suffix,
)
from app.services.scraperapi_product_provider import _extract_review_texts


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


# ================================================================
# Realistic direct-HTML fixture, shaped exactly like the real
# structure confirmed live this round: [data-hook="review"]
# container > [data-hook="reviewText"] body, with Amazon's own
# fixed accessibility-toggle prefix and Read-more/Read-less
# suffix both present, exactly as observed on every real product.
# ================================================================

def _html_review_block(body_text, include_container=True):
    inner = (
        f'<div data-hook="reviewText">'
        f'<span>Brief content visible, double tap to read full content. '
        f'Full content visible, double tap to read brief content. '
        f'{body_text} Read more Read less</span>'
        f'</div>'
    )
    if include_container:
        return f'<div data-hook="review" id="R1">{inner}</div>'
    return inner


REALISTIC_HTML = f"""
<html><body>
<div id="cm-cr-dp-review-list">
  {_html_review_block("Excellent phone, camera is fantastic and battery lasts all day.")}
  {_html_review_block("Good value for money but heats up during gaming sessions.")}
  {_html_review_block("Screen quality is outstanding, very happy with this purchase.")}
</div>
</body></html>
"""


# ================================================================
# 1. Normal structured review response (direct HTML)
# ================================================================

soup = BeautifulSoup(REALISTIC_HTML, "lxml")
reviews = extract_reviews(soup, max_reviews=10)
check(
    "normal realistic HTML fixture (data-hook=review > reviewText, with Amazon's own "
    "boilerplate) -> 3 clean reviews extracted",
    len(reviews) == 3,
)
check(
    "extracted review text has the accessibility prefix stripped",
    not reviews[0].lower().startswith("brief content"),
)
check(
    "extracted review text has the Read more/Read less suffix stripped",
    "read more" not in reviews[0].lower(),
)
check(
    "the real review sentence survives intact",
    "camera is fantastic" in reviews[0].lower(),
)


# ================================================================
# 2. Multiple review records
# ================================================================

check(
    "multiple review records are all captured, not just the first",
    "heats up during gaming" in reviews[1].lower()
    and "screen quality is outstanding" in reviews[2].lower(),
)


# ================================================================
# 3. Missing review field / empty review list (direct HTML)
# ================================================================

no_reviews_html = "<html><body><div>No review section on this page at all.</div></body></html>"
soup = BeautifulSoup(no_reviews_html, "lxml")
check(
    "HTML with no review markup at all -> empty list, no crash",
    extract_reviews(soup, max_reviews=10) == [],
)

empty_containers_html = '<html><body><div data-hook="review" id="R1"></div></body></html>'
soup = BeautifulSoup(empty_containers_html, "lxml")
check(
    "review container present but empty (no reviewText child) -> empty list, no crash",
    extract_reviews(soup, max_reviews=10) == [],
)


# ================================================================
# 4. review field with malformed data / mixed valid+invalid
# ================================================================

malformed_html = f"""
<html><body>
<div data-hook="review" id="R1"><div data-hook="reviewText"></div></div>
<div data-hook="review" id="R2">{_html_review_block("A real, genuine review with actual content.", include_container=False)}</div>
<div data-hook="review" id="R3"><div data-hook="reviewText">   </div></div>
</body></html>
"""
soup = BeautifulSoup(malformed_html, "lxml")
reviews = extract_reviews(soup, max_reviews=10)
check(
    "mixed valid/invalid review blocks (empty body, whitespace-only body, real body) "
    "-> only the real one survives",
    len(reviews) == 1 and "genuine review" in reviews[0].lower(),
)


# ================================================================
# 5. Duplicate reviews
# ================================================================

dup_html = f"""
<html><body>
{_html_review_block("This exact review text appears twice on the page.")}
{_html_review_block("This exact review text appears twice on the page.")}
{_html_review_block("A different, unique review.")}
</body></html>
"""
soup = BeautifulSoup(dup_html, "lxml")
reviews = extract_reviews(soup, max_reviews=10)
check(
    "duplicate review text is de-duplicated",
    len(reviews) == 2,
)


# ================================================================
# 6. 10-review maximum
# ================================================================

many_html = "<html><body>" + "".join(
    _html_review_block(f"Unique review number {i} with distinct content.")
    for i in range(15)
) + "</body></html>"
soup = BeautifulSoup(many_html, "lxml")
reviews = extract_reviews(soup, max_reviews=10)
check(
    "15 real review blocks on the page -> capped at exactly 10",
    len(reviews) == 10,
)


# ================================================================
# 7. normalize_review_list() directly -- the shared layer
# ================================================================

check(
    "normalize_review_list: None input -> empty list, no crash",
    normalize_review_list(None) == [],
)
check(
    "normalize_review_list: empty list -> empty list",
    normalize_review_list([]) == [],
)
check(
    "normalize_review_list: strips accessibility prefix and Read more/Read less suffix together",
    normalize_review_list([
        "Brief content visible, double tap to read full content. "
        "Full content visible, double tap to read brief content. "
        "Great product overall. Read more Read less"
    ]) == ["Great product overall."],
)
check(
    "normalize_review_list: a customer's own review mentioning 'read more' mid-sentence "
    "is NOT truncated (only an exact trailing match is stripped)",
    "you can read more about it online if curious"
    in normalize_review_list(["You can read more about it online if curious."])[0].lower(),
)
check(
    "_strip_accessibility_prefix leaves unrelated text untouched",
    _strip_accessibility_prefix("A completely normal review.") == "A completely normal review.",
)
check(
    "_strip_read_more_less_suffix leaves unrelated text untouched",
    _strip_read_more_less_suffix("A completely normal review.") == "A completely normal review.",
)


# ================================================================
# 8. ScraperAPI path -- realistic fixture shaped like the real
# structure confirmed live this round: a top-level "reviews" list
# of dicts, each with "review" (text), "stars", "title", "date",
# plus reviewer-identity fields this code must never read.
# ================================================================

REALISTIC_SCRAPERAPI_RESPONSE = {
    "name": "Example Product",
    "reviews": [
        {
            "stars": 5,
            "date": "Reviewed in India on 1 January 2026",
            "verified_purchase": True,
            "username": "SomeReviewer",
            "user_url": "https://www.amazon.in/gp/profile/example",
            "title": "Great product",
            "review": "This is a genuine, clean review straight from ScraperAPI with no HTML artifacts.",
            "total_found_helpful": 3,
        },
        {
            "stars": 4,
            "date": "Reviewed in India on 2 January 2026",
            "verified_purchase": True,
            "username": "AnotherReviewer",
            "title": "Good value",
            "review": "Solid product for the price, would recommend to others.",
        },
    ],
}

check(
    "normal structured ScraperAPI response -> both reviews extracted, clean text",
    _extract_review_texts(REALISTIC_SCRAPERAPI_RESPONSE) == [
        "This is a genuine, clean review straight from ScraperAPI with no HTML artifacts.",
        "Solid product for the price, would recommend to others.",
    ],
)
check(
    "reviewer identity fields (username/user_url) are never present in the extracted output",
    not any(
        "SomeReviewer" in r or "AnotherReviewer" in r or "profile/example" in r
        for r in _extract_review_texts(REALISTIC_SCRAPERAPI_RESPONSE)
    ),
)

check(
    "missing 'reviews' field entirely -> empty list, no crash",
    _extract_review_texts({"name": "X"}) == [],
)
check(
    "'reviews' present but an empty list -> empty list",
    _extract_review_texts({"name": "X", "reviews": []}) == [],
)
check(
    "'reviews' present but null -> empty list, no crash",
    _extract_review_texts({"name": "X", "reviews": None}) == [],
)
check(
    "'reviews' is present but is the wrong type (a string, not a list) -> empty list, no crash",
    _extract_review_texts({"name": "X", "reviews": "not a list"}) == [],
)

# rating without text / text without rating / malformed entries
mixed_quality_response = {
    "reviews": [
        {"stars": 5, "title": "No text field at all"},
        {"stars": 3, "review": ""},
        {"stars": None, "review": "This one has text but the rating is missing/null."},
        {"review": "This one has no stars field at all, but does have text."},
        "not even a dict",
        {"stars": 4, "review": "A perfectly normal valid review."},
    ]
}
extracted = _extract_review_texts(mixed_quality_response)
check(
    "rating-without-text entries contribute nothing (no fabricated text)",
    "No text field at all" not in extracted and len(extracted) == 3,
)
check(
    "text-without-rating entries are still kept (rating is not required for real review text)",
    any("rating is missing" in r.lower() for r in extracted)
    and any("no stars field" in r.lower() for r in extracted),
)
check(
    "a non-dict entry in the reviews list does not crash extraction",
    any("perfectly normal valid review" in r.lower() for r in extracted),
)

# duplicates via ScraperAPI too
dup_response = {
    "reviews": [
        {"stars": 5, "review": "This exact text appears twice."},
        {"stars": 5, "review": "This exact text appears twice."},
        {"stars": 4, "review": "A unique second review."},
    ]
}
check(
    "duplicate review text from ScraperAPI is also de-duplicated (shared normalization layer)",
    len(_extract_review_texts(dup_response)) == 2,
)

# 10-review cap via ScraperAPI
many_response = {
    "reviews": [
        {"stars": 5, "review": f"Unique ScraperAPI review number {i}."}
        for i in range(15)
    ]
}
check(
    "15 real ScraperAPI review records -> capped at exactly 10 "
    "(same cap as the direct-HTML path, same shared function)",
    len(_extract_review_texts(many_response)) == 10,
)


# ================================================================
# 9. No fabricated review data, under any circumstance
# ================================================================

check(
    "a product with genuinely zero reviews on Amazon (empty HTML, empty ScraperAPI list) "
    "produces an empty list from BOTH paths -- never a placeholder or invented review",
    extract_reviews(BeautifulSoup("<html><body></body></html>", "lxml"), max_reviews=10) == []
    and _extract_review_texts({"reviews": []}) == [],
)

print()
print("All review extraction root-cause checks passed.")
