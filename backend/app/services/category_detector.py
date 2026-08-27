import re


def detect_category(title: str, specifications: list) -> str:
    """
    Detect the product category using both the product title
    and Amazon specifications.

    Supported categories:
        smartphone
        laptop
        tablet
        headphones
        television
        camera
        smartwatch
        appliance
        electronics
        other
    """

    title_text = (title or "").lower()

    # ---------------------------------------------------------
    # Convert specification list into searchable text
    # ---------------------------------------------------------

    spec_text_parts = []

    for spec in specifications or []:

        if isinstance(spec, dict):
            name = spec.get("name", "")
            value = spec.get("value", "")

        else:
            name = getattr(spec, "name", "")
            value = getattr(spec, "value", "")

        spec_text_parts.append(
            f"{name} {value}"
        )

    spec_text = " ".join(spec_text_parts).lower()

    combined_text = f"{title_text} {spec_text}"

    # ---------------------------------------------------------
    # 1. Smartphone
    # ---------------------------------------------------------

    smartphone_keywords = [
        "smartphone",
        "mobile phone",
        "cell phone",
        "android phone",
        "iphone",
        "5g phone",
        "4g phone",
    ]

    if any(
        keyword in combined_text
        for keyword in smartphone_keywords
    ):
        return "smartphone"

    # ---------------------------------------------------------
    # 2. Laptop
    # ---------------------------------------------------------

    laptop_keywords = [
        "laptop",
        "notebook computer",
        "gaming laptop",
        "ultrabook",
        "chromebook",
        "macbook",
    ]

    if any(
        keyword in combined_text
        for keyword in laptop_keywords
    ):
        return "laptop"

    # ---------------------------------------------------------
    # 3. Tablet
    # ---------------------------------------------------------

    tablet_keywords = [
        "tablet",
        "ipad",
        "android tablet",
    ]

    if any(
        keyword in combined_text
        for keyword in tablet_keywords
    ):
        return "tablet"

    # ---------------------------------------------------------
    # 4. Headphones / Earbuds
    # ---------------------------------------------------------

    headphone_keywords = [
        "headphones",
        "headphone",
        "earbuds",
        "earphones",
        "wireless earbuds",
        "bluetooth headset",
        "headset",
    ]

    if any(
        keyword in combined_text
        for keyword in headphone_keywords
    ):
        return "headphones"

    # ---------------------------------------------------------
    # 5. Television
    # ---------------------------------------------------------

    television_keywords = [
        "television",
        "smart tv",
        "smart television",
        "4k tv",
        "oled tv",
        "qled tv",
    ]

    if any(
        keyword in combined_text
        for keyword in television_keywords
    ):
        return "television"

    # Real listings often separate "TV" from its qualifier with
    # a brand/platform word in between (e.g. "Smart Google TV",
    # "4K ... Google TV"), so the exact-phrase keywords above
    # miss them. Falling back to "TV" as a standalone word
    # catches these without matching unrelated tokens like
    # "TVS" (word boundary requires "tv" not be glued to
    # another letter).
    if re.search(r"\btv\b", combined_text):
        return "television"

    # ---------------------------------------------------------
    # 6. Camera
    # ---------------------------------------------------------

    camera_keywords = [
        "digital camera",
        "mirrorless camera",
        "dslr",
        "action camera",
        "camera body",
        "instant camera",
    ]

    if any(
        keyword in combined_text
        for keyword in camera_keywords
    ):
        return "camera"

    # ---------------------------------------------------------
    # 7. Smartwatch
    # ---------------------------------------------------------

    smartwatch_keywords = [
        "smartwatch",
        "smart watch",
        "fitness watch",
        "wearable watch",
    ]

    if any(
        keyword in combined_text
        for keyword in smartwatch_keywords
    ):
        return "smartwatch"

    # ---------------------------------------------------------
    # 8. Appliances
    # ---------------------------------------------------------

    appliance_keywords = [
        "refrigerator",
        "fridge",
        "washing machine",
        "microwave",
        "air conditioner",
        "air cooler",
        "vacuum cleaner",
        "air purifier",
        "water purifier",
        "dishwasher",
        "mixer grinder",
        "coffee maker",
        "electric kettle",
    ]

    if any(
        keyword in combined_text
        for keyword in appliance_keywords
    ):
        return "appliance"

    # ---------------------------------------------------------
    # 9. Generic electronics
    # ---------------------------------------------------------

    electronics_keywords = [
        "electronic",
        "electronics",
        "bluetooth",
        "wireless",
        "usb",
        "hdmi",
    ]

    if any(
        keyword in combined_text
        for keyword in electronics_keywords
    ):
        return "electronics"

    # ---------------------------------------------------------
    # 10. Fallback
    # ---------------------------------------------------------

    return "other"