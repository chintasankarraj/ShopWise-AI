"""
Confirms the scoring engine does NOT penalize a product merely
because its extracted RAM value equals its extracted Storage
value. Equal RAM/Storage can be a genuine, legitimate spec (and
separately, a mismatched value can also be a data-quality issue
that isn't ours to silently "fix" by penalizing the product) --
either way, the score must come purely from each field's own
independent tier, with no cross-field equality check.
"""

from app.agents.recommendation_agent import recommend


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


def score_for(ram_value, storage_value):
    specs = [
        {"name": "Ram", "value": ram_value},
        {"name": "Storage", "value": storage_value},
    ]
    return recommend(specs, "smartphone")


# --------------------------------------------------------------
# Equal RAM/Storage is scored the same as if they were two
# independent, unrelated fields -- no penalty, no special-case
# deduction, just each field's own normal tier.
# --------------------------------------------------------------

result = score_for("128 GB", "128 GB")
check(
    "equal RAM (128GB) and Storage (128GB) both still score their "
    "own normal tiers",
    "Excellent RAM" in result["reasons"]
    and "Good Storage" in result["reasons"],
)

result_equal = score_for("8 GB", "8 GB")
check(
    "a smaller equal RAM/Storage pair (8GB/8GB) is also not "
    "specially penalized -- RAM still gets its normal 'Good RAM' tier",
    "Good RAM" in result_equal["reasons"],
)

# --------------------------------------------------------------
# The score for equal values must match exactly what the same
# two numbers would score if they were NOT equal to each other
# (i.e. no hidden equality-triggered deduction exists at all).
# --------------------------------------------------------------

result_a = score_for("12 GB", "12 GB")
result_b = score_for("12 GB", "13 GB")

RAM_STORAGE_REASONS = {
    "Excellent RAM",
    "Good RAM",
    "Adequate RAM",
    "Excellent Storage",
    "Large Storage",
    "Good Storage",
}

check(
    "RAM's own score component is identical whether Storage happens "
    "to equal it (12/12) or not (12/13) -- proving there is no "
    "equality-based penalty anywhere in the scoring path",
    result_a["score"] == result_b["score"],
)

# --------------------------------------------------------------
# Regression: genuinely different RAM/Storage values still
# behave exactly as before (each scores its own independent
# tier, unaffected by this change).
# --------------------------------------------------------------

result = score_for("6 GB", "256 GB")
check(
    "genuinely different RAM (6GB) and Storage (256GB) still score "
    "their own correct, independent tiers",
    "Adequate RAM" in result["reasons"]
    and "Large Storage" in result["reasons"],
)

result = score_for("16 GB", "512 GB")
check(
    "another genuinely different pair (16GB RAM / 512GB Storage) "
    "still scores correctly",
    "Excellent RAM" in result["reasons"]
    and "Excellent Storage" in result["reasons"],
)

print()
print("All RAM/Storage data-quality checks passed.")
