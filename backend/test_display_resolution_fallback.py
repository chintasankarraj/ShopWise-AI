from app.agents.recommendation_agent import recommend


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


def result_for(specs):
    return recommend(specs, "smartphone")


RESOLUTION_REASONS = {
    "High Resolution Display",
    "Full HD+ Display",
}


# --------------------------------------------------------------
# Dedicated Resolution field takes priority and is unchanged.
# --------------------------------------------------------------

result = result_for(
    [
        {"name": "Display", "value": "AMOLED"},
        {"name": "Resolution", "value": "3120 x 1440"},
    ]
)
check(
    "dedicated Resolution field (3120x1440) still scores High Resolution Display",
    "High Resolution Display" in result["reasons"],
)

result_dedicated = result_for(
    [
        {"name": "Display", "value": "some unrelated prose with 9999x9999 in it"},
        {"name": "Resolution", "value": "1080 x 2400"},
    ]
)
check(
    "dedicated Resolution field wins over a conflicting number in the "
    "Display value -- fallback never overrides it",
    "Full HD+ Display" in result_dedicated["reasons"],
)


# --------------------------------------------------------------
# Prose-only Display field (the actual iPhone 16 case).
# --------------------------------------------------------------

result = result_for(
    [
        {
            "name": "Display",
            "value": (
                "Super Retina XDR display, 6.1 inch OLED display, "
                "2556x1179-pixel resolution at 460 ppi"
            ),
        },
    ]
)
check(
    'prose-only Display "...2556x1179-pixel resolution..." -> '
    "resolution fallback extracts it correctly (High Resolution Display)",
    "High Resolution Display" in result["reasons"],
)
check(
    "OLED panel quality is also still scored alongside the fallback",
    "OLED Display" in result["reasons"],
)


# --------------------------------------------------------------
# Display with no WxH resolution -> no fallback value invented.
# --------------------------------------------------------------

result = result_for(
    [{"name": "Display", "value": "6.1 in"}],
)
check(
    "sparse Display with no WxH pattern -> no resolution points invented",
    not (RESOLUTION_REASONS & set(result["reasons"])),
)

result = result_for(
    [
        {
            "name": "Display",
            "value": "OLED display, 460 ppi, 15.54 cm diagonal",
        },
    ],
)
check(
    "Display prose with unrelated numbers but no NxN shape -> "
    "no resolution points invented",
    not (RESOLUTION_REASONS & set(result["reasons"])),
)


# --------------------------------------------------------------
# Display containing unrelated numbers PLUS a valid WxH pair ->
# the correct WxH pair is identified, not an unrelated number.
# --------------------------------------------------------------

result = result_for(
    [
        {
            "name": "Display",
            "value": (
                "OLED display, 460 ppi, 15.54 cm diagonal, "
                "2556x1179-pixel resolution"
            ),
        },
    ],
)
check(
    "unrelated numbers (460 ppi, 15.54 cm) surrounding a real WxH pair "
    "don't confuse the fallback -- correct 2556x1179 pair is used",
    "High Resolution Display" in result["reasons"],
)


# --------------------------------------------------------------
# Brand-neutral: a non-Apple prose-style Display value works
# identically -- this is not Apple/iPhone-specific logic.
# --------------------------------------------------------------

result = result_for(
    [
        {
            "name": "Display",
            "value": (
                "Google Pixel-style AMOLED panel, 1080x2400 pixels, "
                "smooth and vivid"
            ),
        },
    ],
)
check(
    "non-Apple prose-style Display value (1080x2400) -> fallback works "
    "identically, proving this is brand-neutral logic",
    "Full HD+ Display" in result["reasons"]
    and "AMOLED Display" in result["reasons"],
)

print()
print("All display resolution fallback checks passed.")
