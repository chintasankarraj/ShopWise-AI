from app.agents.recommendation_agent import recommend


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


def result_for(specs, title=None):
    return recommend(specs, "smartphone", title=title)


# ================================================================
# A. CHARGING FALLBACK
# ================================================================

# A1. Prose-only, Apple-shaped case: no dedicated Charging field,
# but a real wattage stated inside "Power And Battery" prose.
apple_shaped_specs = [
    {
        "name": "Power And Battery",
        "value": (
            "Video playback: Up to 22 hours. Fast-charge capable: "
            "Up to 50% charge in around 30 minutes with 20W adapter "
            "or higher paired with USB-C charging cable, or 30W "
            "adapter or higher paired with MagSafe Charger."
        ),
    },
]

result = result_for(apple_shaped_specs)
check(
    'prose-only "...20W adapter...30W adapter..." -> charging fallback fires',
    "Good Charging Speed" in result["reasons"],
)
check(
    "fallback picks the highest stated wattage (30W, not 20W)",
    result["score"] >= 6,
)

# A2. No wattage anywhere -> no charging points, nothing invented.
no_wattage_specs = [
    {"name": "Battery", "value": "Up to 22 hours video playback"},
]

result = result_for(no_wattage_specs)
CHARGING_REASONS = {
    "Very Fast Charging",
    "Fast Charging",
    "Good Charging Speed",
    "Moderate Charging Speed",
    "Slow Charging",
    "Ultra-Fast Charging",
    "Standard Charging",
    "Basic Charging",
}
check(
    "no wattage stated anywhere -> no charging points awarded",
    not (CHARGING_REASONS & set(result["reasons"])),
)

# A3. Dedicated Charging field takes priority over the fallback,
# even when the fallback text would otherwise suggest a
# different tier.
dedicated_field_specs = [
    {"name": "Charging", "value": "67W"},
    {
        "name": "Power And Battery",
        "value": "Fast-charge capable with 20W adapter or higher.",
    },
]

result = result_for(dedicated_field_specs)
check(
    "dedicated Charging field (67W -> Very Fast Charging) wins over "
    "the fallback text (20W -> would be Standard Charging)",
    "Very Fast Charging" in result["reasons"]
    and "Standard Charging" not in result["reasons"],
)


# ================================================================
# B. CONNECTIVITY FALLBACK
# ================================================================

# B1. Title states 5G, no dedicated Cellular/Network field.
result = result_for(
    [{"name": "Storage", "value": "128 GB"}],
    title="Apple iPhone 16 5G Mobile Phone with Camera Control",
)
check(
    'title "...iPhone 16 5G..." with no Connectivity field -> '
    "5G Connectivity scored",
    "5G Connectivity" in result["reasons"],
)

# B2. Title has no 5G/4G mention -> no connectivity points.
result = result_for(
    [{"name": "Storage", "value": "128 GB"}],
    title="Apple iPhone 16 Mobile Phone with Camera Control",
)
CONNECTIVITY_REASONS = {"5G Connectivity", "4G Connectivity"}
check(
    "title without 5G/4G -> no connectivity points invented",
    not (CONNECTIVITY_REASONS & set(result["reasons"])),
)

# B3. A dedicated Cellular field still takes priority over the
# title, even when they'd disagree.
result = result_for(
    [{"name": "Cellular", "value": "4G"}],
    title="Some Phone 5G Edition",
)
check(
    "dedicated Cellular field (4G) wins over the title (5G)",
    "4G Connectivity" in result["reasons"]
    and "5G Connectivity" not in result["reasons"],
)

# B4. Brand-neutral: works identically for Samsung/Xiaomi/OnePlus
# titles, not just Apple.
for brand_title in [
    "Samsung Galaxy S25 Ultra 5G AI Smartphone",
    "Xiaomi Redmi Note 14 5G",
    "OnePlus 13R 5G",
]:
    result = result_for([{"name": "Storage", "value": "256 GB"}], title=brand_title)
    check(
        f'brand-neutral: "{brand_title}" -> 5G Connectivity scored',
        "5G Connectivity" in result["reasons"],
    )

# B5. False-positive guard: "4GB RAM"/"128GB" in a title must
# NEVER be misread as 4G/5G cellular capability.
result = result_for(
    [{"name": "Storage", "value": "64 GB"}],
    title="Samsung Galaxy A06 (64GB Storage, 4GB RAM)",
)
check(
    '"4GB RAM"/"64GB" storage mentions are NOT misread as 4G cellular',
    not (CONNECTIVITY_REASONS & set(result["reasons"])),
)

result = result_for(
    [{"name": "Storage", "value": "128 GB"}],
    title="Some Phone with 5GB RAM Variant",
)
check(
    'a hypothetical "5GB RAM" mention is NOT misread as 5G cellular',
    not (CONNECTIVITY_REASONS & set(result["reasons"])),
)

print()
print("All charging/connectivity fallback checks passed.")
