from app.agents.alternative_agent import find_alternatives


class TestProduct:
    title = "REDMI Note 17 5G"
    price = "₹27,999"


product = TestProduct()

specs = [
    {
        "name": "RAM",
        "value": "6 GB"
    },
    {
        "name": "Storage",
        "value": "128 GB"
    },
    {
        "name": "Display",
        "value": "6.99 inch AMOLED 120Hz"
    },
    {
        "name": "Battery",
        "value": "8000 mAh"
    },
    {
        "name": "Processor",
        "value": "Snapdragon 4 Gen 4"
    },
    {
        "name": "Camera",
        "value": "50 MP"
    },
    {
        "name": "Charging",
        "value": "45 W"
    },
    {
        "name": "Cellular",
        "value": "5G"
    }
]


print("=" * 80)
print("SHOPWISE ALTERNATIVE AGENT TEST")
print("=" * 80)

try:

    result = find_alternatives(
        product,
        specs
    )

    print("\nRESULT:")
    print(result)

except Exception as error:

    print("\nERROR:")
    print(type(error).__name__)
    print(error)

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)