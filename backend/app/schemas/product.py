from typing import List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, field_validator


# ============================================================
# URL VALIDATION
#
# extract_product() (app/services/product_extractor.py) only
# knows how to parse Amazon product pages, and the server
# fetches whatever URL is submitted here -- so this allowlist
# also prevents the endpoint from being used to make the
# backend fetch arbitrary/internal URLs (SSRF).
# ============================================================

ALLOWED_URL_DOMAINS = {
    "amazon.in",
    "amazon.com",
    "amazon.co.uk",
    "amazon.de",
    "amazon.ca",
    "amazon.com.au",
    "amzn.in",
    "amzn.to",
}


def _is_allowed_product_url(url: str) -> bool:

    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    hostname = (parsed.hostname or "").lower()

    if hostname.startswith("www."):
        hostname = hostname[4:]

    return any(
        hostname == domain or hostname.endswith("." + domain)
        for domain in ALLOWED_URL_DOMAINS
    )


class ProductRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:

        value = (value or "").strip()

        if not value:
            raise ValueError("Product URL is required.")

        if not value.startswith("http"):
            value = "https://" + value

        if not _is_allowed_product_url(value):
            raise ValueError(
                "Only Amazon product URLs (e.g. amazon.in) are "
                "supported."
            )

        return value


class Specification(BaseModel):
    name: str
    value: str


class Product(BaseModel):
    title: str
    brand: Optional[str] = None
    price: Optional[str] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    image: Optional[str] = None
    availability: Optional[str] = None

    specifications: List[Specification] = []

    review_texts: List[str] = []