import re


# Matches bare Apple A-series chip names (A15-A19, optionally
# "Pro"/"Bionic"), with or without a leading "apple " brand
# prefix -- e.g. "a18", "a18 pro", "apple a17 bionic". The
# lookaround assertions require a non-alphanumeric boundary on
# both sides so it can't match inside an unrelated token (e.g.
# "va18000"), and A14-and-below chips are deliberately excluded
# since they aren't in this task's recognized range.
_APPLE_CHIP_PATTERN = re.compile(
    r"(?<![a-z0-9])a1[5-9](?:\s*(?:pro|bionic))?(?![a-z0-9])"
)


# Bounded "<number>W" wattage token (e.g. "20W", "20 W",
# "30W adapter") -- \b on both sides so it can't match inside
# an unrelated word (there's no digit immediately before "w" in
# "Wi-Fi"/"With", so those never reach this pattern regardless).
_CHARGING_WATT_PATTERN = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*w\b"
)


# ============================================================
# HELPERS
# ============================================================

def _normalize_specs(specs):
    """
    Convert specification objects into a normalized dictionary.

    Handles:
    - Pydantic models
    - dictionaries
    - normal Python objects
    """

    normalized = {}

    for spec in specs or []:

        if isinstance(spec, dict):

            name = spec.get("name", "")
            value = spec.get("value", "")

        else:

            name = getattr(spec, "name", "")
            value = getattr(spec, "value", "")

        if not name:
            continue

        key = str(name).lower().strip()

        normalized[key] = str(
            value
        ).lower().strip()

    return normalized


def _find_spec(specs, keywords):
    """
    Find the best matching specification.

    Prefers exact/strong matches and avoids accidentally
    selecting unrelated fields.
    """

    # First pass: exact keyword in specification name
    for keyword in keywords:

        keyword = keyword.lower().strip()

        for name, value in specs.items():

            if name == keyword:
                return value

    # Second pass: keyword contained in specification name
    for keyword in keywords:

        keyword = keyword.lower().strip()

        for name, value in specs.items():

            if keyword in name:
                return value

    return None


def _find_all_specs(specs, keywords):
    """
    Find all matching specifications.

    Useful when multiple fields describe the same feature.
    """

    results = []

    for name, value in specs.items():

        for keyword in keywords:

            if keyword in name:

                results.append(
                    (name, value)
                )

                break

    return results


def _number(value):
    """
    Extract the first numeric value from a string.
    """

    if not value:
        return None

    match = re.search(
        r"\d+(?:\.\d+)?",
        str(value)
    )

    if match:

        return float(
            match.group()
        )

    return None


def _contains_any(value, keywords):
    """
    Check whether a value contains any keyword.
    """

    if not value:
        return False

    value = str(value).lower()

    return any(
        keyword in value
        for keyword in keywords
    )


# Requires a digit immediately (optionally with whitespace)
# before "mah" -- so "5000mah"/"5000 mah" match but an
# unrelated word ending in those letters doesn't -- or the
# spelled-out "milliamp hour(s)" form. Used to tell a genuine
# battery *capacity* figure apart from a *runtime* figure that
# happens to share the same "number + unit word" shape (e.g.
# "22 hours video playback" is not a capacity in mAh).
_BATTERY_CAPACITY_UNIT_PATTERN = re.compile(
    r"\d\s*mah\b|milliamp[\s-]?hours?\b"
)


def _looks_like_battery_capacity(value):
    """
    True only when `value` actually states a capacity unit
    (mAh / milliamp hour(s)), not just any number next to the
    word "battery" -- a runtime duration like "22 hours video
    playback" must never be scored as if it were mAh capacity.
    """

    if not value:
        return False

    return bool(
        _BATTERY_CAPACITY_UNIT_PATTERN.search(
            str(value)
        )
    )


def _charging_watt_tier(charging_watt_value):
    """
    Shared wattage-to-(points, reason) tiering, used by both the
    dedicated-Charging-field path and the fallback path below so
    the two paths can never award different points for the same
    stated wattage.
    """

    if charging_watt_value >= 100:
        return 10, "Ultra-Fast Charging"

    elif charging_watt_value >= 67:
        return 9, "Very Fast Charging"

    elif charging_watt_value >= 45:
        return 8, "Fast Charging"

    elif charging_watt_value >= 25:
        return 6, "Good Charging Speed"

    elif charging_watt_value >= 15:
        return 4, "Standard Charging"

    else:
        return 2, "Basic Charging"


def _extract_fallback_charging_watts(specs):
    """
    When no dedicated Charging-named field exists, look for a
    stated wattage inside closely-related already-extracted
    fields (Battery / Power And Battery / Battery & Charging,
    etc -- anything whose NAME already indicates battery/power
    context). Apple's Amazon listings are a common real example:
    charging speed is stated in prose inside "Power And Battery"
    instead of its own field.

    Only scans fields already found via `battery`/`power` name
    matching -- never arbitrary unrelated specs -- and only
    recognizes a properly bounded "<number>W" token. When more
    than one wattage is stated (e.g. separate wired/MagSafe/Qi
    figures), the highest is used, since that's the maximum
    charging capability actually claimed in the text. Returns
    None (never a guess) when no wattage is stated at all.
    """

    related = _find_all_specs(
        specs,
        ["battery", "power"],
    )

    watt_values = []

    for _name, value in related:

        for match in _CHARGING_WATT_PATTERN.finditer(str(value)):

            try:

                watt_values.append(
                    float(match.group(1))
                )

            except ValueError:

                continue

    if not watt_values:
        return None

    return max(watt_values)


def _extract_fallback_cellular_generation(title):
    """
    When no dedicated Cellular/Network/Connectivity-named field
    exists, fall back to detecting 5G/4G capability from the
    product title -- brand-neutral, since retailers virtually
    always state cellular generation in the title even when they
    omit it as a separate spec (Samsung, Apple, Xiaomi, OnePlus
    listings alike).

    Bounded to a standalone "5G"/"4G" token so it can never match
    inside an unrelated number like "128GB"/"4GB" storage or RAM
    (the immediately-following "B" removes the word boundary).
    5G is preferred over 4G when a title improbably states both,
    mirroring the dedicated-field check's own priority order.
    Returns "5g", "4g", or None -- never invents a generation
    that isn't literally stated.
    """

    if not title:
        return None

    title_lower = str(title).lower()

    if re.search(r"\b5g\b", title_lower):
        return "5g"

    if re.search(r"\b4g\b", title_lower):
        return "4g"

    return None


# Bounded "NNNxNNN" resolution shape only -- deliberately not
# generic digit extraction, so it can't be confused by an
# unrelated number in the same Display value (e.g. a ppi or
# diagonal-size figure).
_DISPLAY_RESOLUTION_PATTERN = re.compile(
    r"\d{3,4}\s*x\s*\d{3,4}"
)


def _extract_resolution_from_display(display_value):
    """
    When no dedicated Resolution/Maximum Display Resolution
    field exists, look for an explicit WxH resolution pattern
    inside the already-found Display field's value -- e.g.
    Apple's prose-style Display description states "2556x1179-
    pixel resolution" instead of exposing a dedicated Resolution
    field, and the same applies to any other brand's listing
    shaped this way.

    Returns the matched "WxH" substring for the existing
    resolution-tier logic below to parse and score exactly as it
    already does for a dedicated field -- this fallback only
    supplies a better input string, it does not duplicate or
    change any tier/weight. Returns None (never a guess) when no
    such pattern is present.
    """

    if not display_value:
        return None

    match = _DISPLAY_RESOLUTION_PATTERN.search(
        str(display_value)
    )

    if not match:
        return None

    return match.group(0)


# ============================================================
# SMARTPHONE SCORING
# ============================================================

def _score_smartphone(specs, title=None):

    score = 0
    reasons = []

    # ========================================================
    # PERFORMANCE — 25 POINTS
    # ========================================================

    processor = _find_spec(
        specs,
        [
            "processor",
            "cpu",
            "chipset",
            "chip",
        ]
    )

    performance_score = 0

    if processor:

        # ----------------------------------------------------
        # Snapdragon
        # ----------------------------------------------------

        if _contains_any(
            processor,
            [
                "snapdragon 8 elite",
                "snapdragon 8 gen 5",
                "snapdragon 8 gen 4",
                "snapdragon 8 gen",
            ]
        ):

            performance_score = 25
            reasons.append(
                "Flagship Processor"
            )

        elif _contains_any(
            processor,
            [
                "snapdragon 7+ gen",
                "snapdragon 7 gen",
                "snapdragon 7s gen",
            ]
        ):

            performance_score = 21
            reasons.append(
                "High Performance Processor"
            )

        elif "snapdragon 6" in processor:

            performance_score = 16
            reasons.append(
                "Good Midrange Processor"
            )

        elif "snapdragon 4" in processor:

            performance_score = 11
            reasons.append(
                "Entry-Level Processor"
            )

        # ----------------------------------------------------
        # MediaTek Dimensity
        # ----------------------------------------------------

        elif "dimensity 9" in processor:

            performance_score = 23
            reasons.append(
                "Flagship Performance Processor"
            )

        elif "dimensity 8" in processor:

            performance_score = 21
            reasons.append(
                "High Performance Processor"
            )

        elif "dimensity 7" in processor:

            performance_score = 16
            reasons.append(
                "Good Midrange Processor"
            )

        elif "dimensity 6" in processor:

            performance_score = 12
            reasons.append(
                "Entry-Level Processor"
            )

        # ----------------------------------------------------
        # Apple
        #
        # Amazon listings for iPhones frequently expose the
        # chip under a field literally named "Chip"/"CPU Model"
        # with just the bare model name as the value (e.g.
        # "A18", "A18 Pro") -- no "Apple" brand prefix, unlike
        # Snapdragon/Dimensity/Exynos values which always
        # include their brand name. _APPLE_CHIP_PATTERN matches
        # that bare form (with or without a leading "apple "),
        # bounded on both sides so it can't match inside an
        # unrelated alphanumeric token (e.g. "va18000" or a
        # stray "5a18"). Older/unlisted A-series chips (A14 and
        # below) intentionally fall through to the generic
        # bucket below, matching the task's explicit scope.
        # ----------------------------------------------------

        elif _APPLE_CHIP_PATTERN.search(processor):

            performance_score = 25
            reasons.append(
                "Flagship Processor"
            )

        # ----------------------------------------------------
        # Google Tensor
        # ----------------------------------------------------

        elif "tensor g" in processor:

            performance_score = 19
            reasons.append(
                "High Performance Processor"
            )

        # ----------------------------------------------------
        # Samsung Exynos
        #
        # Exynos is a distinct SKU-per-chip lineup (not a
        # single-leading-digit generation scheme like
        # Dimensity), so each recognized model is matched by
        # its full number rather than a numeric prefix. Point
        # values mirror the equivalent Snapdragon/Dimensity
        # tier for the same performance class -- newest
        # flagship-class chips (2200/2400/2500) land at the
        # same 23 points as Dimensity 9, the older 2100
        # flagship at the same 21 as Dimensity 8, and so on
        # down the scale. Any other/older Exynos model still
        # gets recognized (11 points, "lower-mid-range") rather
        # than falling into the generic unidentified-processor
        # bucket below.
        # ----------------------------------------------------

        elif _contains_any(
            processor,
            [
                "exynos 2200",
                "exynos 2400",
                "exynos 2500",
            ]
        ):

            performance_score = 23
            reasons.append(
                "Flagship Performance Processor"
            )

        elif "exynos 2100" in processor:

            performance_score = 21
            reasons.append(
                "High Performance Processor"
            )

        elif _contains_any(
            processor,
            [
                "exynos 1380",
                "exynos 1480",
            ]
        ):

            performance_score = 18
            reasons.append(
                "Upper Midrange Processor"
            )

        elif _contains_any(
            processor,
            [
                "exynos 1280",
                "exynos 1330",
            ]
        ):

            performance_score = 16
            reasons.append(
                "Good Midrange Processor"
            )

        elif "exynos" in processor:

            performance_score = 11
            reasons.append(
                "Entry-Level Processor"
            )

        # ----------------------------------------------------
        # Unisoc
        #
        # Unisoc's shipping lineup (Tiger T-series, A-series) is
        # consistently entry/budget-tier in the current market --
        # no genuine flagship Unisoc chip exists today, so every
        # recognized Unisoc value maps to the same Entry-Level
        # tier rather than guessing a higher one it hasn't earned.
        # ----------------------------------------------------

        elif "unisoc" in processor:

            performance_score = 11
            reasons.append(
                "Entry-Level Processor"
            )

        # ----------------------------------------------------
        # Huawei Kirin
        #
        # Matched by model-number prefix, mirroring the
        # Dimensity pattern above: the 9000/990 generation were
        # genuine flagship-class SoCs, the 8-series upper-mid,
        # the 7-series midrange. Any other/unlisted Kirin model
        # still falls to Entry-Level rather than the fully-
        # generic bucket below, since it's a recognized named
        # chip even without a confident specific tier.
        # ----------------------------------------------------

        elif _contains_any(
            processor,
            [
                "kirin 9000",
                "kirin 990",
            ]
        ):

            performance_score = 23
            reasons.append(
                "Flagship Performance Processor"
            )

        elif "kirin 8" in processor:

            performance_score = 21
            reasons.append(
                "High Performance Processor"
            )

        elif "kirin 7" in processor:

            performance_score = 16
            reasons.append(
                "Good Midrange Processor"
            )

        elif "kirin" in processor:

            performance_score = 11
            reasons.append(
                "Entry-Level Processor"
            )

        # ----------------------------------------------------
        # MediaTek Helio
        #
        # MediaTek's older/lower sub-brand, distinct from
        # Dimensity above. The higher-numbered gaming-focused
        # G-series (G90/G91/G96/G99) are genuinely capable
        # midrange chips; everything else in the Helio lineup
        # (lower G-series, P-series, A-series, and any unlisted
        # model) is entry/budget-tier -- Helio has no flagship
        # tier in the real market, so nothing here claims one.
        # ----------------------------------------------------

        elif _contains_any(
            processor,
            [
                "helio g99",
                "helio g96",
                "helio g91",
                "helio g90",
            ]
        ):

            performance_score = 16
            reasons.append(
                "Good Midrange Processor"
            )

        elif "helio" in processor:

            performance_score = 11
            reasons.append(
                "Entry-Level Processor"
            )

        else:

            performance_score = 8
            reasons.append(
                "Processor Detected"
            )

    score += performance_score

    # ========================================================
    # DISPLAY — 20 POINTS
    # ========================================================

    display = _find_spec(
        specs,
        [
            "display",
            "screen",
            "panel",
        ]
    )

    resolution = _find_spec(
        specs,
        [
            "resolution",
            "maximum display resolution",
        ]
    )

    # No dedicated Resolution field -- fall back to an explicit
    # WxH pattern inside the Display field's own value before
    # concluding no resolution info exists.
    if not resolution:

        resolution = _extract_resolution_from_display(
            display
        )

    refresh = _find_spec(
        specs,
        [
            "refresh rate",
            "refresh",
        ]
    )

    display_score = 0

    # --------------------------------------------------------
    # Panel quality — 10 points
    # --------------------------------------------------------

    if display:

        if "amoled" in display:

            display_score += 10
            reasons.append(
                "AMOLED Display"
            )

        elif "oled" in display:

            display_score += 10
            reasons.append(
                "OLED Display"
            )

        elif "p-oled" in display or "poled" in display:

            display_score += 10
            reasons.append(
                "pOLED Display"
            )

        elif "ips" in display:

            display_score += 6
            reasons.append(
                "IPS Display"
            )

        elif "lcd" in display:

            display_score += 4
            reasons.append(
                "LCD Display"
            )

    # --------------------------------------------------------
    # Resolution — 4 points
    # --------------------------------------------------------

    if resolution:

        resolution_numbers = re.findall(
            r"\d{3,5}",
            resolution
        )

        if len(resolution_numbers) >= 2:

            try:

                width = int(
                    resolution_numbers[0]
                )

                height = int(
                    resolution_numbers[1]
                )

                total_pixels = (
                    width * height
                )

                if total_pixels >= 3_000_000:

                    display_score += 4
                    reasons.append(
                        "High Resolution Display"
                    )

                elif total_pixels >= 2_000_000:

                    display_score += 3
                    reasons.append(
                        "Full HD+ Display"
                    )

                elif total_pixels >= 1_500_000:

                    display_score += 2

                else:

                    display_score += 1

            except ValueError:

                pass

    # --------------------------------------------------------
    # Refresh rate — 6 points
    # --------------------------------------------------------

    refresh_value = _number(
        refresh
    )

    if refresh_value is not None:

        if refresh_value >= 144:

            display_score += 6
            reasons.append(
                "Very High Refresh Rate"
            )

        elif refresh_value >= 120:

            display_score += 5
            reasons.append(
                "120Hz Display"
            )

        elif refresh_value >= 90:

            display_score += 4
            reasons.append(
                "90Hz Display"
            )

        elif refresh_value >= 60:

            display_score += 2

        else:

            display_score += 1

    score += min(
        display_score,
        20
    )

    # ========================================================
    # BATTERY — 15 POINTS
    # ========================================================

    battery = _find_spec(
        specs,
        [
            "battery capacity",
            "battery",
        ]
    )

    battery_value = _number(
        battery
    )

    battery_score = 0

    # Only score as capacity when the matched text actually
    # states a capacity unit (see _looks_like_battery_capacity
    # docstring) -- otherwise leave battery_score at 0 rather
    # than inventing a capacity from a runtime figure.
    if (
        battery_value is not None
        and _looks_like_battery_capacity(battery)
    ):

        if battery_value >= 7000:

            battery_score = 12
            reasons.append(
                "Excellent Battery"
            )

        elif battery_value >= 6000:

            battery_score = 11
            reasons.append(
                "Very Large Battery"
            )

        elif battery_value >= 5000:

            battery_score = 9
            reasons.append(
                "Good Battery"
            )

        elif battery_value >= 4500:

            battery_score = 7
            reasons.append(
                "Decent Battery"
            )

        elif battery_value >= 4000:

            battery_score = 5
            reasons.append(
                "Average Battery"
            )

        else:

            battery_score = 3
            reasons.append(
                "Small Battery"
            )

    # --------------------------------------------------------
    # Battery life information — up to 3 points
    # --------------------------------------------------------

    battery_life = _find_spec(
        specs,
        [
            "battery average life",
            "battery life",
        ]
    )

    if battery_life:

        if "2 days" in battery_life:

            battery_score += 3

        elif "1 day" in battery_life:

            battery_score += 2

        else:

            battery_score += 1

    # --------------------------------------------------------
    # Battery score maximum = 15
    # --------------------------------------------------------

    score += min(
        battery_score,
        15
    )

    # ========================================================
    # CAMERA — 10 POINTS
    # ========================================================

    rear_camera = _find_spec(
        specs,
        [
            "rear facing camera photo sensor resolution",
            "rear camera",
            "optical sensor resolution",
            "camera",
        ]
    )

    front_camera = _find_spec(
        specs,
        [
            "front photo sensor resolution",
            "front camera",
        ]
    )

    video = _find_spec(
        specs,
        [
            "video capture resolution",
            "effective video resolution",
            "video resolution",
        ]
    )

    camera_score = 0

    # --------------------------------------------------------
    # Rear camera
    # --------------------------------------------------------

    rear_value = _number(
        rear_camera
    )

    if rear_value is not None:

        if rear_value >= 200:

            camera_score += 6

        elif rear_value >= 108:

            camera_score += 6

        elif rear_value >= 64:

            camera_score += 5

        elif rear_value >= 50:

            camera_score += 4

        elif rear_value >= 48:

            camera_score += 4

        elif rear_value >= 12:

            camera_score += 3

        else:

            camera_score += 1

    # --------------------------------------------------------
    # Front camera
    # --------------------------------------------------------

    front_value = _number(
        front_camera
    )

    if front_value is not None:

        if front_value >= 32:

            camera_score += 2

        elif front_value >= 16:

            camera_score += 2

        elif front_value >= 12:

            camera_score += 1

        elif front_value >= 8:

            camera_score += 1

    # --------------------------------------------------------
    # 4K video
    # --------------------------------------------------------

    if video:

        if "4k" in video:

            camera_score += 2
            reasons.append(
                "4K Video Recording"
            )

    # --------------------------------------------------------
    # Maximum camera score
    # --------------------------------------------------------

    camera_score = min(
        camera_score,
        10
    )

    score += camera_score

    if camera_score >= 5:

        reasons.append(
            "Good Camera"
        )

    # ========================================================
    # RAM + STORAGE — 10 POINTS
    # ========================================================

    ram = _find_spec(
        specs,
        [
            "ram",
            "memory",
        ]
    )

    storage = _find_spec(
        specs,
        [
            "storage",
        ]
    )

    memory_score = 0

    ram_value = _number(
        ram
    )

    if ram_value is not None:

        if ram_value >= 16:

            memory_score += 5
            reasons.append(
                "Excellent RAM"
            )

        elif ram_value >= 12:

            memory_score += 4

        elif ram_value >= 8:

            memory_score += 4
            reasons.append(
                "Good RAM"
            )

        elif ram_value >= 6:

            memory_score += 3
            reasons.append(
                "Adequate RAM"
            )

        elif ram_value >= 4:

            memory_score += 2

        else:

            memory_score += 1

    storage_value = _number(
        storage
    )

    if storage_value is not None:

        if storage and "tb" in storage:

            memory_score += 5
            reasons.append(
                "Excellent Storage"
            )

        elif storage_value >= 512:

            memory_score += 5
            reasons.append(
                "Excellent Storage"
            )

        elif storage_value >= 256:

            memory_score += 4
            reasons.append(
                "Large Storage"
            )

        elif storage_value >= 128:

            memory_score += 3
            reasons.append(
                "Good Storage"
            )

        elif storage_value >= 64:

            memory_score += 2

        else:

            memory_score += 1

    score += min(
        memory_score,
        10
    )

    # ========================================================
    # CHARGING — 10 POINTS
    # ========================================================

    charging_watts = _find_spec(
        specs,
        [
            "charging",
            "fast charging",
            "charging power",
        ]
    )

    charging_time = _find_spec(
        specs,
        [
            "battery charge time",
            "charge time",
            "charging time",
        ]
    )

    charging_watt_value = _number(
        charging_watts
    )

    charging_time_value = _number(
        charging_time
    )

    # --------------------------------------------------------
    # Charging time takes priority
    # --------------------------------------------------------

    if charging_time_value is not None:

        if charging_time_value <= 45:

            score += 10
            reasons.append(
                "Very Fast Charging"
            )

        elif charging_time_value <= 60:

            score += 9
            reasons.append(
                "Fast Charging"
            )

        elif charging_time_value <= 90:

            score += 7
            reasons.append(
                "Good Charging Speed"
            )

        elif charging_time_value <= 120:

            score += 5
            reasons.append(
                "Moderate Charging Speed"
            )

        else:

            score += 3
            reasons.append(
                "Slow Charging"
            )

    # --------------------------------------------------------
    # Otherwise use charging wattage
    # --------------------------------------------------------

    elif charging_watt_value is not None:

        points, reason = _charging_watt_tier(
            charging_watt_value
        )

        score += points
        reasons.append(reason)

    # --------------------------------------------------------
    # Neither a dedicated Charging field nor a charging-related
    # wattage/time value -- fall back to a wattage stated inside
    # closely-related battery/power fields before concluding no
    # charging info exists at all. Never invents a number: if
    # none is found, no charging points are awarded, same as
    # today.
    # --------------------------------------------------------

    else:

        fallback_watts = _extract_fallback_charging_watts(
            specs
        )

        if fallback_watts is not None:

            points, reason = _charging_watt_tier(
                fallback_watts
            )

            score += points
            reasons.append(reason)

    # ========================================================
    # DURABILITY — 5 POINTS
    # ========================================================

    durability_score = 0

    protection = _find_spec(
        specs,
        [
            "screen protection",
            "glass",
        ]
    )

    water_resistance = _find_spec(
        specs,
        [
            "water/dust",
            "water resistance",
            "ip rating",
            "water",
            "dust",
        ]
    )

    if protection:

        if "gorilla" in protection:

            durability_score += 2
            reasons.append(
                "Gorilla Glass Protection"
            )

        else:

            durability_score += 1

    if water_resistance:

        ip_match = re.search(
            r"ip(\d{2})",
            water_resistance
        )

        if ip_match:

            ip_value = int(
                ip_match.group(1)
            )

            if ip_value >= 68:

                durability_score += 3
                reasons.append(
                    "Strong Water Resistance"
                )

            elif ip_value >= 65:

                durability_score += 3
                reasons.append(
                    "IP65 Protection"
                )

            elif ip_value >= 54:

                durability_score += 2
                reasons.append(
                    "Water Resistance"
                )

    score += min(
        durability_score,
        5
    )

    # ========================================================
    # CONNECTIVITY — 5 POINTS
    # ========================================================

    cellular = _find_spec(
        specs,
        [
            "cellular",
            "network",
            "connectivity",
        ]
    )

    if cellular:

        if "5g" in cellular:

            score += 5
            reasons.append(
                "5G Connectivity"
            )

        elif "4g" in cellular:

            score += 3
            reasons.append(
                "4G Connectivity"
            )

    # --------------------------------------------------------
    # No dedicated Cellular/Network/Connectivity field -- fall
    # back to the product title, which retailers virtually
    # always state cellular generation in even when they omit
    # it as a separate spec (brand-neutral: Samsung, Apple,
    # Xiaomi, OnePlus listings alike). Never invents a
    # generation that isn't literally stated in the title.
    # --------------------------------------------------------

    else:

        fallback_generation = _extract_fallback_cellular_generation(
            title
        )

        if fallback_generation == "5g":

            score += 5
            reasons.append(
                "5G Connectivity"
            )

        elif fallback_generation == "4g":

            score += 3
            reasons.append(
                "4G Connectivity"
            )

    # ========================================================
    # SPECIFICATION COVERAGE
    # ========================================================

    if len(specs) >= 15:

        reasons.append(
            "Detailed Specifications Available"
        )

    return score, reasons


# ============================================================
# LAPTOP SCORING
# ============================================================

def _score_laptop(specs):

    score = 0
    reasons = []

    cpu = _find_spec(
        specs,
        [
            "processor",
            "cpu",
            "chip",
        ]
    )

    if cpu:

        if any(
            x in cpu
            for x in [
                "i9",
                "ultra 9",
                "ryzen 9",
            ]
        ):

            score += 30
            reasons.append(
                "Flagship Processor"
            )

        elif any(
            x in cpu
            for x in [
                "i7",
                "ultra 7",
                "ryzen 7",
            ]
        ):

            score += 27
            reasons.append(
                "High Performance Processor"
            )

        elif any(
            x in cpu
            for x in [
                "i5",
                "ultra 5",
                "ryzen 5",
            ]
        ):

            score += 23
            reasons.append(
                "Powerful Processor"
            )

        else:

            score += 12
            reasons.append(
                "Processor Detected"
            )

    ram = _number(
        _find_spec(
            specs,
            [
                "ram",
                "memory",
            ]
        )
    )

    if ram:

        if ram >= 32:

            score += 20
            reasons.append(
                "Excellent RAM"
            )

        elif ram >= 16:

            score += 16
            reasons.append(
                "Very Good RAM"
            )

        elif ram >= 8:

            score += 10
            reasons.append(
                "Adequate RAM"
            )

        else:

            score += 5
            reasons.append(
                "Limited RAM"
            )

    storage = _find_spec(
        specs,
        [
            "storage",
            "ssd",
            "hard drive",
        ]
    )

    if storage:

        if "2tb" in storage:

            score += 15
            reasons.append(
                "Large Storage"
            )

        elif "1tb" in storage:

            score += 14
            reasons.append(
                "Large Storage"
            )

        elif "512gb" in storage:

            score += 12
            reasons.append(
                "Fast SSD"
            )

        elif "ssd" in storage:

            score += 10
            reasons.append(
                "SSD Storage"
            )

    display = _find_spec(
        specs,
        [
            "display",
            "screen",
            "resolution",
        ]
    )

    if display:

        if "oled" in display:

            score += 15
            reasons.append(
                "OLED Display"
            )

        elif "4k" in display:

            score += 15
            reasons.append(
                "4K Display"
            )

        elif (
            "2k" in display
            or "qhd" in display
        ):

            score += 13
            reasons.append(
                "High Resolution Display"
            )

        elif "fhd" in display:

            score += 10
            reasons.append(
                "Full HD Display"
            )

    battery = _number(
        _find_spec(
            specs,
            [
                "battery",
            ]
        )
    )

    if battery:

        if battery >= 70:

            score += 10
            reasons.append(
                "Large Battery"
            )

        elif battery >= 50:

            score += 8
            reasons.append(
                "Good Battery"
            )

        else:

            score += 5

    return score, reasons


# ============================================================
# GENERIC ELECTRONICS
# ============================================================

def _score_generic(specs):

    score = 0
    reasons = []

    useful_specs = len(specs)

    if useful_specs >= 12:

        score += 70
        reasons.append(
            "Detailed Specifications"
        )

    elif useful_specs >= 8:

        score += 60
        reasons.append(
            "Good Specification Coverage"
        )

    elif useful_specs >= 5:

        score += 50
        reasons.append(
            "Basic Specification Coverage"
        )

    elif useful_specs >= 3:

        score += 40
        reasons.append(
            "Limited Specification Coverage"
        )

    else:

        score += 25
        reasons.append(
            "Insufficient Specifications"
        )

    return score, reasons


# ============================================================
# MAIN RECOMMENDATION FUNCTION
# ============================================================

def recommend(
    specs,
    category="other",
    title=None
):

    normalized_specs = _normalize_specs(
        specs
    )

    # --------------------------------------------------------
    # Category-specific scoring
    #
    # `title` is optional and defaults to None -- existing
    # callers that don't pass it keep working unchanged (only
    # used by the smartphone connectivity title-fallback).
    # --------------------------------------------------------

    if category == "smartphone":

        score, reasons = _score_smartphone(
            normalized_specs,
            title=title
        )

    elif category == "laptop":

        score, reasons = _score_laptop(
            normalized_specs
        )

    else:

        score, reasons = _score_generic(
            normalized_specs
        )

    # --------------------------------------------------------
    # Keep score within 0–100
    # --------------------------------------------------------

    score = max(
        0,
        min(
            int(score),
            100
        )
    )

    # --------------------------------------------------------
    # Recommendation
    # --------------------------------------------------------

    if score >= 80:

        recommendation = "BUY"

    elif score >= 60:

        recommendation = "CONSIDER"

    else:

        recommendation = "AVOID"

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    if reasons:

        summary = (
            f"{category.title()} evaluation "
            f"scored {score}/100. "
            f"Key factors: "
            f"{', '.join(reasons)}."
        )

    else:

        summary = (
            f"{category.title()} evaluation "
            f"scored {score}/100. "
            "There was not enough specification "
            "data for a detailed evaluation."
        )

    return {
        "score": score,
        "recommendation": recommendation,
        "reasons": reasons,
        "summary": summary,
    }