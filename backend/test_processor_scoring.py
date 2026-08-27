from app.agents.recommendation_agent import recommend


def reasons_for(processor_value):
    """
    Score a minimal smartphone spec set containing only a
    Processor field, so the processor-tier reason can be
    checked in isolation from the other scoring dimensions.
    """

    specs = [
        {"name": "Processor", "value": processor_value},
    ]

    result = recommend(specs, "smartphone")

    return result["reasons"], result["score"]


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


# --------------------------------------------------------------
# New: Exynos recognition (Issue 1 fix)
# --------------------------------------------------------------

reasons, score = reasons_for("Exynos 1380 S5E8835")
check(
    "Exynos 1380 -> recognized as Upper Midrange (not generic 'Processor Detected')",
    "Upper Midrange Processor" in reasons,
)
check(
    "Exynos 1380 -> not misclassified as a higher tier",
    "Flagship Performance Processor" not in reasons
    and "High Performance Processor" not in reasons,
)

reasons, _ = reasons_for("Exynos 1480")
check(
    "Exynos 1480 -> also Upper Midrange (same family as 1380)",
    "Upper Midrange Processor" in reasons,
)

reasons, _ = reasons_for("Exynos 1280")
check(
    "Exynos 1280 -> Good Midrange (same tier/points as Snapdragon 6 / Dimensity 7)",
    "Good Midrange Processor" in reasons,
)

reasons, _ = reasons_for("Exynos 1330")
check(
    "Exynos 1330 -> same Good Midrange tier as Exynos 1280",
    "Good Midrange Processor" in reasons,
)

reasons, _ = reasons_for("Exynos 2400")
check(
    "Exynos 2400 -> Flagship Performance (same tier as Dimensity 9)",
    "Flagship Performance Processor" in reasons,
)

reasons, _ = reasons_for("Exynos 2200")
check(
    "Exynos 2200 -> same Flagship Performance tier as 2400/2500",
    "Flagship Performance Processor" in reasons,
)

reasons, _ = reasons_for("Exynos 2100")
check(
    "Exynos 2100 (older flagship) -> High Performance, one tier below 2400/2500",
    "High Performance Processor" in reasons,
)

reasons, _ = reasons_for("Exynos 990")
check(
    "Unlisted/older Exynos model -> still recognized as a named Exynos chip "
    "(Entry-Level tier), not the generic 'Processor Detected' fallback",
    "Entry-Level Processor" in reasons
    and "Processor Detected" not in reasons,
)

# --------------------------------------------------------------
# Regression: an unrecognized chip family still falls into the
# original generic fallback tier unchanged. (Unisoc is used
# elsewhere in this file as a newly-*recognized* family -- this
# guard uses a genuinely unlisted brand instead.)
# --------------------------------------------------------------

reasons, _ = reasons_for("Rockchip RK3588")
check(
    "Unrelated/unrecognized chip family still falls back to 'Processor Detected'",
    "Processor Detected" in reasons,
)

# --------------------------------------------------------------
# Regression: existing Snapdragon / Dimensity tiers unchanged.
# --------------------------------------------------------------

reasons, _ = reasons_for("Snapdragon 8 Elite")
check(
    "Existing Snapdragon 8 Elite tier unchanged -> Flagship Processor",
    "Flagship Processor" in reasons,
)

reasons, _ = reasons_for("MediaTek Dimensity 7300")
check(
    "Existing Dimensity 7-series tier unchanged -> Good Midrange Processor",
    "Good Midrange Processor" in reasons,
)

reasons, _ = reasons_for("Apple A17 Pro")
check(
    "existing 'apple a17 pro'-prefixed form still works unchanged",
    "Flagship Processor" in reasons,
)


# --------------------------------------------------------------
# New: bare Apple A-series chip recognition (iPhone 16 fix).
# Amazon lists the chip as just "A18"/"A18 Pro" with no "Apple"
# brand prefix, unlike Snapdragon/Dimensity/Exynos values which
# always include their brand name.
# --------------------------------------------------------------

reasons, score = reasons_for("A18")
check(
    'bare "A18" (no "Apple" prefix) -> recognized as Flagship Processor',
    "Flagship Processor" in reasons,
)
check(
    'bare "A18" awards the full flagship 25 processor points',
    score >= 25,
)

reasons, _ = reasons_for("A18 Pro")
check(
    'bare "A18 Pro" -> recognized as Flagship Processor',
    "Flagship Processor" in reasons,
)

reasons, _ = reasons_for("A17 Pro")
check(
    'bare "A17 Pro" -> recognized as Flagship Processor',
    "Flagship Processor" in reasons,
)

reasons, _ = reasons_for("A16")
check(
    'bare "A16" -> recognized as Flagship Processor',
    "Flagship Processor" in reasons,
)

reasons, _ = reasons_for("A15")
check(
    'bare "A15" -> recognized as Flagship Processor',
    "Flagship Processor" in reasons,
)

# --------------------------------------------------------------
# Regression guard: bounded matching must not fire on unrelated
# values that merely contain a similar-looking substring.
# --------------------------------------------------------------

reasons, _ = reasons_for("va18000")
check(
    'unrelated token "va18000" (chip-like substring glued to other '
    "characters) must NOT be classified as an Apple processor",
    "Flagship Processor" not in reasons,
)

reasons, _ = reasons_for("A Series A10")
check(
    "the real Amazon data-error value 'A Series A10' (older/unlisted "
    "chip, outside the A15-A19 range) must NOT be classified as Apple flagship",
    "Flagship Processor" not in reasons,
)

reasons, _ = reasons_for("model-a180-x processor")
check(
    "chip-like digits glued to unrelated digits (\"a180\", not a "
    "bounded \"a18\") must NOT be classified as an Apple processor",
    "Flagship Processor" not in reasons,
)


# ================================================================
# Newly supported processor families: Unisoc, Kirin, MediaTek
# Helio. Capability-based tiers, not "Apple gets more points" --
# these apply equally to any brand shipping these chips.
# ================================================================

reasons, score = reasons_for("Unisoc Tiger T612")
check(
    "Unisoc -> recognized as a named processor (Entry-Level), not "
    "the fully-generic 'Processor Detected' bucket",
    "Entry-Level Processor" in reasons
    and "Processor Detected" not in reasons,
)
check(
    "Unisoc does NOT receive flagship-level points",
    score < 25,
)

reasons, _ = reasons_for("HiSilicon Kirin 9000")
check(
    "Kirin 9000 (genuine flagship-class SoC) -> Flagship Performance tier",
    "Flagship Performance Processor" in reasons,
)

reasons, _ = reasons_for("Kirin 820")
check(
    "Kirin 8-series -> High Performance tier",
    "High Performance Processor" in reasons,
)

reasons, _ = reasons_for("Kirin 710")
check(
    "Kirin 7-series -> Good Midrange tier",
    "Good Midrange Processor" in reasons,
)

reasons, score = reasons_for("Kirin 620")
check(
    "unlisted/older Kirin model -> still recognized (Entry-Level), "
    "not the fully-generic bucket",
    "Entry-Level Processor" in reasons
    and "Processor Detected" not in reasons,
)
check(
    "unlisted Kirin model does NOT receive flagship-level points",
    score < 25,
)

reasons, _ = reasons_for("MediaTek Helio G99")
check(
    "Helio G99 (capable midrange gaming chip) -> Good Midrange tier",
    "Good Midrange Processor" in reasons,
)

reasons, score = reasons_for("MediaTek Helio P35")
check(
    "older/lower Helio model -> Entry-Level, not fully-generic",
    "Entry-Level Processor" in reasons,
)
check(
    "Helio P35 does NOT receive flagship-level points",
    score < 25,
)


# --------------------------------------------------------------
# Regression: a genuinely unrecognized processor family still
# falls back to the generic bucket, never flagship-level points.
# --------------------------------------------------------------

reasons, score = reasons_for("Some Obscure Chip XYZ123")
check(
    "a truly unrecognized processor family still falls back to "
    "'Processor Detected', not any tier",
    "Processor Detected" in reasons,
)
check(
    "a truly unrecognized processor does NOT receive flagship-level points",
    score < 25,
)

print()
print("All processor scoring checks passed.")
