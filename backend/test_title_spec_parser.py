from app.services.title_spec_parser import extract_title_specifications


def spec_map(title):
    return {s["name"]: s["value"] for s in extract_title_specifications(title)}


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


# --------------------------------------------------------------
# Fix: display sizes written in prose ("6.77 inch AMOLED
# display") should be extracted as Display Size, not just the
# quote/prime-symbol form ("6.77\"").
# --------------------------------------------------------------

specs = spec_map("Phone with 6.77 inch AMOLED display and 5000mAh Battery")
check(
    '"6.77 inch AMOLED display" -> Display Size = "6.77 inch AMOLED"',
    specs.get("Display Size") == "6.77 inch AMOLED",
)

specs = spec_map("Laptop with a stunning 15.6 inches Full HD screen")
check(
    '"15.6 inches" (plural) -> Display Size = "15.6 inch"',
    specs.get("Display Size") == "15.6 inch",
)

# Regression: the original quote/prime-symbol form must keep
# working unchanged.
specs = spec_map('Phone (6.77" AMOLED 120Hz Display)')
check(
    'quote-symbol form still works -> Display Size = "6.77 inch AMOLED"',
    specs.get("Display Size") == "6.77 inch AMOLED",
)

# Regression: a bare "in" abbreviation must NOT be treated as
# inches (too ambiguous -- "Built-in", "in Ear", etc).
specs = spec_map("Wireless Earbuds with Built-in Microphone, 10 hours Battery Life")
check(
    'bare "in" (e.g. "Built-in") is not hallucinated as Display Size',
    "Display Size" not in specs,
)


# --------------------------------------------------------------
# Fix: common Intel and AMD/Ryzen processors should be
# extracted from titles when product_information doesn't
# already provide them.
# --------------------------------------------------------------

specs = spec_map(
    "Dell Inspiron 15 3520 Laptop (12th Gen Intel Core i5-1235U, "
    "16GB RAM, 512GB SSD, Windows 11, 15.6 inch FHD)"
)
check(
    '"12th Gen Intel Core i5-1235U" -> Processor captures generation + model',
    specs.get("Processor") == "12th Gen Intel Core i5-1235U",
)

specs = spec_map("HP Smartchoice Victus, AMD Ryzen 7 7445HS, 16GB DDR5, 512GB SSD")
check(
    '"AMD Ryzen 7 7445HS" -> Processor extracted',
    specs.get("Processor") == "AMD Ryzen 7 7445HS",
)

specs = spec_map("Lenovo IdeaPad, Ryzen 5 5500U, 8GB RAM, 512GB SSD")
check(
    'bare "Ryzen 5 5500U" (no "AMD" prefix) -> Processor extracted',
    specs.get("Processor") == "Ryzen 5 5500U",
)

specs = spec_map("Acer Aspire 1 Slim Laptop, Intel Celeron Dual-Core Processor, 12GB RAM")
check(
    '"Intel Celeron" -> Processor extracted',
    specs.get("Processor") is not None
    and specs["Processor"].startswith("Intel Celeron"),
)

# Regression: existing phone chipset patterns still take
# priority and are unaffected by the new laptop patterns.
specs = spec_map("Nothing Phone 3a Pro 5G | Snapdragon 7s Gen 3 | 50MP Camera")
check(
    "existing Snapdragon phone pattern still works unchanged",
    specs.get("Processor") == "Snapdragon 7s Gen 3",
)

print()
print("All title_spec_parser.py checks passed.")
