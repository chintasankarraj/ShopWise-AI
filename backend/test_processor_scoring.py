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
# Regression: an unrecognized non-Exynos chip still falls into
# the original generic fallback tier unchanged.
# --------------------------------------------------------------

reasons, _ = reasons_for("UNISOC Tiger T612")
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

print()
print("All processor scoring checks passed.")
