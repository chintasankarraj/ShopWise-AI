from bs4 import BeautifulSoup


# Specifications that are useful for product analysis.
ALLOWED_KEYWORDS = [
    "processor",
    "cpu",
    "chip",
    "ram",
    "memory",
    "storage",
    "ssd",
    "hard drive",
    "display",
    "screen",
    "resolution",
    "refresh rate",
    "battery",
    "charging",
    "camera",
    "rear camera",
    "front camera",
    "graphics",
    "gpu",
    "operating system",
    "os",
    "bluetooth",
    "wi-fi",
    "wifi",
    "cellular",
    "5g",
    "4g",
    "water resistance",
    "dust resistance",
    "weight",
    "dimensions",
    "material",
    "color",
    "colour",
    "form factor",
    "connectivity",
    "ports",
    "usb",
    "hdmi",
    "warranty",
    "item type",
]


# Specifications that should never be sent to the AI.
IGNORED_KEYWORDS = [
    "replacement",
    "defective item",
    "physical damage",
    "importer contact",
    "manufacturer contact",
    "packer contact",
    "contact information",
    "asin",
    "best sellers rank",
    "customer reviews",
    "customer ratings",
    "unit count",
    "box contents",
]


def normalize_name(name: str) -> str:
    """
    Normalize specification names so duplicates can be detected.
    """

    name = " ".join(name.lower().split())

    aliases = {
        "ram memory installed size": "ram",
        "ram memory installed": "ram",
        "memory storage capacity": "storage",
        "brand name": "brand",
        "display type": "display",
        "battery power": "battery",
        "cellular technology": "cellular",
        "item type name": "item type",
    }

    return aliases.get(name, name)


def is_relevant(name: str) -> bool:
    """
    Decide whether a specification is useful for product analysis.
    """

    normalized = name.lower().strip()

    for ignored in IGNORED_KEYWORDS:
        if ignored in normalized:
            return False

    for keyword in ALLOWED_KEYWORDS:
        if keyword in normalized:
            return True

    return False


def extract_specifications(soup: BeautifulSoup) -> list[dict]:
    """
    Extract useful product specifications from Amazon.

    The parser is category-independent and works with products
    such as smartphones, laptops, headphones, appliances, etc.
    """

    specifications = []

    def add_spec(name: str, value: str):

        name = " ".join(name.split()).strip()
        value = " ".join(value.split()).strip()

        if not name or not value:
            return

        if not is_relevant(name):
            return

        normalized_name = normalize_name(name)

        specifications.append(
            {
                "name": normalized_name.title(),
                "value": value,
            }
        )

    # ============================================================
    # 1. Amazon Technical Details
    # ============================================================

    technical_selectors = [
        "#productDetails_techSpec_section_1 tr",
        "#productDetails_techSpec_section_2 tr",
        "#productDetails_detailBullets_sections1 tr",
        "#productDetails_detailBullets_sections2 tr",
        "#technicalSpecifications tr",
    ]

    for selector in technical_selectors:

        rows = soup.select(selector)

        for row in rows:

            cells = row.find_all(["th", "td"])

            if len(cells) >= 2:

                name = cells[0].get_text(" ", strip=True)
                value = cells[1].get_text(" ", strip=True)

                add_spec(name, value)

    # ============================================================
    # 2. Amazon Detail Bullets
    # ============================================================

    bullet_selectors = [
        "#detailBullets_feature_div li",
        "#detailBulletsWrapper_feature_div li",
        "#detailBullets_feature_div .a-list-item",
    ]

    for selector in bullet_selectors:

        items = soup.select(selector)

        for item in items:

            text = item.get_text(" ", strip=True)

            if ":" not in text:
                continue

            name, value = text.split(":", 1)

            add_spec(name, value)

    # ============================================================
    # 3. Generic Tables
    # ============================================================

    for table in soup.find_all("table"):

        rows = table.find_all("tr")

        for row in rows:

            cells = row.find_all(["th", "td"])

            if len(cells) < 2:
                continue

            name = cells[0].get_text(" ", strip=True)
            value = cells[1].get_text(" ", strip=True)

            if len(name) > 100:
                continue

            if len(value) > 500:
                continue

            add_spec(name, value)

    # ============================================================
    # 4. Remove duplicates
    # ============================================================

    unique_specs = []

    seen = set()

    for spec in specifications:

        key = (
            normalize_name(spec["name"]),
            spec["value"].lower().strip(),
        )

        if key in seen:
            continue

        seen.add(key)

        unique_specs.append(spec)

    # ============================================================
    # 5. Keep one value per normalized specification
    # ============================================================

    final_specs = []

    seen_names = set()

    for spec in unique_specs:

        name = normalize_name(spec["name"])

        if name in seen_names:
            continue

        seen_names.add(name)

        final_specs.append(spec)

    return final_specs