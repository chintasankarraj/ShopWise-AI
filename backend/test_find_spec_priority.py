"""
Regression tests for the _find_spec() processor/CPU field-priority
fix (QA Audit Round 1, Issue 2). Real laptop listings on Amazon.in
often carry a "Video Processor" field describing the GPU vendor,
which happens to also contain the word "processor". Before this
fix, _find_spec(specs, ["processor", "cpu", "chip"]) could return
that GPU field instead of the real "Processor Type"/"Cpu Model"
field whenever the listing had no standalone "Processor" field to
win on an exact-name match -- confirmed live on the ASUS Zenbook
14 (Ultra 5), MacBook Air M3, and ASUS Vivobook S15 (Snapdragon X
Elite) during the real-world QA audit.

find_cpu() below mirrors the exact call the production code now
makes (both _score_smartphone and _score_laptop pass the same
exclude=["video processor", "graphics"] list), so these tests
exercise the real production contract, not just _find_spec() in
isolation.
"""

from app.agents.recommendation_agent import _find_spec, _normalize_specs, recommend

CPU_EXCLUDE = ["video processor", "graphics"]


def find_cpu(specs):
    return _find_spec(specs, ["processor", "cpu", "chip"], exclude=CPU_EXCLUDE)


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


def laptop_reasons(specs):
    result = recommend(specs, "laptop")
    return result["reasons"], result["score"]


# --------------------------------------------------------------
# The exact field-collision shape from each of the three audited
# laptops.
# --------------------------------------------------------------

zenbook_specs = _normalize_specs([
    {"name": "Cpu Model", "value": "Intel Core Ultra 5"},
    {"name": "Graphics Co Processor", "value": "Intel Graphics"},
    {"name": "Video Processor", "value": "Intel"},
    {"name": "Processor Type", "value": "Intel Core Ultra 5"},
    {"name": "Processor Speed", "value": "1.7 GHz"},
    {"name": "Processor Brand", "value": "Intel"},
])

check(
    "Zenbook: Processor Type beats Video Processor",
    find_cpu(zenbook_specs) == "intel core ultra 5",
)

macbook_specs = _normalize_specs([
    {"name": "Cpu Model", "value": "Apple M3"},
    {"name": "Video Processor", "value": "Apple"},
    {"name": "Processor Type", "value": "Apple M3"},
    {"name": "Processor Brand", "value": "Apple"},
    {"name": "Cpu Model Number", "value": "Apple M3 chip with 8-core CPU and 10-core GPU"},
])

check(
    "MacBook Air M3: Cpu Model / Processor Type beats Video Processor",
    find_cpu(macbook_specs) == "apple m3",
)

vivobook_specs = _normalize_specs([
    {"name": "Cpu Model", "value": "Snapdragon X Elite"},
    {"name": "Graphics Co Processor", "value": "Qualcomm Adreno GPU"},
    {"name": "Video Processor", "value": "Qualcomm"},
    {"name": "Processor Type", "value": "Snapdragon X Elite"},
    {"name": "Processor Brand", "value": "Qualcomm"},
])

check(
    "Vivobook Snapdragon X Elite: Processor Type beats Video Processor",
    find_cpu(vivobook_specs) == "snapdragon x elite",
)

# --------------------------------------------------------------
# GPU/video-processor field alone (no dedicated CPU field at
# all) must never be treated as a CPU value -- the exclusion is
# absolute, not just a lower-priority fallback.
# --------------------------------------------------------------

gpu_only_specs = _normalize_specs([
    {"name": "Video Processor", "value": "NVIDIA"},
    {"name": "Graphics Co Processor", "value": "NVIDIA RTX 4070"},
])

check(
    "No dedicated CPU field present -> GPU fields are excluded entirely, "
    "find_cpu() honestly returns nothing rather than a mislabeled GPU value",
    find_cpu(gpu_only_specs) is None,
)

# --------------------------------------------------------------
# End-to-end: the fix must actually change the laptop score/
# reasons for the three audited products, not just the raw
# _find_spec() lookup.
# --------------------------------------------------------------

reasons, score = laptop_reasons([
    {"name": "Cpu Model", "value": "Intel Core Ultra 5"},
    {"name": "Video Processor", "value": "Intel"},
    {"name": "Processor Type", "value": "Intel Core Ultra 5"},
    {"name": "Ram", "value": "16 GB"},
])
check(
    "Zenbook-shaped laptop now correctly tiers as 'Powerful Processor' "
    "(Ultra 5), not the generic 'Processor Detected' bucket",
    "Powerful Processor" in reasons and "Processor Detected" not in reasons,
)

reasons, score = laptop_reasons([
    {"name": "Cpu Model", "value": "Ryzen 7 7445HS"},
    {"name": "Video Processor", "value": "AMD"},
    {"name": "Processor Type", "value": "Ryzen 7 7445HS"},
    {"name": "Ram", "value": "16 GB"},
])
check(
    "Ryzen-7-shaped laptop with a Video Processor field still correctly "
    "tiers as 'High Performance Processor'",
    "High Performance Processor" in reasons,
)

# --------------------------------------------------------------
# Regression: an explicit, standalone "Processor" field (exact
# name match) still wins immediately -- this is the existing
# behavior that spared HP Pavilion / HP Victus / Acer Aspire
# Lite in the audit.
# --------------------------------------------------------------

hp_pavilion_specs = _normalize_specs([
    {"name": "Cpu Model", "value": "Core i5"},
    {"name": "Video Processor", "value": "Intel"},
    {"name": "Processor", "value": "12Th Gen Intel Core I5"},
])

check(
    "Exact-name 'Processor' field still wins immediately (unchanged behavior)",
    find_cpu(hp_pavilion_specs) == "12th gen intel core i5",
)

# --------------------------------------------------------------
# Regression: smartphone processor detection is unaffected.
# --------------------------------------------------------------

reasons = recommend(
    [{"name": "Processor", "value": "Snapdragon 8 Elite"}],
    "smartphone",
)["reasons"]
check(
    "Smartphone processor detection (exact 'Processor' field) unchanged -> Flagship Processor",
    "Flagship Processor" in reasons,
)

s25_ultra_like_specs = _normalize_specs([
    {"name": "Cpu Model", "value": "Snapdragon 8 Elite"},
    {"name": "Processor Series", "value": "Snapdragon 8 Elite"},
    {"name": "Processor Speed", "value": "4.47 GHz"},
    {"name": "Processor", "value": "Snapdragon 8 Elite for Galaxy"},
])

check(
    "Smartphone with no Video Processor field still resolves the "
    "dedicated 'Processor' field first, unaffected by the fix",
    find_cpu(s25_ultra_like_specs) == "snapdragon 8 elite for galaxy",
)

oneplus13_like_specs = _normalize_specs([
    {"name": "Cpu Model", "value": "Snapdragon 8 Elite"},
    {"name": "Cpu Speed", "value": "3.2 GHz"},
    {"name": "Processor Series", "value": "Snapdragon 8 Elite"},
    {"name": "Processor Speed", "value": "3.2 GHz"},
])

check(
    "Smartphone with only Processor Series/Speed (no Video Processor, "
    "no bare Processor field) still resolves the CPU value correctly",
    find_cpu(oneplus13_like_specs) == "snapdragon 8 elite",
)

print()
print("All _find_spec processor-priority checks passed.")
