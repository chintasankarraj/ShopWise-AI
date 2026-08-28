import re


def extract_title_specifications(title: str) -> list[dict]:
    """
    Extract useful specifications embedded directly in a product title.
    """

    if not title:
        return []

    text = title

    specifications = []

    def add_spec(name: str, value: str):

        if not value:
            return

        specifications.append({
            "name": name,
            "value": value.strip(),
        })

    # --------------------------------------------------
    # RAM
    # --------------------------------------------------

    ram = re.search(
        r"(\d+)\s*GB\s*RAM",
        text,
        re.IGNORECASE,
    )

    if ram:
        add_spec(
            "RAM",
            f"{ram.group(1)} GB",
        )

    # --------------------------------------------------
    # Storage / ROM
    # --------------------------------------------------

    storage = re.search(
        r"(\d+)\s*(GB|TB)\s*(?:ROM|Storage)",
        text,
        re.IGNORECASE,
    )

    if storage:

        add_spec(
            "Storage",
            f"{storage.group(1)} {storage.group(2).upper()}",
        )

    # --------------------------------------------------
    # Battery
    # --------------------------------------------------

    battery = re.search(
        r"(\d{3,6})\s*mAh\s*Battery",
        text,
        re.IGNORECASE,
    )

    if battery:

        add_spec(
            "Battery",
            f"{battery.group(1)} mAh",
        )

    # --------------------------------------------------
    # Charging
    # --------------------------------------------------

    charging = re.search(
        r"(\d+)\s*W\s*(?:Fast\s*)?Charging",
        text,
        re.IGNORECASE,
    )

    if charging:

        add_spec(
            "Charging",
            f"{charging.group(1)} W",
        )

    # --------------------------------------------------
    # Display Size
    # --------------------------------------------------

    # Titles use the quote/prime symbol ("6.77\""); prose --
    # feature bullets in particular -- tends to spell it out
    # instead ("6.77 inch"). A bare "in" abbreviation is
    # deliberately not accepted here: it's too common inside
    # unrelated words/phrases ("Built-in", "in Ear") to be a
    # safe signal.
    display_size = re.search(
        r'(\d+(?:\.\d+)?)\s*(?:["″]|inch(?:es)?\b)\s*'
        r'(?:\d+\s*Hz\s*)?(?:TrueColour\s*)?(AMOLED|OLED|LCD|IPS)?',
        text,
        re.IGNORECASE,
    )

    if display_size:

        value = f"{display_size.group(1)} inch"

        if display_size.group(2):
            value += f" {display_size.group(2).upper()}"

        add_spec(
            "Display Size",
            value,
        )

    # --------------------------------------------------
    # Refresh Rate
    # --------------------------------------------------

    refresh = re.search(
        r"(\d+)\s*Hz",
        text,
        re.IGNORECASE,
    )

    if refresh:

        add_spec(
            "Refresh Rate",
            f"{refresh.group(1)} Hz",
        )

    # --------------------------------------------------
    # Processor / Chipset
    # --------------------------------------------------

    # Apple Silicon (M-series) laptop chips -- checked first and
    # separately from the generic patterns below because the
    # emitted value must include the literal word "Apple" (the
    # scoring tier lookup in recommendation_agent.py requires it,
    # to stay disambiguated from Intel's old "Core M3/M5/M7"
    # Y-series branding). Requires the literal word "chip"
    # immediately after the model -- how Apple always phrases it
    # on Amazon ("...with M3 chip: ...") -- which alone already
    # rules out Intel's naming (never phrased that way), so no
    # separate "Apple" co-occurrence check in the source text is
    # needed before emitting the qualified value.
    apple_silicon = re.search(
        r"\bM([1-4])\s*(Pro|Max|Ultra)?\s*chip\b",
        text,
        re.IGNORECASE,
    )

    if apple_silicon:

        variant = (
            f" {apple_silicon.group(2)}"
            if apple_silicon.group(2)
            else ""
        )

        add_spec(
            "Processor",
            f"Apple M{apple_silicon.group(1)}{variant} chip",
        )

    else:

        processor_patterns = [
            r"(Snapdragon\s+[A-Za-z0-9\s]+?)(?=\s*\||\s*\d+MP|\s*$)",
            r"(Dimensity\s+[A-Za-z0-9\s]+?)(?=\s*\||\s*\d+MP|\s*$)",
            r"(MediaTek\s+[A-Za-z0-9\s]+?)(?=\s*\||\s*\d+MP|\s*$)",
            r"(Apple\s+A\d+\s*(?:Bionic|Pro)?)",
            r"(Exynos\s+[A-Za-z0-9\s]+?)(?=\s*\||\s*\d+MP|\s*$)",
            # Laptop chips (Intel/AMD). Appended after the phone
            # chipset patterns above rather than interleaved, since a
            # title never matches both groups and this keeps the
            # existing phone-pattern priority/order untouched.
            r"((?:\d+(?:st|nd|rd|th)\s+Gen\s+)?Intel\s+Core\s+i[3579](?:-[A-Za-z0-9]+)?)",
            r"(Intel\s+(?:Celeron|Pentium)(?:\s+[A-Za-z0-9]+)?)",
            r"(AMD\s+Ryzen\s+[3579](?:\s+[A-Za-z0-9]+)?)",
            r"(Ryzen\s+[3579](?:\s+[A-Za-z0-9]+)?)",
        ]

        for pattern in processor_patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:

                add_spec(
                    "Processor",
                    match.group(1),
                )

                break

    # --------------------------------------------------
    # Camera
    # --------------------------------------------------

    camera = re.search(
        r"(\d+)\s*MP[^|]*Camera",
        text,
        re.IGNORECASE,
    )

    if camera:

        add_spec(
            "Camera",
            f"{camera.group(1)} MP",
        )

    # --------------------------------------------------
    # Gorilla Glass
    # --------------------------------------------------

    glass = re.search(
        r"(Corning[®\s]*Gorilla[®\s]*Glass\s*[A-Za-z0-9]+)",
        text,
        re.IGNORECASE,
    )

    if glass:

        add_spec(
            "Screen Protection",
            glass.group(1),
        )

    # --------------------------------------------------
    # IP Rating
    # --------------------------------------------------

    ip_rating = re.search(
        r"\b(IP\d{2})\b",
        text,
        re.IGNORECASE,
    )

    if ip_rating:

        add_spec(
            "Water/Dust Resistance",
            ip_rating.group(1).upper(),
        )

    # --------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------

    unique = []

    seen = set()

    for spec in specifications:

        key = (
            spec["name"].lower(),
            spec["value"].lower(),
        )

        if key in seen:
            continue

        seen.add(key)

        unique.append(spec)

    return unique