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
    "water resistant",
    "dust resistance",
    "dust resistant",
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


def specification_richness(value: str) -> tuple:
    """
    Deterministic heuristic for how informative a specification
    VALUE is, used to pick between two values that share the
    same normalized specification name (see step 5 below).

    Amazon listings sometimes carry the same attribute in more
    than one table with different levels of detail -- e.g. a
    compact "at a glance" summary ("6.1 in") alongside a fuller
    technical description ("Super Retina XDR display ... OLED
    ... 2556x1179-pixel resolution at 460 ppi") both normalizing
    to "Display". Picking whichever was merely encountered
    first can silently keep the less useful one.

    Returns a (digit_count, word_count, length) tuple, compared
    lexicographically by the caller. This is deliberately NOT
    "longest string wins" -- that alone could let an unusually
    long but low-content value (e.g. repeated boilerplate/legal
    text) beat a short, precise one no matter how long the
    former is. Putting digit count and word count ahead of
    length in the tuple means actual technical content (a
    resolution, a measurement, distinct descriptive terms) is
    always compared first; raw length only ever acts as the
    final tie-breaker between two values with equal content
    signals, never as a way to out-rank them.
    """

    value = (value or "").strip()

    if not value:
        return (0, 0, 0)

    digit_count = sum(
        character.isdigit()
        for character in value
    )

    word_count = len(
        value.split()
    )

    return (
        digit_count,
        word_count,
        len(value),
    )


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
    # 5. Keep the most informative value per normalized
    #    specification (see specification_richness() docstring
    #    above) -- not simply whichever was encountered first.
    #    The final list still preserves each name's original
    #    first-seen ORDER; only which value is kept for that
    #    name can change.
    # ============================================================

    best_by_name = {}

    order = []

    for spec in unique_specs:

        name = normalize_name(spec["name"])

        if name not in best_by_name:

            best_by_name[name] = spec

            order.append(name)

            continue

        existing = best_by_name[name]

        if (
            specification_richness(spec["value"])
            > specification_richness(existing["value"])
        ):

            best_by_name[name] = spec

    final_specs = [
        best_by_name[name]
        for name in order
    ]

    return final_specs