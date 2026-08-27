"""
Offline, network-free tests for the Issue 5 fix: alternatives
must be verified against a real Amazon.in listing (reusing the
existing ScraperAPI infrastructure) before being shown as
available, and the static curated dataset must never be used as
a live "Better Alternatives" fallback anymore.
"""

import app.agents.alternative_agent as alternative_agent

from app.schemas.product import Product


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


def fake_fetch_factory(responses):
    """
    Build a fake fetch_product_from_scraperapi(url, timeout=...)
    that returns a canned Product (or raises) per URL, so tests
    don't touch the network or spend real ScraperAPI credits.
    Accepts (and ignores) `timeout` since production code always
    passes an explicit override for verification calls -- see
    test_network_timeouts.py for dedicated timeout-value checks.
    """

    def _fake_fetch(url, timeout=60):
        result = responses[url]

        if isinstance(result, Exception):
            raise result

        return result

    return _fake_fetch


# --------------------------------------------------------------
# _amazon_asin_if_verifiable: domain gating
# --------------------------------------------------------------

check(
    "real amazon.in product URL -> ASIN extracted",
    alternative_agent._amazon_asin_if_verifiable(
        "https://www.amazon.in/dp/B0DSKMV3ZC"
    )
    == "B0DSKMV3ZC",
)
check(
    "non-Amazon URL -> None (not verifiable with our infra)",
    alternative_agent._amazon_asin_if_verifiable(
        "https://www.flipkart.com/some-product/p/itm123"
    )
    is None,
)
check(
    "look-alike domain (not a real amazon.in subdomain) -> None",
    alternative_agent._amazon_asin_if_verifiable(
        "https://evilamazon.in/dp/B0DSKMV3ZC"
    )
    is None,
)

# --------------------------------------------------------------
# _verify_amazon_availability: the three outcomes
# --------------------------------------------------------------

verified_product = Product(
    title="Real Current Phone",
    brand="Brand",
    price="₹19,999",
    rating=4.2,
    reviews=500,
    availability="In stock",
    specifications=[],
    review_texts=[],
)

unavailable_product = Product(
    title="Discontinued Phone",
    brand="Brand",
    price=None,
    rating=4.0,
    reviews=200,
    availability="Currently unavailable.",
    specifications=[],
    review_texts=[],
)

alternative_agent.fetch_product_from_scraperapi = fake_fetch_factory(
    {
        "https://www.amazon.in/dp/VERIFIED01": verified_product,
        "https://www.amazon.in/dp/GONE000001": unavailable_product,
        "https://www.amazon.in/dp/ERRORS00001": (
            alternative_agent.ScraperAPIProviderError("no key configured")
        ),
    }
)

status, price, availability = alternative_agent._verify_amazon_availability(
    "https://www.amazon.in/dp/VERIFIED01"
)
check(
    "listing with a real price -> status 'verified'",
    status == "verified" and price == "₹19,999",
)

status, price, availability = alternative_agent._verify_amazon_availability(
    "https://www.amazon.in/dp/GONE000001"
)
check(
    "listing explicitly marked unavailable -> status 'unavailable'",
    status == "unavailable" and price is None,
)

status, price, availability = alternative_agent._verify_amazon_availability(
    "https://www.amazon.in/dp/ERRORS00001"
)
check(
    "ScraperAPI failure (e.g. missing key) -> status 'unknown', no crash",
    status == "unknown",
)

status, price, availability = alternative_agent._verify_amazon_availability(
    "https://www.flipkart.com/some-product"
)
check(
    "non-Amazon URL -> status 'unknown' (can't verify, never claim available)",
    status == "unknown",
)


# --------------------------------------------------------------
# _verify_and_label_alternatives: end-to-end labeling behavior
# --------------------------------------------------------------

candidates = [
    {
        "name": "Verified Current Phone",
        "price": "Price unavailable",
        "url": "https://www.amazon.in/dp/VERIFIED01",
        "availability": "Currently listed",
        "reason": "A real reason.",
    },
    {
        "name": "Discontinued Phone",
        "price": "Price unavailable",
        "url": "https://www.amazon.in/dp/GONE000001",
        "availability": "Currently listed",
        "reason": "A real reason.",
    },
    {
        "name": "Unverifiable Manufacturer Listing",
        "price": "₹24,999",
        "url": "https://www.flipkart.com/some-product",
        "availability": "Currently listed",
        "reason": "A real reason.",
    },
]

labeled = alternative_agent._verify_and_label_alternatives(candidates)
labeled_by_name = {item["name"]: item for item in labeled}

check(
    "verified alternative is accepted with its real price and verified=True",
    labeled_by_name.get("Verified Current Phone", {}).get("price") == "₹19,999"
    and labeled_by_name["Verified Current Phone"]["verified"] is True,
)
check(
    "confirmed-unavailable alternative is dropped entirely, not shown",
    "Discontinued Phone" not in labeled_by_name,
)
check(
    "unverifiable alternative is kept but honestly labeled, not padded with a fake claim",
    labeled_by_name.get("Unverifiable Manufacturer Listing", {}).get("availability")
    == "Availability could not be verified",
)
check(
    "unverifiable alternative's price/url are unchanged, not invented",
    labeled_by_name["Unverifiable Manufacturer Listing"]["price"] == "₹24,999"
    and labeled_by_name["Unverifiable Manufacturer Listing"]["url"]
    == "https://www.flipkart.com/some-product",
)
check(
    "insufficient verified candidates -> fewer results (2), not padded back up to 3",
    len(labeled) == 2,
)


# --------------------------------------------------------------
# find_alternatives(): both live tiers failing must NOT fall
# back to the old curated dataset (the actual Issue 5 bug).
# --------------------------------------------------------------

class DummyProduct:
    title = "Samsung Galaxy M36 5G Mobile"
    brand = "Samsung"
    price = "₹19,999"
    rating = 4.1
    reviews = 4
    availability = "In stock"
    category = "smartphone"


alternative_agent._find_with_gemini = lambda product, spec_data: []
alternative_agent._find_with_web_fallback = lambda product, spec_data: []

result = alternative_agent.find_alternatives(DummyProduct(), [])

check(
    "both live tiers empty -> returns [] (never falls back to stale curated dataset)",
    result == {"alternatives": []},
)

STALE_NAMES = {"Redmi Note 13 5G", "realme 12x 5G", "POCO M6 Pro 5G"}

check(
    "the specific stale products from the reported bug are nowhere in the result",
    not any(
        item.get("name") in STALE_NAMES
        for item in result["alternatives"]
    ),
)

check(
    "the old curated-dataset tier is no longer wired into the module at all",
    not hasattr(alternative_agent, "get_curated_alternatives"),
)


# --------------------------------------------------------------
# Regression: existing legitimacy validation is unchanged.
# --------------------------------------------------------------

class SameProduct:
    title = "Samsung Galaxy M36 5G Mobile"


same_product_candidates = [
    {
        "name": "Samsung Galaxy M36 5G Mobile",
        "price": "₹19,999",
        "url": "https://www.amazon.in/dp/SOMEOTHER1",
        "availability": "Currently listed",
        "reason": "Should be rejected as same product.",
    }
]

validated = alternative_agent._validate_alternatives(
    same_product_candidates,
    SameProduct(),
)

check(
    "existing same-product rejection in _validate_alternatives still works unchanged",
    validated == [],
)

print()
print("All alternative verification checks passed.")
