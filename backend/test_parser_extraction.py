from bs4 import BeautifulSoup

from app.services.parser import (
    extract_specifications,
    specification_richness,
    is_relevant,
)


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


def spec_map(specs):
    return {s["name"]: s["value"] for s in specs}


# ================================================================
# FIX 2 -- prefer the richer of two same-named specifications
# ================================================================

SPARSE_DISPLAY = "6.1 in"

RICH_DISPLAY = (
    "Super Retina XDR display, 15.54 cm / 6.1-inch (diagonal), "
    "all-screen OLED display, 2556x1179-pixel resolution at 460 ppi"
)

check(
    "richness: the rich, detail-dense Display value scores higher "
    "than the sparse size-only value",
    specification_richness(RICH_DISPLAY) > specification_richness(SPARSE_DISPLAY),
)

check(
    "richness: empty value scores the minimum (0, 0, 0)",
    specification_richness("") == (0, 0, 0)
    and specification_richness(None) == (0, 0, 0),
)

check(
    "richness: a long but low-content (repeated-character) value does "
    "NOT beat a short, information-dense one, no matter how long the "
    "garbage is -- not just 'longest wins'",
    specification_richness("5000 mAh Li-Po")
    > specification_richness("A" * 500),
)

# --------------------------------------------------------------
# End-to-end: sparse Display encountered first, rich Display
# encountered later (in a separate table, mirroring the real
# Amazon page shape) -> the rich value must be the one kept.
# --------------------------------------------------------------

html_sparse_then_rich = f"""
<html><body>
<table>
  <tr><th>Display</th><td>{SPARSE_DISPLAY}</td></tr>
</table>
<table>
  <tr><th>Display</th><td>{RICH_DISPLAY}</td></tr>
</table>
</body></html>
"""

soup = BeautifulSoup(html_sparse_then_rich, "lxml")
specs = spec_map(extract_specifications(soup))

check(
    "sparse Display (first) + rich Display (later) -> rich value wins",
    specs.get("Display") == RICH_DISPLAY,
)

# Reversed order: rich encountered first, sparse later -- richer
# value must still win regardless of encounter order.

html_rich_then_sparse = f"""
<html><body>
<table>
  <tr><th>Display</th><td>{RICH_DISPLAY}</td></tr>
</table>
<table>
  <tr><th>Display</th><td>{SPARSE_DISPLAY}</td></tr>
</table>
</body></html>
"""

soup = BeautifulSoup(html_rich_then_sparse, "lxml")
specs = spec_map(extract_specifications(soup))

check(
    "rich Display (first) + sparse Display (later) -> rich value still wins",
    specs.get("Display") == RICH_DISPLAY,
)

# --------------------------------------------------------------
# Regression: a normal, single-occurrence spec is unaffected.
# --------------------------------------------------------------

html_single = """
<html><body>
<table>
  <tr><th>RAM</th><td>8 GB</td></tr>
  <tr><th>Storage</th><td>256 GB</td></tr>
</table>
</body></html>
"""

soup = BeautifulSoup(html_single, "lxml")
specs = spec_map(extract_specifications(soup))

check(
    "existing normal single-value specs are unchanged",
    specs.get("Ram") == "8 GB" and specs.get("Storage") == "256 GB",
)

# --------------------------------------------------------------
# Regression: duplicate handling for one field doesn't disturb
# unrelated fields, doesn't produce duplicate entries, and the
# surviving spec keeps its original first-seen list position.
# --------------------------------------------------------------

html_mixed = f"""
<html><body>
<table>
  <tr><th>Display</th><td>{SPARSE_DISPLAY}</td></tr>
  <tr><th>Battery</th><td>5000 mAh</td></tr>
</table>
<table>
  <tr><th>Display</th><td>{RICH_DISPLAY}</td></tr>
</table>
</body></html>
"""

soup = BeautifulSoup(html_mixed, "lxml")
result = extract_specifications(soup)
names = [s["name"] for s in result]

check(
    "duplicate Display collapses to exactly one entry",
    names.count("Display") == 1,
)
check(
    "the unrelated Battery spec is untouched by Display's dedup",
    spec_map(result).get("Battery") == "5000 mAh",
)
check(
    "the surviving Display entry keeps its original first-seen position",
    names.index("Display") == 0,
)


# ================================================================
# FIX 3 -- recognize "resistant" (adjective) wording, not just
# "resistance" (noun), for durability specs
# ================================================================

check(
    '"Water Resistant" is now relevant',
    is_relevant("Water Resistant"),
)
check(
    '"Water Resistance" (existing noun form) still relevant',
    is_relevant("Water Resistance"),
)
check(
    '"Dust Resistant" is now relevant',
    is_relevant("Dust Resistant"),
)
check(
    '"Dust Resistance" (existing noun form) still relevant',
    is_relevant("Dust Resistance"),
)

check(
    "an unrelated field name is NOT swept in by the broadened match",
    not is_relevant("Water Bottle Capacity"),
)

# --------------------------------------------------------------
# End-to-end: the actual real-world Amazon field name that
# triggered this fix.
# --------------------------------------------------------------

html_water_resistant = """
<html><body>
<table>
  <tr>
    <th>Splash, Water, and Dust Resistant</th>
    <td>Rated IP68 (maximum depth of 6 metres up to 30 minutes) under IEC standard 60529</td>
  </tr>
</table>
</body></html>
"""

soup = BeautifulSoup(html_water_resistant, "lxml")
specs = spec_map(extract_specifications(soup))

check(
    "the real 'Splash, Water, and Dust Resistant' Amazon field is no "
    "longer discarded",
    any("ip68" in value.lower() for value in specs.values()),
)

print()
print("All parser extraction checks passed.")
