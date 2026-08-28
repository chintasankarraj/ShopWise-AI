from app.agents.recommendation_agent import (
    recommend,
    _resolve_processor as _resolve_processor_raw,
    _normalize_specs,
)


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


def _resolve_processor(specs, title, keywords=None):
    """
    Test-only wrapper: _resolve_processor expects the same
    normalized {name: value} dict recommend() already builds
    internally before calling it, not a raw specification list.
    """

    normalized = _normalize_specs(specs)

    if keywords is None:
        return _resolve_processor_raw(normalized, title)

    return _resolve_processor_raw(normalized, title, keywords=keywords)


# ================================================================
# 1. Valid structured CPU -> structured field wins, unchanged,
#    even when the title contains a DIFFERENT recognizable chip
#    (proves the structured field is never second-guessed once
#    it's genuine).
# ================================================================

specs = [
    {"name": "Processor", "value": "Intel Core i7-1355U"},
]

resolved = _resolve_processor(
    specs,
    "Some Laptop with AMD Ryzen 5 mentioned only in marketing copy",
)

check(
    "genuine structured Processor field is used exactly as-is",
    resolved == "intel core i7-1355u",
)

reasons, score = (
    lambda r: (r["reasons"], r["score"])
)(recommend(specs, "laptop", title="irrelevant AMD Ryzen 5 mention"))

check(
    "genuine structured i7 still scores its real tier (High Performance Processor)",
    "High Performance Processor" in reasons,
)


# ================================================================
# 2. "Unknown" structured CPU -> title fallback.
#    Real MacBook Air M3 case from the V1 audit: Amazon's own
#    "Cpu Model" field literally says "Unknown", the real chip
#    name is only in the title.
# ================================================================

macbook_specs = [
    {"name": "Screen Size", "value": "13.6 Inches"},
    {"name": "Colour", "value": "Midnight"},
    {"name": "Cpu Model", "value": "Unknown"},
    {"name": "Ram", "value": "8 GB"},
    {"name": "Operating System", "value": "Mac OS"},
    {"name": "Graphics Card Description", "value": "Integrated"},
    {"name": "Graphics Coprocessor", "value": "Apple Integrated Graphics"},
    {"name": "Processor Type", "value": "Unknown"},
    {"name": "Processor Brand", "value": "Apple"},
    {"name": "Cpu Model Number", "value": "8-Core CPU, 8-Core GPU, 16-core Neural Engine"},
    {"name": "Item Type", "value": "Laptop"},
]

macbook_title = (
    "Apple 2024 MacBook Air 13″ Laptop with M3 chip: "
    "34.46 cm (13.6″) Liquid Retina Display, 8GB Unified Memory, "
    "256GB SSD Storage, Backlit Keyboard, 1080p FaceTime HD Camera, "
    "Touch ID- Midnight"
)

resolved = _resolve_processor(macbook_specs, macbook_title)

check(
    "'Unknown' structured Cpu Model falls back to the title, resolving to the real M3 chip",
    resolved is not None and "apple" in resolved and "m3" in resolved,
)

macbook_result = recommend(macbook_specs, "laptop", title=macbook_title)

check(
    "MacBook Air M3 now scores an Apple Silicon tier instead of the generic fallback",
    "Processor Detected" not in macbook_result["reasons"]
    and any(
        r in macbook_result["reasons"]
        for r in ("Powerful Processor", "High Performance Processor", "Flagship Processor")
    ),
)


# ================================================================
# 3a. "Others" structured CPU, NO recoverable title evidence ->
#     stays honest, returns None (Not Available), never guesses.
#     Real Samsung Galaxy S26 case from the V1 audit.
# ================================================================

s26_specs = [
    {"name": "Operating System", "value": "Android 16"},
    {"name": "Ram", "value": "12 GB"},
    {"name": "Cpu Model", "value": "Others"},
    {"name": "Processor Series", "value": "Others"},
    {"name": "Storage", "value": "256 GB"},
    {"name": "Item Type", "value": "Smartphone"},
]

s26_title = (
    "Samsung Galaxy S26 5G (Black, 12GB RAM, 256GB Storage), AI Phone, "
    "Photo Assist, Creative Studio, 50MP Camera with ProVisual Engine, "
    "Powerful Customized Processor and 4300mAh Battery"
)

resolved = _resolve_processor(
    s26_specs,
    s26_title,
    keywords=["processor", "cpu", "chipset", "chip"],
)

check(
    "'Others' with no recognizable chip anywhere in the title resolves to None, not a guess",
    resolved is None,
)

s26_result = recommend(s26_specs, "smartphone", title=s26_title)

check(
    "Samsung S26 gets zero processor points/reason rather than the old generic 8pt bucket",
    "Processor Detected" not in s26_result["reasons"]
    and not any("Processor" in r for r in s26_result["reasons"]),
)


# ================================================================
# 3b. "Others" structured CPU, WITH recoverable title evidence ->
#     falls back and resolves correctly (the "only when evidence
#     exists" half of the same rule).
# ================================================================

specs = [
    {"name": "Cpu Model", "value": "Others"},
]

resolved = _resolve_processor(
    specs,
    "Some Phone with Snapdragon 7 Gen 3 and a great camera",
    keywords=["processor", "cpu", "chipset", "chip"],
)

check(
    "'Others' WITH a real chip name in the title falls back and resolves it",
    resolved is not None and "snapdragon 7 gen 3" in resolved,
)


# ================================================================
# 4. Empty structured CPU (no processor-ish field at all) ->
#    title fallback.
# ================================================================

specs = [
    {"name": "Ram", "value": "16 GB"},
]

resolved = _resolve_processor(
    specs,
    "Great Laptop with AMD Ryzen 7 7445HS and a big battery",
)

check(
    "No structured processor field at all falls back to the title",
    resolved is not None and "ryzen 7" in resolved,
)


# ================================================================
# 5. No usable CPU evidence anywhere -> Not Available (None),
#    no crash, no invented tier.
# ================================================================

specs = [
    {"name": "Ram", "value": "16 GB"},
]

resolved = _resolve_processor(specs, "A perfectly nice laptop with a great screen")

check(
    "No processor evidence in either source resolves to None",
    resolved is None,
)

result = recommend(specs, "laptop", title="A perfectly nice laptop with a great screen")

check(
    "No processor evidence anywhere -> no crash, no processor reason, no points invented",
    not any("Processor" in r for r in result["reasons"]),
)


# ================================================================
# 6. No brand-specific hardcoding -- a placeholder value paired
#    with a brand name that is NOT Apple/Snapdragon/etc. and no
#    recognizable chip pattern in the title must still resolve to
#    None, proving the fallback is driven by actual regex
#    evidence, never "if brand looks like X, assume chip Y".
# ================================================================

specs = [
    {"name": "Cpu Model", "value": "Unknown"},
]

resolved = _resolve_processor(
    specs,
    "Dell Laptop with a great processor and long battery life",
)

check(
    "Unrecognized brand + placeholder + no chip pattern in title -> None, not a brand-based guess",
    resolved is None,
)

# Same check the other direction: a real, unusual/untiered chip
# name in a structured field is never treated as a placeholder or
# second-guessed via title, regardless of brand.
specs = [
    {"name": "Processor", "value": "MediaTek Some Future Chip 9999"},
]

resolved = _resolve_processor(specs, "Random Phone Title Mentioning Nothing Useful")

check(
    "A genuine but unrecognized/untiered processor name is kept exactly as-is (not a placeholder)",
    resolved == "mediatek some future chip 9999",
)


print("\nAll processor title-fallback checks passed.")
