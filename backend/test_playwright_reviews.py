from playwright.sync_api import sync_playwright


URL = "https://www.amazon.in/dp/B09V4B6F4L/"


print("=" * 80)
print("SHOPWISE PLAYWRIGHT REVIEW EXTRACTION TEST")
print("=" * 80)


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page(
        viewport={
            "width": 1366,
            "height": 900
        }
    )

    print("Opening Amazon product page...")

    page.goto(
        URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    print("PAGE TITLE:")
    print(page.title())

    print()

    print("CURRENT URL:")
    print(page.url)

    print()

    print("=" * 80)
    print("SCROLLING TO REVIEWS")
    print("=" * 80)

    customer_reviews = page.locator(
        "#customerReviews"
    )

    print(
        "customerReviews count:",
        customer_reviews.count()
    )

    if customer_reviews.count() > 0:

        customer_reviews.scroll_into_view_if_needed()

        print(
            "Scrolled to customer reviews."
        )

    else:

        print(
            "customerReviews section not found."
        )

    # Give Amazon some time to render
    page.wait_for_timeout(3000)

    print()

    print("=" * 80)
    print("CHECKING REVIEW ELEMENTS")
    print("=" * 80)

    selectors = [
        '[data-hook="review"]',
        '[data-hook="review-body"]',
        '.review',
        '.a-section.review',
        '.cr-list',
        '.cr-reviews-list',
        '[id^="customer_review-"]',
    ]

    for selector in selectors:

        count = page.locator(
            selector
        ).count()

        print(
            f"{selector:40} -> {count}"
        )

    print()

    print("=" * 80)
    print("TEXT INSIDE CUSTOMER REVIEWS")
    print("=" * 80)

    if customer_reviews.count() > 0:

        text = customer_reviews.inner_text(
            timeout=10000
        )

        print(text[:10000])

    else:

        print(
            "Customer reviews section unavailable."
        )

    print()

    print("=" * 80)
    print("PRESS ENTER TO CLOSE BROWSER")
    print("=" * 80)

    input()

    browser.close()