import re


def _normalize_spec_dict(specifications):
    """
    Build a {lowercased name: lowercased value} lookup out of the
    same specification objects detect_category already accepts
    (Pydantic models or dicts), so structural checks can target a
    specific field instead of a raw concatenated-text search.
    """

    normalized = {}

    for spec in specifications or []:

        if isinstance(spec, dict):
            name = spec.get("name", "")
            value = spec.get("value", "")

        else:
            name = getattr(spec, "name", "")
            value = getattr(spec, "value", "")

        if not name:
            continue

        normalized[str(name).lower().strip()] = str(value).lower().strip()

    return normalized


def _spec_value(specs_dict, keywords):
    """
    First specification value whose (lowercased) name contains
    one of the given keywords.
    """

    for keyword in keywords:
        for name, value in specs_dict.items():
            if keyword in name:
                return value

    return None


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
    # 9. Structural fallback for smartphone / laptop
    #
    # A real listing's title sometimes omits every generic
    # category noun ("phone", "mobile", "laptop"...) and its
    # scraped specs can likewise omit a helpful "Item Type"
    # field, so the keyword checks above find nothing even
    # though the specifications themselves clearly describe a
    # phone or a laptop. This only runs after every more
    # specific keyword category above has already had a chance
    # to match, so it can't override an explicit tablet/TV/
    # camera/appliance/etc. classification -- it only rescues
    # products that would otherwise fall through to generic
    # "electronics"/"other".
    # ---------------------------------------------------------

    specs_dict = _normalize_spec_dict(specifications)

    # Deliberately just "operating system", not a bare "os" --
    # "os" as a loose substring would false-positive on unrelated
    # field names like "Cross Platform Support" or "Hosting".
    operating_system = _spec_value(
        specs_dict,
        ["operating system"],
    )

    screen_size_text = _spec_value(
        specs_dict,
        ["screen size", "display size"],
    )

    screen_inches = None

    if screen_size_text:
        size_match = re.search(r"\d+(?:\.\d+)?", screen_size_text)
        if size_match:
            screen_inches = float(size_match.group())

    is_mobile_os = bool(operating_system) and (
        "android" in operating_system
        or "ios" in operating_system
    )

    has_cellular_generation = bool(
        re.search(r"\b[45]g\b", combined_text)
    )

    looks_like_smartphone = (
        is_mobile_os
        and has_cellular_generation
        and (screen_inches is None or screen_inches <= 7.2)
    )

    if looks_like_smartphone:
        return "smartphone"

    is_desktop_os = bool(operating_system) and (
        "windows" in operating_system
        or "mac os" in operating_system
        or "macos" in operating_system
    )

    has_computer_memory_fields = bool(
        _spec_value(specs_dict, ["ram", "memory"])
    ) and bool(
        _spec_value(specs_dict, ["storage", "hard drive", "ssd"])
    )

    looks_like_laptop = (
        is_desktop_os
        and has_computer_memory_fields
        and (screen_inches is None or screen_inches >= 9.0)
    )

    if looks_like_laptop:
        return "laptop"

    # ---------------------------------------------------------
    # 10. Generic electronics
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
    # 11. Fallback
    # ---------------------------------------------------------

    return "other"