import json
import os
import zipfile

PBIX_PATH = r"d:\data\powerbi\Ecommerce_Business_Analytics.pbix"
THEME_PATH = r"d:\data\powerbi\powerbi_theme.json"

print(f"Generating Power BI Project File at: {PBIX_PATH}...")

# Read theme JSON
with open(THEME_PATH, "r", encoding="utf-8") as f:
  theme_content = f.read()

# Layout definition for the 6 pages
report_layout = {
    "id": 0,
    "resourcePackages": [{
        "resourcePackage": {
            "name": "ApexCartDarkTheme",
            "type": 2,
            "items": [{"name": "CustomTheme", "path": "BaseThemes/theme.json"}],
        }
    }],
    "sections": [
        {
            "id": 0,
            "name": "ExecutiveOverview",
            "displayName": "1. Executive Overview",
            "filters": "[]",
            "ordinal": 0,
            "visualContainers": [
                {
                    "x": 20,
                    "y": 20,
                    "z": 1000,
                    "width": 280,
                    "height": 120,
                    "config": (
                        '{"name":"Card1","singleVisual":{"visualType":"card"}}'
                    ),
                },
                {
                    "x": 320,
                    "y": 20,
                    "z": 1000,
                    "width": 280,
                    "height": 120,
                    "config": (
                        '{"name":"Card2","singleVisual":{"visualType":"card"}}'
                    ),
                },
                {
                    "x": 620,
                    "y": 20,
                    "z": 1000,
                    "width": 280,
                    "height": 120,
                    "config": (
                        '{"name":"Card3","singleVisual":{"visualType":"card"}}'
                    ),
                },
                {
                    "x": 920,
                    "y": 20,
                    "z": 1000,
                    "width": 320,
                    "height": 120,
                    "config": (
                        '{"name":"Card4","singleVisual":{"visualType":"card"}}'
                    ),
                },
                {
                    "x": 20,
                    "y": 160,
                    "z": 1000,
                    "width": 800,
                    "height": 320,
                    "config": (
                        '{"name":"LineChart1","singleVisual":{"visualType":"lineStackedColumnComboChart"}}'
                    ),
                },
                {
                    "x": 840,
                    "y": 160,
                    "z": 1000,
                    "width": 400,
                    "height": 320,
                    "config": (
                        '{"name":"Donut1","singleVisual":{"visualType":"donutChart"}}'
                    ),
                },
                {
                    "x": 20,
                    "y": 500,
                    "z": 1000,
                    "width": 600,
                    "height": 200,
                    "config": (
                        '{"name":"Table1","singleVisual":{"visualType":"tableEx"}}'
                    ),
                },
                {
                    "x": 640,
                    "y": 500,
                    "z": 1000,
                    "width": 600,
                    "height": 200,
                    "config": (
                        '{"name":"Gauge1","singleVisual":{"visualType":"gauge"}}'
                    ),
                },
            ],
        },
        {
            "id": 1,
            "name": "SalesPerformance",
            "displayName": "2. Sales Performance",
            "ordinal": 1,
            "visualContainers": [],
        },
        {
            "id": 2,
            "name": "CustomerAnalytics",
            "displayName": "3. Customer Analytics",
            "ordinal": 2,
            "visualContainers": [],
        },
        {
            "id": 3,
            "name": "ProductAnalytics",
            "displayName": "4. Product & Margin Analytics",
            "ordinal": 3,
            "visualContainers": [],
        },
        {
            "id": 4,
            "name": "InventoryOperations",
            "displayName": "5. Inventory & Operations",
            "ordinal": 4,
            "visualContainers": [],
        },
        {
            "id": 5,
            "name": "ReturnsProfitability",
            "displayName": "6. Returns & Profitability",
            "ordinal": 5,
            "visualContainers": [],
        },
    ],
}

content_types_xml = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="xml" ContentType="application/xml" />
  <Override PartName="/Report/Layout" ContentType="application/json" />
  <Override PartName="/BaseThemes/theme.json" ContentType="application/json" />
  <Override PartName="/Version" ContentType="application/octet-stream" />
</Types>
"""

with zipfile.ZipFile(PBIX_PATH, "w", zipfile.ZIP_DEFLATED) as z:
  z.writestr("[Content_Types].xml", content_types_xml)
  z.writestr("Version", "1.28")
  z.writestr("Report/Layout", json.dumps(report_layout, indent=2))
  z.writestr("BaseThemes/theme.json", theme_content)

print(
    f"Successfully built Power BI file ({os.path.getsize(PBIX_PATH):,} bytes)!"
)
