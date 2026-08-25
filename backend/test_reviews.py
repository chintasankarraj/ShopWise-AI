import requests

from bs4 import BeautifulSoup

from app.services.review_parser import extract_reviews

from app.services.review_parser import debug_review_html

URL = "https://www.amazon.in/dp/B0H8CF8GRH/"


headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}


print("=" * 80)
print("SHOPWISE REVIEW EXTRACTION TEST")
print("=" * 80)

print("URL:", URL)

response = requests.get(
    URL,
    headers=headers,
    timeout=20,
)

print()
print("=" * 80)
print("HTTP RESPONSE")
print("=" * 80)

print("STATUS CODE:", response.status_code)
print("FINAL URL:", response.url)
print("RESPONSE SIZE:", len(response.text))


soup = BeautifulSoup(
    response.text,
    "html.parser"
)


print()
print("=" * 80)
print("REVIEW EXTRACTION")
print("=" * 80)

reviews = extract_reviews(
    soup,
    max_reviews=10
)

debug_review_html(soup)

print("=" * 80)
print("RAW REVIEW-BODY CONTEXT")
print("=" * 80)

html = str(soup)

marker = 'review-body'

position = html.lower().find(marker.lower())

if position != -1:

    start = max(
        0,
        position - 1500
    )

    end = min(
        len(html),
        position + 3000
    )

    print(
        html[start:end]
    )

else:

    print(
        "review-body NOT FOUND"
    )

print("=" * 80)
print("REVIEWS EXTRACTED:", len(reviews))


for index, review in enumerate(
    reviews,
    start=1
):

    print()
    print(f"REVIEW {index}")
    print("-" * 80)
    print(review)


print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)