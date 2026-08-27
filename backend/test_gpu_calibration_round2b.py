"""
Round 2B: adversarial calibration validation for the laptop GPU
dimension, plus adversarial missing/ambiguous-data tests across GPU,
refresh rate, resolution, and battery. These exist specifically to
find inversions and invented-capability bugs before committing --
see recommendation_agent.py's _dedicated_gpu_tier_from_vram()
docstring for the calibration reasoning.
"""

from app.agents.recommendation_agent import (
    recommend,
    _normalize_specs,
    _score_laptop_gpu,
)


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


def gpu(desc=None, co=None, title=None, cpu_model_number=None, vram=None):
    specs = []
    if desc is not None:
        specs.append({"name": "Graphics Card Description", "value": desc})
    if co is not None:
        specs.append({"name": "Graphics Co Processor", "value": co})
    if cpu_model_number is not None:
        specs.append({"name": "Cpu Model Number", "value": cpu_model_number})
    if vram is not None:
        specs.append({"name": "Graphics Ram Size", "value": vram})
    return _score_laptop_gpu(_normalize_specs(specs), title=title)


def laptop_result(specs, title=None):
    return recommend(specs, "laptop", title=title)


# ================================================================
# 1. GPU calibration -- the specific real-product inversion
# ================================================================

hp_victus_points, hp_victus_reason = gpu("Dedicated", "AMD Radeon R7", vram="6 GB")
acer_nitro_points, acer_nitro_reason = gpu("Dedicated", "NVIDIA GeForce RTX 4050", vram="6 GB")

check(
    "real audited pair no longer inverted: HP Victus (RTX 3050, VRAM-fallback path) "
    "and Acer Nitro V (RTX 4050, model-number path) now score identically instead of "
    "the older/weaker-generation card outscoring the newer one",
    hp_victus_points == acer_nitro_points and hp_victus_reason == acer_nitro_reason,
)
check(
    "both resolve to the correct 'Entry' tier, not just an accidental tie at the wrong value",
    (hp_victus_points, hp_victus_reason) == (6, "Entry Dedicated GPU"),
)


# ================================================================
# 2. Broader GPU capability ordering -- integrated -> Iris Xe/Arc
# -> entry dedicated -> capable -> high-end -> flagship. Detects
# inversions rather than asserting exact point values everywhere.
# ================================================================

ordering = [
    ("integrated basic (UHD)",        gpu("Integrated", "Intel UHD Graphics")[0]),
    ("integrated Iris Xe",            gpu("Integrated", "Intel Iris Xe Graphics")[0]),
    ("integrated Arc",                gpu("Integrated", "Intel Arc Graphics")[0]),
    ("Apple integrated (10-core GPU)", gpu("Integrated", cpu_model_number="Apple M3 chip with 8-core CPU and 10-core GPU")[0]),
    ("dedicated GTX 1650 (old entry)", gpu("Dedicated", "NVIDIA GeForce GTX 1650")[0]),
    ("dedicated RTX 2050",            gpu("Dedicated", "NVIDIA GeForce RTX 2050")[0]),
    ("dedicated RTX 3050 (real HP Victus data shape)", gpu("Dedicated", "AMD Radeon R7", vram="6 GB")[0]),
    ("dedicated RTX 4050 (real Acer Nitro V data shape)", gpu("Dedicated", "NVIDIA GeForce RTX 4050", vram="6 GB")[0]),
    ("dedicated RTX 4060",            gpu("Dedicated", "NVIDIA GeForce RTX 4060", vram="8 GB")[0]),
    ("dedicated AMD Radeon RX 6600",  gpu("Dedicated", "AMD Radeon RX 6600", vram="8 GB")[0]),
    ("dedicated RTX 4070",            gpu("Dedicated", "NVIDIA GeForce RTX 4070", vram="8 GB")[0]),
    ("dedicated RTX 4080",            gpu("Dedicated", "NVIDIA GeForce RTX 4080", vram="12 GB")[0]),
]

check(
    "integrated basic strictly below Iris Xe/Arc/Apple-integrated "
    "(no bonus merely for having a GPU field)",
    ordering[0][1] < ordering[1][1] == ordering[2][1] == ordering[3][1],
)
check(
    "capable-integrated tier strictly below every dedicated tier "
    "(an integrated GPU never outscores a confirmed dedicated one)",
    ordering[3][1] < ordering[4][1],
)
check(
    "old entry-class dedicated (GTX 1650) does not outrank newer entry-class (RTX 2050/3050/4050)",
    ordering[4][1] <= ordering[5][1] == ordering[6][1] == ordering[7][1],
)
check(
    "RTX 4060 and a same-VRAM-class AMD RX 6600 land in the same capable tier "
    "(no cross-vendor favoritism at equivalent evidence)",
    ordering[8][1] == ordering[9][1],
)
check(
    "RTX 4060 strictly outranks entry-tier RTX 3050/4050 "
    "(the specific class of inversion this round set out to catch)",
    ordering[6][1] < ordering[8][1] and ordering[7][1] < ordering[8][1],
)
check(
    "RTX 4070 strictly outranks RTX 4060, RTX 4080 strictly outranks RTX 4070 "
    "(monotonic within a single reliable-text vendor scale)",
    ordering[8][1] < ordering[10][1] < ordering[11][1],
)

# Print the full ordering for human review even though the checks
# above are what actually gate pass/fail.
print()
print("Full GPU ordering (points):")
for label, points in ordering:
    print(f"  {points:2d}  {label}")
print()


# ================================================================
# 3. Adversarial missing/ambiguous GPU data
# ================================================================

check(
    "GPU field exists but is empty string -> no capability invented",
    gpu("Dedicated", "") == (4, "Dedicated GPU Detected"),
)
check(
    "GPU field says only the generic word 'Graphics' -> no capability invented",
    gpu("Dedicated", "Graphics") == (4, "Dedicated GPU Detected"),
)
check(
    "GPU-related field slot actually contains unrelated CPU information "
    "(e.g. a stray Cpu Model Number with no GPU mention) -> no capability invented",
    gpu("Integrated", cpu_model_number="Intel Core i7-1355U, 10 cores, up to 5.0 GHz") == (0, None),
)
check(
    "dedicated confirmed, GPU text names a real but totally unrecognized chip, "
    "no VRAM field present -> minimal detected-only tier, nothing invented",
    gpu("Dedicated", "Zorblax GPU 9000") == (4, "Dedicated GPU Detected"),
)
check(
    "dedicated confirmed, no VRAM field at all, no recognizable model number "
    "-> minimal tier, not a crash, not a 0",
    gpu("Dedicated") == (4, "Dedicated GPU Detected"),
)
check(
    "Graphics Card Description field itself entirely absent, but stray GPU-ish "
    "text exists -> never promoted into the dedicated branch without the "
    "structured confirmation",
    gpu(None, "NVIDIA GeForce RTX 4090") != (12, "Flagship Dedicated GPU"),
)


# ================================================================
# 4. Adversarial missing refresh rate / resolution
# ================================================================

result = laptop_result([{"name": "Ram", "value": "16 GB"}])
check(
    "refresh rate absent entirely -> no refresh-tier reason, no crash",
    not any("Refresh" in r or "Hz Display" in r for r in result["reasons"]),
)

result = laptop_result([{"name": "Display", "value": "Vibrant colors, wide viewing angles"}])
check(
    "resolution absent entirely (no dedicated field, no WxH in Display prose) "
    "-> no resolution-tier reason invented",
    not any(
        r in ("High Resolution Display", "Full HD+ Display")
        for r in result["reasons"]
    ),
)

result = laptop_result([{"name": "Display", "value": "16:10 aspect ratio, 500 nits peak brightness"}])
check(
    "Display prose contains unrelated numbers (aspect ratio, nits) -> neither "
    "resolution nor refresh rate is misread from them",
    not any(
        r in ("High Resolution Display", "Full HD+ Display", "Very High Refresh Rate", "120Hz Display", "90Hz Display")
        for r in result["reasons"]
    ),
)


# ================================================================
# 5. Adversarial battery data
# ================================================================

result = laptop_result([{"name": "Battery Cell Type", "value": "Lithium Ion"}])
check(
    "battery field exists but only states the cell chemistry (no capacity at all) "
    "-> no battery reason, no crash",
    not any("Battery" in r for r in result["reasons"]),
)

result = laptop_result([
    {"name": "Battery Cell Type", "value": "Lithium Ion"},
    {"name": "Battery Life", "value": "10 Hours"},
])
check(
    "battery fields exist but state only a duration, never a Wh figure anywhere "
    "-> no battery reason invented from the hours value",
    not any("Battery" in r for r in result["reasons"]),
)

print()
print("All Round 2B GPU calibration and adversarial checks passed.")
