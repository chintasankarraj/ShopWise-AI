import re


def extract_specs(title: str):
    specs = {}

    # CPU
    cpu_match = re.search(
        r"(Intel Core [A-Za-z0-9\s\-]+|AMD Ryzen [A-Za-z0-9\s\-]+)",
        title,
        re.IGNORECASE,
    )
    specs["cpu"] = cpu_match.group(0) if cpu_match else None

    # RAM
    ram_match = re.search(r"(\d+\s?GB)", title, re.IGNORECASE)
    specs["ram"] = ram_match.group(1) if ram_match else None

    # Storage
    storage_match = re.search(r"(\d+\s?(GB|TB)\s?SSD)", title, re.IGNORECASE)
    specs["storage"] = storage_match.group(1) if storage_match else None

    # Display
    display_match = re.search(r'(\d{2}\.?\d?")', title)
    specs["display"] = display_match.group(1) if display_match else None

    return specs