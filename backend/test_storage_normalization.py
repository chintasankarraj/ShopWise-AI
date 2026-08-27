"""
Regression tests for the laptop storage unit-normalization fix
(QA Audit Round 1, Issue 3). _score_laptop()'s storage tier
checks ("2tb" in storage / "1tb" in storage / "512gb" in storage)
were space-sensitive: a real extracted value like "1 TB" (with a
space, the overwhelmingly common Amazon formatting) matched none
of them, silently zeroing 14-15 legitimate storage points.
Confirmed live on 5 of 6 laptops in the real-world QA audit.
"""

from app.agents.recommendation_agent import _normalize_unit_spacing, recommend


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


def laptop_result(storage_value):
    specs = [
        {"name": "Hard Drive Size", "value": storage_value},
    ]
    return recommend(specs, "laptop")


# --------------------------------------------------------------
# _normalize_unit_spacing() unit-level checks
# --------------------------------------------------------------

check('"1 TB" normalizes to "1TB"', _normalize_unit_spacing("1 TB") == "1TB")
check('"1-TB" normalizes to "1TB"', _normalize_unit_spacing("1-TB") == "1TB")
check('"1tb" is left unchanged', _normalize_unit_spacing("1tb") == "1tb")
check('"512 GB" normalizes to "512GB"', _normalize_unit_spacing("512 GB") == "512GB")
check("None passes through unchanged", _normalize_unit_spacing(None) is None)
check('empty string passes through unchanged', _normalize_unit_spacing("") == "")

# --------------------------------------------------------------
# End-to-end: every equivalent representation of "1 TB" must
# score identically through _score_laptop().
# --------------------------------------------------------------

baseline = laptop_result("1TB")
check(
    "baseline '1TB' (already space-free) scores 'Large Storage'",
    "Large Storage" in baseline["reasons"],
)

for variant in ["1 TB", "1-TB", "1tb", "1 tb", "1-tb"]:
    result = laptop_result(variant)
    check(
        f"laptop storage {variant!r} scores identically to baseline '1TB' "
        f"(score={result['score']}, baseline={baseline['score']})",
        result["score"] == baseline["score"]
        and "Large Storage" in result["reasons"],
    )

# --------------------------------------------------------------
# 2TB and 512GB tiers, same spacing variants.
# --------------------------------------------------------------

baseline_2tb = laptop_result("2TB")
for variant in ["2 TB", "2-TB", "2tb"]:
    result = laptop_result(variant)
    check(
        f"laptop storage {variant!r} matches the 2TB tier consistently",
        result["score"] == baseline_2tb["score"]
        and "Large Storage" in result["reasons"],
    )

baseline_512 = laptop_result("512GB")
for variant in ["512 GB", "512-GB", "512gb"]:
    result = laptop_result(variant)
    check(
        f"laptop storage {variant!r} matches the 512GB tier consistently",
        result["score"] == baseline_512["score"]
        and "Fast SSD" in result["reasons"],
    )

# --------------------------------------------------------------
# Regression: existing tier boundaries/point values are
# unchanged -- 2TB still outranks 1TB which still outranks
# 512GB, and the plain "ssd" catch-all still works.
# --------------------------------------------------------------

check(
    "2TB still scores strictly higher than 1TB (tier ordering unchanged)",
    baseline_2tb["score"] > baseline["score"],
)
check(
    "1TB still scores strictly higher than 512GB (tier ordering unchanged)",
    baseline["score"] > baseline_512["score"],
)

ssd_only = laptop_result("SSD")
check(
    "plain 'SSD' with no capacity number still hits the generic SSD Storage tier",
    "SSD Storage" in ssd_only["reasons"],
)

no_storage = laptop_result("")
check(
    "empty storage value contributes no storage reason (unchanged)",
    "Large Storage" not in no_storage["reasons"]
    and "Fast SSD" not in no_storage["reasons"]
    and "SSD Storage" not in no_storage["reasons"],
)

print()
print("All storage normalization checks passed.")
