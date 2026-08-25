from app.agents.recommendation_agent import recommend


specs = [

    {
        "name": "Operating System",
        "value": "OxygenOS 16",
    },

    {
        "name": "Ram",
        "value": "8 GB",
    },

    {
        "name": "Cpu Model",
        "value": "Mediatek Dimensity 7400",
    },

    {
        "name": "Cpu Speed",
        "value": "2.6 GHz",
    },

    {
        "name": "Processor Series",
        "value": "Mediatek Dimensity 7400",
    },

    {
        "name": "Processor Speed",
        "value": "2.6 GHz",
    },

    {
        "name": "Storage",
        "value": "256 GB",
    },

    {
        "name": "Colour",
        "value": "Hyper Black",
    },

    {
        "name": "Form Factor",
        "value": "Bar",
    },

    {
        "name": "Water Resistance Level",
        "value": "Water Resistant",
    },

    {
        "name": "Front Photo Sensor Resolution",
        "value": "8 MP",
    },

    {
        "name": "Rear Facing Camera Photo Sensor Resolution",
        "value": "50 MP",
    },

    {
        "name": "Camera Description",
        "value": "Front, Rear",
    },

    {
        "name": "Camera Flash Type",
        "value": "LED",
    },

    {
        "name": "Optical Sensor Resolution",
        "value": "50 MP",
    },

    {
        "name": "Number Of Rear Facing Cameras",
        "value": "2",
    },

    {
        "name": "Number Of Front Cameras",
        "value": "1",
    },

    {
        "name": "Battery Capacity",
        "value": "7000",
    },

    {
        "name": "Battery Charge Time",
        "value": "97 Minutes",
    },

    {
        "name": "Battery",
        "value": "7000",
    },

    {
        "name": "Item Weight Unit Of Measure",
        "value": "208 Grams",
    },

    {
        "name": "Effective Video Resolution",
        "value": "50 MP",
    },

    {
        "name": "Video Capture Resolution",
        "value": "4k",
    },

    {
        "name": "Frame Rate",
        "value": "30 Frames per Second",
    },

    {
        "name": "Screen Size Unit Of Measure",
        "value": "6.72 Inches",
    },

    {
        "name": "Resolution",
        "value": "2400 x 1080",
    },

    {
        "name": "Refresh Rate",
        "value": "144",
    },

    {
        "name": "Display",
        "value": "LCD",
    },

    {
        "name": "Maximum Display Resolution",
        "value": "2400 x 1080 Pixels",
    },

    {
        "name": "Display Pixel Density",
        "value": "392 Pixels Per Inch (PPI)",
    },

    {
        "name": "Cellular",
        "value": "5G",
    },

    {
        "name": "Network Connectivity Technology",
        "value": "Bluetooth, USB, Wi-Fi",
    },

    {
        "name": "Warranty Description",
        "value": "1",
    },

    {
        "name": "Item Type",
        "value": "Smartphone",
    },

    {
        "name": "Battery Average Life",
        "value": "2 Days",
    },

    {
        "name": "Processor",
        "value": "Dimensity 7400 Apex Processor",
    },

    {
        "name": "Camera",
        "value": "50 MP",
    },
]


result = recommend(
    specs,
    "smartphone"
)


print("=" * 80)
print("ONEPLUS NORD CE6 LITE SCORE TEST")
print("=" * 80)

print()

print("Score:", result["score"])
print()

print("RAW RESULT:")
print(result)

print(
    "Recommendation:",
    result["recommendation"]
)

print()

print("Reasons:")

for reason in result["reasons"]:

    print(
        "-",
        reason
    )

print()

print("Summary:")

print(
    result["summary"]
)

print()

print("=" * 80)