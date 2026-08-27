from app.agents.insights_agent import (
    _prepare_review_texts,
    _build_review_section,
    _MAX_REVIEWS_FOR_PROMPT,
    _MAX_CHARS_PER_REVIEW,
)


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


# --------------------------------------------------------------
# _prepare_review_texts: empty / missing input
# --------------------------------------------------------------

check(
    "None -> empty list (no crash)",
    _prepare_review_texts(None) == [],
)
check(
    "empty list -> empty list",
    _prepare_review_texts([]) == [],
)
check(
    "blank/whitespace-only entries are dropped",
    _prepare_review_texts(["", "   ", "\n"]) == [],
)

# --------------------------------------------------------------
# _prepare_review_texts: real reviews pass through
# --------------------------------------------------------------

prepared = _prepare_review_texts(["Great phone!", "Battery could be better."])
check(
    "real reviews pass through unchanged (under the cap)",
    prepared == ["Great phone!", "Battery could be better."],
)

# --------------------------------------------------------------
# _prepare_review_texts: safety caps (Issue 3 requirement 7)
# --------------------------------------------------------------

many_reviews = [f"Review number {i}" for i in range(50)]
capped = _prepare_review_texts(many_reviews)
check(
    f"count is capped at _MAX_REVIEWS_FOR_PROMPT ({_MAX_REVIEWS_FOR_PROMPT})",
    len(capped) == _MAX_REVIEWS_FOR_PROMPT,
)

long_review = "x" * 2000
truncated = _prepare_review_texts([long_review])[0]
check(
    f"long review text is truncated to <= {_MAX_CHARS_PER_REVIEW + 1} chars",
    len(truncated) <= _MAX_CHARS_PER_REVIEW + 1,
)
check(
    "truncated review is marked with an ellipsis",
    truncated.endswith("…"),
)

short_review = "short review"
check(
    "short review is NOT truncated/marked",
    _prepare_review_texts([short_review])[0] == short_review,
)

# --------------------------------------------------------------
# _build_review_section: no reviews -> honest "Not Available"
# --------------------------------------------------------------

empty_section = _build_review_section([], 4.1, 4)
check(
    "no reviews -> section instructs 'Not Available'",
    '"overall_sentiment": "Not Available"' in empty_section,
)
check(
    "no reviews -> section does NOT claim real review text exists",
    "REAL customer review text" not in empty_section,
)

# --------------------------------------------------------------
# _build_review_section: real reviews -> real analysis instructed
# --------------------------------------------------------------

real_reviews = ["Battery lasts all day.", "Camera is disappointing in low light."]
real_section = _build_review_section(real_reviews, 4.1, 4)

check(
    "real reviews -> section includes the actual review text",
    "Battery lasts all day." in real_section
    and "Camera is disappointing in low light." in real_section,
)
check(
    "real reviews -> section does NOT hardcode 'Not Available'",
    '"overall_sentiment": "Not Available"' not in real_section,
)
check(
    "real reviews -> section explicitly warns against using the star rating as sentiment evidence",
    "metadata ONLY" in real_section,
)
check(
    "real reviews -> section forbids inferring from specifications",
    "Do NOT" in real_section and "specifications" in real_section,
)

print()
print("All insights review-prompt checks passed.")
