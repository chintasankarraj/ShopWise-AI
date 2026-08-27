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

# --------------------------------------------------------------
# Fix: a real listing whose title has no generic category noun
# ("phone"/"mobile"/"smartphone") and whose specs happen to omit
# an "Item Type" field must still resolve from structural
# evidence (OS + cellular generation + phone-sized screen)
# instead of falling through to generic "electronics". This is
# the exact shape of the Redmi Note 14 Pro 5G bug found in the
# real-world QA audit.
# --------------------------------------------------------------

check(
    "Redmi Note 14 Pro 5G-shaped payload (no 'phone' in title, "
    "no Item Type field) -> smartphone, not electronics",
    detect_category(
        "Redmi Note 14 Pro 5G",
        [
            {"name": "Operating System", "value": "Android 14"},
            {"name": "Ram", "value": "8 GB"},
            {"name": "Cpu Model", "value": "Mediatek Dimensity 7300"},
            {"name": "Storage", "value": "256 GB"},
            {"name": "Screen Size Unit Of Measure", "value": "6.67 Inches"},
            {"name": "Network Connectivity Technology", "value": "Bluetooth, NFC, USB, Wi-Fi"},
        ],
    )
    == "smartphone",
)

check(
    "Normal smartphone title with the explicit keyword still matches directly",
    detect_category("OnePlus 13 Smartphone with OnePlus AI", []) == "smartphone",
)

check(
    "Laptop title/spec payload without a generic 'laptop' word in the "
    "title still resolves from structural evidence",
    detect_category(
        "ASUS ZenPro X14 UX9404, 16GB RAM, 1TB SSD",
        [
            {"name": "Operating System", "value": "Windows 11 Home"},
            {"name": "Ram", "value": "16 GB"},
            {"name": "Hard Drive Size", "value": "1 TB"},
            {"name": "Screen Size", "value": "14 Inches"},
        ],
    )
    == "laptop",
)

check(
    "Laptop title with the explicit 'Laptop' keyword still matches directly",
    detect_category("Acer Aspire Lite ... Laptop", []) == "laptop",
)

check(
    "A tablet whose title says 'Tablet' is not hijacked by the new "
    "smartphone structural fallback even with a phone-sized screen",
    detect_category(
        "Lenovo Tab M8 Android Tablet",
        [
            {"name": "Operating System", "value": "Android 13"},
            {"name": "Screen Size", "value": "8 Inches"},
            {"name": "Cellular", "value": "4G"},
        ],
    )
    == "tablet",
)

check(
    "An Android tablet with cellular but a large screen is not "
    "misclassified as a smartphone by the structural fallback",
    detect_category(
        "Generic 10.5 inch Android Slate",
        [
            {"name": "Operating System", "value": "Android 13"},
            {"name": "Screen Size", "value": "10.5 Inches"},
            {"name": "Network Connectivity Technology", "value": "4G, Wi-Fi"},
        ],
    )
    != "smartphone",
)

check(
    "Unrelated electronics with no OS/cellular/computer signals "
    "remain electronics, not hijacked by either new fallback",
    detect_category(
        "Generic Bluetooth USB Adapter Dongle",
        [
            {"name": "Connectivity", "value": "Bluetooth 5.0, USB"},
        ],
    )
    == "electronics",
)

print()
print("All category_detector.py checks passed.")
