from app.services.category_detector import detect_category


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


# --------------------------------------------------------------
# Fix: realistic TV titles where "TV" is separated from its
# qualifier by a brand/platform word (e.g. "Smart Google TV")
# should still be detected as television, not generic
# electronics.
# --------------------------------------------------------------

check(
    'coocaa 55" 4K Google TV -> television',
    detect_category(
        "coocaa 138 cm (55 inch) Frameless UHD 4K Smart Google TV 55Y74",
        [
            {"name": "Connectivity Technology", "value": "Ethernet, HDMI, USB, Wi-Fi"},
        ],
    )
    == "television",
)

check(
    'Simple "... TV" title -> television',
    detect_category("Samsung 43 inch LED TV", []) == "television",
)

# --------------------------------------------------------------
# Regression: existing exact-phrase keywords still match.
# --------------------------------------------------------------

check(
    '"Smart TV" exact phrase still matches -> television',
    detect_category("Samsung 43 inch Smart TV", []) == "television",
)

check(
    '"4K TV" exact phrase still matches -> television',
    detect_category("LG 55 inch 4K TV", []) == "television",
)

# --------------------------------------------------------------
# Regression: "TV" as a standalone word must not fire on
# unrelated tokens that merely contain the letters "tv" glued to
# another letter (word-boundary check).
# --------------------------------------------------------------

check(
    '"TVS" (glued letters, not standalone "tv") does not force television',
    detect_category("TVS Motor Company Annual Report", []) != "television",
)

# --------------------------------------------------------------
# Regression: other categories are unaffected by this change.
# --------------------------------------------------------------

check(
    "Smartphone title still detected as smartphone",
    detect_category("Samsung Galaxy S25 Ultra 5G AI Smartphone", []) == "smartphone",
)

check(
    "Laptop title still detected as laptop",
    detect_category("Dell Inspiron 15 Laptop", []) == "laptop",
)

print()
print("All category_detector.py checks passed.")
