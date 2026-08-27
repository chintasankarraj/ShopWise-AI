"""
Regression tests for QA Audit Round 2: Apple Silicon / Snapdragon X
processor tiers, a laptop GPU scoring dimension, laptop refresh-rate
and resolution scoring, and the laptop battery field-selection fix.

All tiers are evidence-based (derived from real product-line
capability hierarchies, not reverse-engineered to hit a specific
tested product's score) and generalized (no brand/product-specific
hacks -- see recommendation_agent.py's docstrings for the reasoning
behind each tier).
"""

from app.agents.recommendation_agent import (
    recommend,
    _apple_silicon_tier,
    _snapdragon_x_tier,
    _laptop_panel_tech,
    _score_laptop_gpu,
    _extract_laptop_battery_wh,
    _looks_like_watt_hour_capacity,
    _normalize_specs,
)


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


def laptop_result(specs, title=None):
    return recommend(specs, "laptop", title=title)


# ================================================================
# Apple M-series processor tiers
# ================================================================

check(
    "bare 'apple m3' -> Powerful Processor tier (base chip, i5-equivalent bucket)",
    _apple_silicon_tier("apple m3") == (23, "Powerful Processor"),
)
check(
    "'apple m1' -> same base tier as m3 (tier is by variant, not generation)",
    _apple_silicon_tier("apple m1") == (23, "Powerful Processor"),
)
check(
    "'apple m3 pro' -> High Performance Processor tier (i7-equivalent bucket)",
    _apple_silicon_tier("apple m3 pro") == (27, "High Performance Processor"),
)
check(
    "'apple m2 max' -> Flagship Processor tier",
    _apple_silicon_tier("apple m2 max") == (30, "Flagship Processor"),
)
check(
    "'apple m1 ultra' -> Flagship Processor tier (same bucket as Max)",
    _apple_silicon_tier("apple m1 ultra") == (30, "Flagship Processor"),
)
check(
    "'apple m4' (newest generation, base variant) -> still base tier, not auto-flagship",
    _apple_silicon_tier("apple m4") == (23, "Powerful Processor"),
)
check(
    "no 'apple' co-occurrence -> None (closes the Intel 'Core m3' collision)",
    _apple_silicon_tier("intel core m3-7y30") is None,
)
check(
    "unrelated string -> None",
    _apple_silicon_tier("intel core ultra 5") is None,
)

# End-to-end: MacBook Air M3 (the real audited product) gets the
# base tier, not a value picked to hit a target score.
macbook_specs = _normalize_specs([
    {"name": "Cpu Model", "value": "Apple M3"},
    {"name": "Processor Type", "value": "Apple M3"},
    {"name": "Ram", "value": "24 GB"},
])
result = laptop_result([
    {"name": "Cpu Model", "value": "Apple M3"},
    {"name": "Processor Type", "value": "Apple M3"},
    {"name": "Ram", "value": "24 GB"},
])
check(
    "MacBook Air M3 end-to-end -> Powerful Processor (base M3, not Pro/Max/Ultra)",
    "Powerful Processor" in result["reasons"],
)


# ================================================================
# Snapdragon X tiers
# ================================================================

check(
    "'snapdragon x elite' -> High Performance Processor tier",
    _snapdragon_x_tier("snapdragon x elite") == (27, "High Performance Processor"),
)
check(
    "'snapdragon x plus' -> Powerful Processor tier (cut-down variant)",
    _snapdragon_x_tier("snapdragon x plus") == (23, "Powerful Processor"),
)
check(
    "bare 'snapdragon x' (unspecified variant) -> None, falls to generic fallback",
    _snapdragon_x_tier("snapdragon x") is None,
)
check(
    "'snapdragon 8 elite' (a PHONE chip) is NOT matched as Snapdragon X",
    _snapdragon_x_tier("qualcomm snapdragon 8 elite for galaxy") is None,
)

result = laptop_result([
    {"name": "Cpu Model", "value": "Snapdragon X Elite"},
    {"name": "Processor Type", "value": "Snapdragon X Elite"},
    {"name": "Ram", "value": "16 GB"},
])
check(
    "Vivobook Snapdragon X Elite end-to-end -> High Performance Processor",
    "High Performance Processor" in result["reasons"],
)


# ================================================================
# Intel/AMD regression -- unchanged behavior, unaffected by the
# new Apple/Snapdragon branches.
# ================================================================

for cpu_value, expected_reason in [
    ("intel core i9-13900h", "Flagship Processor"),
    ("amd ryzen 9 7940hs", "Flagship Processor"),
    ("intel core ultra 7 155h", "High Performance Processor"),
    ("amd ryzen 7 7445hs", "High Performance Processor"),
    ("12th gen intel core i5", "Powerful Processor"),
    ("amd ryzen 5 7520u", "Powerful Processor"),
    ("13th gen intel core i3-1305u", "Processor Detected"),
]:
    result = laptop_result([{"name": "Processor", "value": cpu_value}])
    check(
        f"regression: {cpu_value!r} still tiers as {expected_reason!r}",
        expected_reason in result["reasons"],
    )


# ================================================================
# Dedicated GPU tiers
# ================================================================

def gpu_for(description, co_processor=None, vram=None, title=None):
    specs = [{"name": "Graphics Card Description", "value": description}]
    if co_processor is not None:
        specs.append({"name": "Graphics Co Processor", "value": co_processor})
    if vram is not None:
        specs.append({"name": "Graphics Ram Size", "value": vram})
    return _score_laptop_gpu(_normalize_specs(specs), title=title)

check(
    "RTX 4090 (suffix 90) -> Flagship Dedicated GPU",
    gpu_for("Dedicated", "NVIDIA GeForce RTX 4090") == (12, "Flagship Dedicated GPU"),
)
check(
    "RTX 4070 (suffix 70) -> High-End Dedicated GPU",
    gpu_for("Dedicated", "NVIDIA GeForce RTX 4070") == (10, "High-End Dedicated GPU"),
)
check(
    "RTX 4060 (suffix 60) -> Capable Dedicated GPU",
    gpu_for("Dedicated", "NVIDIA GeForce RTX 4060") == (8, "Capable Dedicated GPU"),
)
check(
    "RTX 4050 (suffix 50) -> Entry Dedicated GPU (real audited Acer Nitro V case)",
    gpu_for("Dedicated", "NVIDIA GeForce RTX 4050") == (6, "Entry Dedicated GPU"),
)
check(
    "AMD Radeon RX 7900 (AMD's round-hundred naming) -> Flagship Dedicated GPU",
    gpu_for("Dedicated", "AMD Radeon RX 7900") == (12, "Flagship Dedicated GPU"),
)
check(
    "AMD Radeon RX 7800 -> High-End Dedicated GPU, distinct from the 7900 flagship",
    gpu_for("Dedicated", "AMD Radeon RX 7800") == (10, "High-End Dedicated GPU"),
)
check(
    "AMD Radeon RX 6600 -> Capable Dedicated GPU",
    gpu_for("Dedicated", "AMD Radeon RX 6600") == (8, "Capable Dedicated GPU"),
)
check(
    "AMD Radeon RX 6400 (entry) -> Entry Dedicated GPU",
    gpu_for("Dedicated", "AMD Radeon RX 6400") == (6, "Entry Dedicated GPU"),
)
check(
    "unrecognized dedicated GPU text, no VRAM field -> minimal 'Dedicated GPU Detected'",
    gpu_for("Dedicated", "Some Unknown Chip") == (4, "Dedicated GPU Detected"),
)
check(
    "dedicated confirmed but unreliable co-processor text -> falls back to VRAM size "
    "(real audited HP Victus case: 'AMD Radeon R7' text does not name the real RTX 3050)",
    gpu_for("Dedicated", "AMD Radeon R7", vram="6 GB") == (6, "Entry Dedicated GPU"),
)
check(
    "Round 2B calibration fix: HP Victus's real RTX 3050 (VRAM-fallback path) now "
    "ties with Acer Nitro V's real RTX 4050 (model-number path) instead of outscoring "
    "it -- both are genuinely entry-tier laptop dedicated GPUs",
    gpu_for("Dedicated", "AMD Radeon R7", vram="6 GB")
    == gpu_for("Dedicated", "NVIDIA GeForce RTX 4050", vram="6 GB"),
)
check(
    "VRAM-fallback tier never outranks the same real capability class scored via a "
    "reliable model number: an 8GB VRAM-only reading does not outscore a known RTX 4060",
    gpu_for("Dedicated", "Unknown Chip", vram="8 GB")
    == gpu_for("Dedicated", "NVIDIA GeForce RTX 4060", vram="8 GB"),
)
check(
    "dedicated confirmed, no usable text or VRAM at all -> still only the minimal tier",
    gpu_for("Dedicated") == (4, "Dedicated GPU Detected"),
)


# ================================================================
# Integrated GPU behavior -- never rewarded merely for existing.
# ================================================================

check(
    "plain Intel UHD integrated graphics -> no bonus",
    gpu_for("Integrated", "Intel UHD Graphics") == (0, None),
)
check(
    "plain 'Integrated' with no GPU text at all -> no bonus",
    gpu_for("Integrated") == (0, None),
)
check(
    "Intel Iris Xe (recognized capable integrated) -> small bonus",
    gpu_for("Integrated", "Intel Iris Xe Graphics") == (3, "Capable Integrated Graphics"),
)
check(
    "Intel Arc integrated graphics, present in a structured field -> small bonus",
    gpu_for("Integrated", "Intel Arc Graphics") == (3, "Capable Integrated Graphics"),
)
check(
    "Intel Arc mentioned ONLY in the title, no structured GPU field "
    "(real audited HP 14 AI case) -> title fallback still credits it",
    gpu_for("Integrated", title="HP 14 AI ... Intel Arc Graphics ... Laptop")
    == (3, "Capable Integrated Graphics"),
)
check(
    "older/basic integrated AMD Radeon (610M) -> no bonus",
    gpu_for("Integrated", "Integrated AMD Radeon 610M Graphics") == (0, None),
)
check(
    "newer high-end integrated AMD Radeon (780M) -> small bonus, symmetric with Iris Xe",
    gpu_for("Integrated", "Integrated AMD Radeon 780M Graphics") == (3, "Capable Integrated Graphics"),
)
check(
    "Qualcomm Adreno (no differentiating capability evidence) -> no bonus, not punished either",
    gpu_for("Integrated", "Qualcomm Adreno GPU") == (0, None),
)
apple_gpu_specs = _normalize_specs([
    {"name": "Graphics Card Description", "value": "Integrated"},
    {"name": "Video Processor", "value": "Apple"},
    {"name": "Cpu Model Number", "value": "Apple M3 chip with 8-core CPU and 10-core GPU"},
])
check(
    "Apple '10-core GPU' (real audited MacBook Air M3 case) -> capable-tier bonus, "
    "evidence-based via the stated core count, not a Apple-brand special case",
    _score_laptop_gpu(apple_gpu_specs) == (3, "Capable Integrated Graphics"),
)

apple_high_core_specs = _normalize_specs([
    {"name": "Graphics Card Description", "value": "Integrated"},
    {"name": "Cpu Model Number", "value": "Apple M3 Max chip with 16-core CPU and 40-core GPU"},
])
check(
    "a much higher stated core count (40-core GPU) crosses into the higher integrated bonus tier",
    _score_laptop_gpu(apple_high_core_specs) == (6, "High Core-Count Integrated GPU"),
)

generic_high_core_specs = _normalize_specs([
    {"name": "Graphics Card Description", "value": "Integrated"},
    {"name": "Graphics Co Processor", "value": "Some Vendor Chip with 20-core GPU"},
])
check(
    "the core-count rule is brand-neutral -- a non-Apple listing stating the same "
    "evidence gets the same bonus",
    _score_laptop_gpu(generic_high_core_specs) == (6, "High Core-Count Integrated GPU"),
)


# ================================================================
# Dedicated refresh-rate field priority + prose fallback
# ================================================================

result = laptop_result([{"name": "Refresh Rate", "value": "144 Hz"}])
check(
    "dedicated Refresh Rate field: 144Hz -> Very High Refresh Rate",
    "Very High Refresh Rate" in result["reasons"],
)

result = laptop_result([{"name": "Refresh Rate", "value": "165 Hz"}])
check(
    "dedicated Refresh Rate field: 165Hz (real audited Acer Nitro V case) -> Very High Refresh Rate",
    "Very High Refresh Rate" in result["reasons"],
)

result = laptop_result([{"name": "Refresh Rate", "value": "90 Hz"}])
check(
    "dedicated Refresh Rate field: 90Hz -> 90Hz Display",
    "90Hz Display" in result["reasons"],
)

result = laptop_result([{"name": "Display", "value": "144Hz IPS panel with fast response time"}])
check(
    "no dedicated Refresh Rate field, but 144Hz stated in the Display field's prose "
    "-> fallback picks it up",
    "Very High Refresh Rate" in result["reasons"],
)

result = laptop_result([
    {"name": "Refresh Rate", "value": "120 Hz"},
    {"name": "Display", "value": "60Hz OLED panel"},
])
check(
    "dedicated Refresh Rate field takes priority over conflicting Display-prose text",
    "120Hz Display" in result["reasons"] and "Very High Refresh Rate" not in result["reasons"],
)

result = laptop_result([{"name": "Display", "value": "FHD IPS panel, no refresh rate stated"}])
check(
    "no refresh rate anywhere -> no refresh-tier reason invented",
    not any("Refresh Rate" in r or "Hz Display" in r for r in result["reasons"]),
)

result = laptop_result([{"name": "Display", "value": "OLED display, 300 nits brightness"}])
check(
    "an unrelated number in Display prose (300 nits) is never misread as a refresh rate "
    "(the fallback pattern requires the literal 'Hz' unit)",
    not any("Refresh Rate" in r or "Hz Display" in r for r in result["reasons"]),
)


# ================================================================
# Dedicated resolution priority + fallback
# ================================================================

result = laptop_result([{"name": "Maximum Display Resolution", "value": "3840 x 2160 Pixels"}])
check(
    "dedicated resolution field: 3840x2160 (4K) -> High Resolution Display",
    "High Resolution Display" in result["reasons"],
)

result = laptop_result([{"name": "Native Resolution", "value": "1920 x 1080 pixels"}])
check(
    "dedicated resolution field: 1920x1080 -> Full HD+ Display",
    "Full HD+ Display" in result["reasons"],
)

result = laptop_result([{"name": "Display", "value": "Super sharp 2560x1664-pixel display"}])
check(
    "no dedicated resolution field, WxH pattern embedded in Display prose -> fallback picks it up",
    "High Resolution Display" in result["reasons"],
)

result = laptop_result([
    {"name": "Native Resolution", "value": "1920 x 1080 pixels"},
    {"name": "Display", "value": "3840x2160-pixel marketing description"},
])
check(
    "dedicated resolution field takes priority over conflicting Display-prose numbers",
    "Full HD+ Display" in result["reasons"] and "High Resolution Display" not in result["reasons"],
)


# ================================================================
# Battery units
# ================================================================

check(
    "'52.6 Watt Hours' recognized as a valid capacity",
    _looks_like_watt_hour_capacity("52.6 watt hours") is True,
)
check(
    "'52.6Wh' (abbreviated) recognized as a valid capacity",
    _looks_like_watt_hour_capacity("52.6wh") is True,
)
check(
    "'18 Hours' (a duration, not a capacity) is NOT recognized",
    _looks_like_watt_hour_capacity("18 hours") is False,
)
check(
    "'Lithium Ion' (non-numeric descriptor) is NOT recognized",
    _looks_like_watt_hour_capacity("lithium ion") is False,
)

battery_collision_specs = _normalize_specs([
    {"name": "Battery Cell Type", "value": "Lithium Ion"},
    {"name": "Battery Life", "value": "18 Hours"},
    {"name": "Lithium Battery Energy Content", "value": "75 Watt Hours"},
])
check(
    "real audited field-collision shape (Battery Cell Type resolves first under a plain "
    "lookup) -- the fix correctly finds the real 75Wh capacity instead",
    _extract_laptop_battery_wh(battery_collision_specs) == 75.0,
)

conflicting_wh_specs = _normalize_specs([
    {"name": "Battery Cell Type", "value": "Lithium Ion"},
    {"name": "Battery Life", "value": "42 Watt Hours"},
    {"name": "Lithium Battery Energy Content", "value": "70 Watt Hours"},
])
check(
    "when two fields both state watt-hours (real audited Vivobook case: Battery Life "
    "says 42Wh, Lithium Battery Energy Content says 70Wh), the unambiguously-named "
    "'energy content' field wins",
    _extract_laptop_battery_wh(conflicting_wh_specs) == 70.0,
)

result = laptop_result([
    {"name": "Battery Cell Type", "value": "Lithium Ion"},
    {"name": "Lithium Battery Energy Content", "value": "75 Watt Hours"},
])
check(
    "end-to-end: 75Wh -> Large Battery",
    "Large Battery" in result["reasons"],
)

result = laptop_result([
    {"name": "Battery Cell Type", "value": "Lithium Ion"},
    {"name": "Lithium Battery Energy Content", "value": "52.5 Watt Hours"},
])
check(
    "end-to-end: 52.5Wh -> Good Battery",
    "Good Battery" in result["reasons"],
)

result = laptop_result([
    {"name": "Battery Cell Type", "value": "Lithium Ion"},
    {"name": "Lithium Battery Energy Content", "value": "36 Watt Hours"},
])
check(
    "end-to-end: 36Wh -> low tier, but still an honest reason string (not silently 0 with no label)",
    "Battery Detected" in result["reasons"],
)


# ================================================================
# Missing-data behavior -- never invent, never crash.
# ================================================================

result = laptop_result([{"name": "Ram", "value": "16 GB"}])
check(
    "no processor field at all -> no processor reason, no crash",
    not any("Processor" in r for r in result["reasons"]),
)
check(
    "no GPU field at all -> no GPU reason",
    not any("GPU" in r for r in result["reasons"]),
)
check(
    "no display field at all -> no display/resolution/refresh reason",
    not any(
        term in r
        for r in result["reasons"]
        for term in ["Display", "Resolution", "Refresh", "Hz"]
    ),
)
check(
    "no battery field at all -> no battery reason",
    not any("Battery" in r for r in result["reasons"]),
)

empty_result = laptop_result([])
check(
    "completely empty spec list -> score 0, empty reasons, no crash",
    empty_result["score"] == 0 and empty_result["reasons"] == [],
)

print()
print("All Round 2 laptop scoring checks passed.")
