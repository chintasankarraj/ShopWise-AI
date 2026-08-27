import re


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


# ============================================================
# SMARTPHONE SCORING
# ============================================================

def _score_smartphone(specs):

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
        # ----------------------------------------------------

        elif any(
            x in processor
            for x in [
                "apple a18",
                "apple a17",
                "apple a16",
            ]
        ):

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

    if battery_value is not None:

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

        if charging_watt_value >= 100:

            score += 10
            reasons.append(
                "Ultra-Fast Charging"
            )

        elif charging_watt_value >= 67:

            score += 9
            reasons.append(
                "Very Fast Charging"
            )

        elif charging_watt_value >= 45:

            score += 8
            reasons.append(
                "Fast Charging"
            )

        elif charging_watt_value >= 25:

            score += 6
            reasons.append(
                "Good Charging Speed"
            )

        elif charging_watt_value >= 15:

            score += 4
            reasons.append(
                "Standard Charging"
            )

        else:

            score += 2
            reasons.append(
                "Basic Charging"
            )
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
    category="other"
):

    normalized_specs = _normalize_specs(
        specs
    )

    # --------------------------------------------------------
    # Category-specific scoring
    # --------------------------------------------------------

    if category == "smartphone":

        score, reasons = _score_smartphone(
            normalized_specs
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