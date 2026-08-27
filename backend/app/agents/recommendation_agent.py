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


# Bare Apple Silicon chip names -- "m1".."m4", optionally followed
# by "ultra"/"max"/"pro" (e.g. "m3", "m3 pro", "m2 max", "m1
# ultra"). Bounded on both sides so it can't match inside an
# unrelated token. This alone would also match Intel's old "Core
# m3/m5/m7" (Y-series) branding, so callers must additionally
# require the word "apple" to appear in the same string before
# treating a match as Apple Silicon -- Amazon's own MacBook
# listings always include "Apple" in the processor field, so this
# costs no real recall while closing that collision.
_APPLE_SILICON_PATTERN = re.compile(
    r"(?<![a-z0-9])m([1-4])(?:\s+(ultra|max|pro))?(?![a-z0-9])"
)

# Snapdragon X-series laptop chips -- "Snapdragon X Elite" /
# "Snapdragon X Plus" / bare "Snapdragon X" (unspecified variant).
# Deliberately does NOT match "Snapdragon 8 Elite" or other
# Snapdragon *phone* chips, since there is no literal "x" token
# right after "snapdragon" in those.
_SNAPDRAGON_X_PATTERN = re.compile(
    r"snapdragon\s*x\s*(elite|plus)?\b"
)

# A dedicated GPU model number stated as "RTX 4050", "GTX 1650",
# "Radeon RX 6600", or "Arc A730"/"Arc B580" -- the vendor tokens
# most laptop-GPU listings on Amazon actually use.
_GPU_DEDICATED_MODEL_PATTERN = re.compile(
    r"\b(?:rtx|gtx|radeon\s*rx|arc\s*[ab])\s*(\d{3,4})\b"
)

# A newer/higher-end *integrated* AMD Radeon iGPU model number
# (e.g. "Radeon 780M", "Radeon 610M") -- distinct from the
# dedicated Radeon RX pattern above (no "rx" token).
_GPU_INTEGRATED_AMD_MODEL_PATTERN = re.compile(
    r"\bradeon\s*(\d{3})m?\b"
)

# An explicit "<N>-core GPU" figure, as Apple's own listings state
# (e.g. "8‑core CPU and 10‑core GPU") -- brand-neutral: matches
# whichever vendor's listing happens to state a GPU core count.
_GPU_CORE_COUNT_PATTERN = re.compile(
    r"(\d+)[\s‑-]*core\s*gpu"
)

_ARC_BRAND_PATTERN = re.compile(r"\barc\b")
_IRIS_XE_PATTERN = re.compile(r"\biris\s*xe\b")

# A refresh rate stated in prose (e.g. buried inside a Display
# field's own value) -- requires the literal "Hz" unit so an
# unrelated number can never be misread as a refresh rate.
_REFRESH_RATE_TEXT_PATTERN = re.compile(
    r"\b(\d{2,3})\s*hz\b"
)

# A battery capacity explicitly stated in watt-hours ("52.6 Watt
# Hours", "52.6Wh", "52.6 wh") -- requires the unit so a duration
# ("18 Hours") or a non-numeric descriptor ("Lithium Ion") is
# never misread as a capacity figure.
_WATT_HOUR_UNIT_PATTERN = re.compile(
    r"\d\s*(?:watt[\s-]?hours?|wh)\b"
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


def _find_spec(specs, keywords, exclude=None):
    """
    Find the best matching specification.

    Prefers exact/strong matches and avoids accidentally
    selecting unrelated fields. `exclude` is an optional list of
    substrings that disqualify a field name outright regardless
    of which pass would otherwise match it -- used so a
    "Video Processor"/"Graphics Co Processor" (GPU) field can
    never be mistaken for the CPU, even when no dedicated
    processor field exists at all.
    """

    exclude = [
        term.lower().strip()
        for term in (exclude or [])
    ]

    def _is_excluded(name):
        return any(term in name for term in exclude)

    # First pass: exact keyword in specification name
    for keyword in keywords:

        keyword = keyword.lower().strip()

        for name, value in specs.items():

            if _is_excluded(name):
                continue

            if name == keyword:
                return value

    # Second pass: specification name starts with the keyword
    # (e.g. "processor type", "cpu model"). This is checked
    # before the loose "keyword anywhere in name" pass below so
    # a compound field that merely *mentions* the keyword at the
    # end -- like "video processor" for a "processor" lookup --
    # can't outrank the actual dedicated field.
    for keyword in keywords:

        keyword = keyword.lower().strip()

        for name, value in specs.items():

            if _is_excluded(name):
                continue

            if name.startswith(keyword):
                return value

    # Third pass: keyword contained anywhere in specification
    # name (last-resort fallback, unchanged from before).
    for keyword in keywords:

        keyword = keyword.lower().strip()

        for name, value in specs.items():

            if _is_excluded(name):
                continue

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


def _normalize_unit_spacing(value):
    """
    Collapse whitespace/hyphen separators between a digit and the
    unit letters that follow it, so "1 TB", "1-TB", and "1TB" all
    compare equal to the same substring checks. Does not touch
    the digits or letters themselves, so already-tight values
    ("1tb") pass through unchanged.
    """

    if not value:
        return value

    return re.sub(
        r"(\d)[\s-]+(?=[a-zA-Z])",
        r"\1",
        value,
    )


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
# LAPTOP SCORING HELPERS
# ============================================================

def _apple_silicon_tier(cpu):
    """
    Evidence-based tier for an Apple Silicon laptop chip, derived
    from Apple's own product-line hierarchy (base < Pro < Max /
    Ultra), slotted into the SAME point buckets already used for
    Intel/AMD (no new point values invented). Requires "apple" to
    co-occur in the string -- see _APPLE_SILICON_PATTERN's comment
    for why. Returns None for any non-Apple-Silicon string.
    """

    if "apple" not in cpu:
        return None

    match = _APPLE_SILICON_PATTERN.search(cpu)

    if not match:
        return None

    variant = match.group(2)

    if variant in ("ultra", "max"):
        return 30, "Flagship Processor"

    elif variant == "pro":
        return 27, "High Performance Processor"

    else:
        return 23, "Powerful Processor"


def _snapdragon_x_tier(cpu):
    """
    Evidence-based tier for a Snapdragon X-series laptop chip.
    X Elite is genuinely flagship/H-series-class in real-world
    multi-core benchmarks -- tiered at the same bucket as i7/
    Ultra 7/Ryzen 7, not i9, to stay conservative rather than
    overclaim. X Plus is a cut-down variant of the same family,
    one bucket down. A bare "Snapdragon X" with no stated variant
    returns None so the caller's existing generic fallback
    handles it -- we don't know enough to pick a tier.
    """

    match = _SNAPDRAGON_X_PATTERN.search(cpu)

    if not match:
        return None

    variant = match.group(1)

    if variant == "elite":
        return 27, "High Performance Processor"

    elif variant == "plus":
        return 23, "Powerful Processor"

    return None


_PANEL_TECH_RANK = {
    "oled": 3,
    "ips": 2,
    "lcd": 1,
    "led": 1,
}


def _laptop_panel_tech(specs):
    """
    Some real listings expose the actual panel technology only in
    a separate "Display Technology" field while the primary
    "Display" field states just the generic backlight type
    ("LED") -- e.g. a real audited gaming laptop's "Display" field
    said "LED" while "Display Technology" separately said "Ips".
    Checks every Display/Screen/Panel-named field and keeps
    whichever value names the MOST SPECIFIC recognized panel
    technology, rather than trusting whichever field a plain
    keyword lookup happens to resolve to first.
    """

    candidates = _find_all_specs(
        specs,
        ["display", "screen", "panel"],
    )

    best_tech = None
    best_rank = -1

    for _name, value in candidates:

        for tech, rank in _PANEL_TECH_RANK.items():

            if tech in value and rank > best_rank:
                best_tech = tech
                best_rank = rank

    return best_tech


def _dedicated_gpu_tier(model_number):
    """
    Tiers a dedicated GPU by its model number, within its own
    vendor's naming convention -- NVIDIA/Intel encode the tier in
    the last two digits (4050/4060/4070/4080/4090), while AMD's
    Radeon RX line encodes it in the hundreds digit instead
    (RX 7600/7700/7800/7900, always a round hundred). Applying the
    tens-place rule to an AMD number would misread e.g. 7800 as
    tier "00" -- so an AMD-shaped (round-hundred) number gets its
    own, coarser bucket boundaries instead of being forced onto
    NVIDIA's finer-grained scale.
    """

    remainder = model_number % 1000

    if remainder != 0 and remainder % 100 == 0:

        hundreds = remainder // 100

        if hundreds >= 9:
            return 12, "Flagship Dedicated GPU"

        elif hundreds >= 7:
            return 10, "High-End Dedicated GPU"

        elif hundreds >= 6:
            return 8, "Capable Dedicated GPU"

        else:
            return 6, "Entry Dedicated GPU"

    suffix = model_number % 100

    if suffix >= 80:
        return 12, "Flagship Dedicated GPU"

    elif suffix >= 70:
        return 10, "High-End Dedicated GPU"

    elif suffix >= 60:
        return 8, "Capable Dedicated GPU"

    elif suffix >= 40:
        return 6, "Entry Dedicated GPU"

    else:
        return 4, "Dedicated GPU Detected"


def _dedicated_gpu_tier_from_vram(vram_gb):
    """
    Fallback dedicated-GPU tiering by VRAM size, used only when no
    recognizable model number could be read from the GPU-text
    fields -- a real audited gaming laptop's "Graphics Co
    Processor" field named its CPU's integrated-graphics brand
    instead of its actual discrete GPU, while "Graphics Ram Size"
    (a separate, structured field) correctly stated the real
    card's dedicated VRAM.

    Thresholds follow the real-world VRAM bands entry/capable/
    high-end/flagship dedicated laptop GPUs actually ship with
    across recent generations (entry-tier RTX 3050/4050-class
    cards commonly carry 6GB; 8GB is the common capable/upper-mid
    band; 10-12GB+ is high-end/flagship) -- calibrated against
    that general landscape, not against any single tested product.
    A round-trip check: this must never rate a VRAM-only reading
    higher than what the SAME real card would score via a reliable
    model number on the sibling function above, for any VRAM size
    a model-number-tiered card in that bucket would actually ship
    with -- see test_laptop_scoring_round2.py's cross-path parity
    checks.
    """

    if vram_gb >= 16:
        return 12, "Flagship Dedicated GPU"

    elif vram_gb >= 10:
        return 10, "High-End Dedicated GPU"

    elif vram_gb >= 8:
        return 8, "Capable Dedicated GPU"

    elif vram_gb >= 6:
        return 6, "Entry Dedicated GPU"

    else:
        return 4, "Dedicated GPU Detected"


def _score_laptop_gpu(specs, title=None):
    """
    Laptop GPU dimension. "Graphics Card Description"/"Graphics
    Description" (Dedicated vs Integrated) is the one field this
    session's real-product audit found consistently present and
    reliable across every tested laptop, so it gates everything
    else -- a laptop is never credited with a dedicated-GPU tier
    unless this field actually says so.

    Within a confirmed-dedicated laptop, the specific model text
    is not always reliable: try the model-number pattern first,
    fall back to the also-structured VRAM size, and if neither is
    available, credit only that a dedicated GPU exists (never
    invent a specific tier from nothing).

    Integrated graphics are NOT rewarded merely for existing --
    only recognized, capability-differentiating evidence (Iris Xe,
    Arc branding, a newer high-end integrated AMD Radeon model, or
    an explicit "N-core GPU" figure as Apple's listings state)
    earns a modest bonus. The title is checked only as a last
    resort for this same narrow integrated-capability evidence
    (e.g. "Intel Arc Graphics" sometimes appears only in the
    title, never in a structured field) -- it is never used to
    promote a laptop into the dedicated tier, since that would
    override the structured Dedicated/Integrated field.
    """

    description = _find_spec(
        specs,
        ["graphics card description", "graphics description"],
    )

    gpu_text_fields = _find_all_specs(
        specs,
        ["graphics co processor", "video processor", "cpu model number"],
    )

    gpu_text = " ".join(value for _name, value in gpu_text_fields)

    is_dedicated = bool(description) and "dedicated" in description

    if is_dedicated:

        model_match = _GPU_DEDICATED_MODEL_PATTERN.search(gpu_text)

        if model_match:
            return _dedicated_gpu_tier(int(model_match.group(1)))

        vram = _number(
            _find_spec(specs, ["graphics ram size"])
        )

        if vram:
            return _dedicated_gpu_tier_from_vram(vram)

        return 4, "Dedicated GPU Detected"

    combined_text = f"{gpu_text} {title or ''}".lower()

    if not combined_text.strip():
        return 0, None

    core_match = _GPU_CORE_COUNT_PATTERN.search(combined_text)

    if core_match:

        core_count = int(core_match.group(1))

        if core_count >= 16:
            return 6, "High Core-Count Integrated GPU"

        elif core_count >= 8:
            return 3, "Capable Integrated Graphics"

    if _IRIS_XE_PATTERN.search(combined_text):
        return 3, "Capable Integrated Graphics"

    if _ARC_BRAND_PATTERN.search(combined_text):
        return 3, "Capable Integrated Graphics"

    amd_match = _GPU_INTEGRATED_AMD_MODEL_PATTERN.search(combined_text)

    if amd_match and int(amd_match.group(1)) >= 740:
        return 3, "Capable Integrated Graphics"

    return 0, None


def _looks_like_watt_hour_capacity(value):
    """
    True only when `value` explicitly states a watt-hour unit --
    mirrors _looks_like_battery_capacity's mAh-unit-awareness so a
    plain duration ("18 Hours") is never misread as a capacity.
    """

    if not value:
        return False

    return bool(
        _WATT_HOUR_UNIT_PATTERN.search(
            str(value)
        )
    )


def _extract_laptop_battery_wh(specs):
    """
    Laptop battery capacity, in watt-hours. "Battery Cell Type"
    (e.g. "Lithium Ion") is the most commonly-present battery-
    named field across real listings but is never numeric, so a
    plain _find_spec(["battery"]) lookup silently resolves to it
    and returns nothing -- confirmed live across every laptop in
    this session's audit, all of which separately stated a real
    watt-hour figure under a different field name.

    Requires an explicit watt-hour unit before accepting a number
    (never misreads an Hours duration as capacity), and prefers a
    field whose name says "energy content" -- the least ambiguous
    naming for capacity -- over any other battery/power-named
    field that also happens to state Wh, since "Battery Life" is
    inconsistently either a duration or, on some listings, itself
    stated in watt-hours.
    """

    candidates = _find_all_specs(
        specs,
        ["battery", "power"],
    )

    energy_content_candidates = [
        (name, value)
        for name, value in candidates
        if "energy content" in name
    ]

    for _name, value in energy_content_candidates + candidates:

        if _looks_like_watt_hour_capacity(value):
            return _number(value)

    return None


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
        ],
        exclude=[
            "video processor",
            "graphics",
        ],
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

def _score_laptop(specs, title=None):

    score = 0
    reasons = []

    # ========================================================
    # PROCESSOR — 30 POINTS
    # ========================================================

    cpu = _find_spec(
        specs,
        [
            "processor",
            "cpu",
            "chip",
        ],
        exclude=[
            "video processor",
            "graphics",
        ],
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

            apple_tier = _apple_silicon_tier(cpu)
            snapdragon_tier = _snapdragon_x_tier(cpu)

            if apple_tier:

                points, reason = apple_tier
                score += points
                reasons.append(reason)

            elif snapdragon_tier:

                points, reason = snapdragon_tier
                score += points
                reasons.append(reason)

            else:

                score += 12
                reasons.append(
                    "Processor Detected"
                )

    # ========================================================
    # RAM — 20 POINTS
    # ========================================================

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

    # ========================================================
    # STORAGE — 15 POINTS
    # ========================================================

    storage = _find_spec(
        specs,
        [
            "storage",
            "ssd",
            "hard drive",
        ]
    )

    storage = _normalize_unit_spacing(storage)

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

    # ========================================================
    # DISPLAY — panel 8 + resolution 4 + refresh rate 6 = 18
    # ========================================================

    panel_tech = _laptop_panel_tech(specs)

    if panel_tech == "oled":

        score += 8
        reasons.append(
            "OLED Display"
        )

    elif panel_tech == "ips":

        score += 5
        reasons.append(
            "IPS Display"
        )

    elif panel_tech in (
        "lcd",
        "led",
    ):

        score += 2
        reasons.append(
            "Display Detected"
        )

    resolution = _find_spec(
        specs,
        [
            "resolution",
            "maximum display resolution",
            "native resolution",
        ]
    )

    if not resolution:

        display_value = _find_spec(
            specs,
            ["display"]
        )

        resolution = _extract_resolution_from_display(
            display_value
        )

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

                    score += 4
                    reasons.append(
                        "High Resolution Display"
                    )

                elif total_pixels >= 2_000_000:

                    score += 3
                    reasons.append(
                        "Full HD+ Display"
                    )

                elif total_pixels >= 1_500_000:

                    score += 2

                else:

                    score += 1

            except ValueError:

                pass

    refresh = _find_spec(
        specs,
        [
            "refresh rate",
            "refresh",
        ]
    )

    if not refresh:

        display_value = _find_spec(
            specs,
            ["display"]
        )

        if display_value:

            refresh_match = _REFRESH_RATE_TEXT_PATTERN.search(
                display_value
            )

            if refresh_match:
                refresh = refresh_match.group(0)

    refresh_value = _number(
        refresh
    )

    if refresh_value is not None:

        if refresh_value >= 144:

            score += 6
            reasons.append(
                "Very High Refresh Rate"
            )

        elif refresh_value >= 120:

            score += 5
            reasons.append(
                "120Hz Display"
            )

        elif refresh_value >= 90:

            score += 4
            reasons.append(
                "90Hz Display"
            )

        elif refresh_value >= 60:

            score += 2

        else:

            score += 1

    # ========================================================
    # GPU — up to 12 points
    # ========================================================

    gpu_points, gpu_reason = _score_laptop_gpu(
        specs,
        title=title,
    )

    if gpu_points:

        score += gpu_points
        reasons.append(
            gpu_reason
        )

    # ========================================================
    # BATTERY — 10 POINTS
    # ========================================================

    battery = _extract_laptop_battery_wh(
        specs
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
            reasons.append(
                "Battery Detected"
            )

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
            normalized_specs,
            title=title
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