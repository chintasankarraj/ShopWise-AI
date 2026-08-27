from app.agents.recommendation_agent import recommend


def score_battery(battery_value):
    """
    Score a minimal smartphone spec set containing only a
    Battery field, so battery-tier behavior can be checked in
    isolation from the other scoring dimensions.
    """

    specs = [
        {"name": "Battery", "value": battery_value},
    ]

    result = recommend(specs, "smartphone")

    return result["reasons"], result["score"]


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


BATTERY_TIER_REASONS = {
    "Excellent Battery",
    "Very Large Battery",
    "Good Battery",
    "Decent Battery",
    "Average Battery",
    "Small Battery",
}


# --------------------------------------------------------------
# Genuine capacity figures still score correctly.
# --------------------------------------------------------------

reasons, score = score_battery("5000 mAh")
check(
    '"5000 mAh" -> scored as capacity (Excellent Battery, >=7000 tier '
    "not hit but >=5000 -> Good Battery)",
    "Good Battery" in reasons,
)
check(
    '"5000 mAh" awards real capacity points (>0)',
    score > 0,
)

reasons, _ = score_battery("4000 milliamp hours")
check(
    '"4000 milliamp hours" (spelled-out unit) -> scored as capacity',
    "Average Battery" in reasons,
)

reasons, _ = score_battery("7500mAh")
check(
    '"7500mAh" (no space before unit) -> still recognized as capacity',
    "Excellent Battery" in reasons,
)

reasons, _ = score_battery("6200 Milliamp Hour")
check(
    'singular "Milliamp Hour" form -> still recognized as capacity',
    "Very Large Battery" in reasons,
)


# --------------------------------------------------------------
# The actual iPhone 16 case: a runtime duration must NEVER be
# treated as a capacity figure, even though it has the same
# "number + unit word" shape.
# --------------------------------------------------------------

reasons, score = score_battery("Up to 22 hours video playback")
check(
    '"Up to 22 hours video playback" -> NOT scored as 22 mAh capacity',
    not (BATTERY_TIER_REASONS & set(reasons)),
)
check(
    "no capacity was invented from the runtime figure -> 0 battery points",
    score == 0,
)

reasons, score = score_battery("Up to 20 hours talk time")
check(
    '"Up to 20 hours talk time" -> not treated as capacity either',
    not (BATTERY_TIER_REASONS & set(reasons)),
)

reasons, score = score_battery("Up to 80 hours audio playback")
check(
    '"Up to 80 hours audio playback" -> unrelated large number, still not capacity',
    not (BATTERY_TIER_REASONS & set(reasons))
    and score == 0,
)


# --------------------------------------------------------------
# Unrelated numbers embedded in longer battery prose must not
# be misread as capacity either.
# --------------------------------------------------------------

reasons, score = score_battery(
    "Built-in rechargeable lithium-ion battery, "
    "fast-charge up to 50% in around 30 minutes"
)
check(
    "battery prose with unrelated numbers (50%, 30 minutes) and no "
    "capacity unit -> not treated as capacity",
    not (BATTERY_TIER_REASONS & set(reasons))
    and score == 0,
)

print()
print("All battery scoring checks passed.")
