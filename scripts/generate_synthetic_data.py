import csv
import datetime
import math
import os
import random
from pathlib import Path

# Set random seed for full reproducibility
random.seed(42)

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
CLEANED_DIR = ROOT / "data" / "cleaned"
SOURCE_DIR = ROOT / "data" / "source"
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(CLEANED_DIR, exist_ok=True)
os.makedirs(SOURCE_DIR, exist_ok=True)

print("Starting Enterprise E-Commerce 100k+ Dataset Generation Engine...")

# ==========================================
# 1. CATEGORIES & SUB-CATEGORIES
# ==========================================
categories_data = [
    # Category, Sub-Category, Sub-Cat ID, Base Markup %
    ("Technology", "Laptops & Desktops", "SUB-TECH-01", 0.35),
    ("Technology", "Smartphones & Accessories", "SUB-TECH-02", 0.40),
    ("Technology", "Audio & Headphones", "SUB-TECH-03", 0.45),
    ("Technology", "Monitors & Displays", "SUB-TECH-04", 0.30),
    ("Technology", "Printers & Networking", "SUB-TECH-05", 0.28),
    ("Furniture", "Office Chairs", "SUB-FURN-01", 0.50),
    ("Furniture", "Standing Desks", "SUB-FURN-02", 0.48),
    ("Furniture", "Bookcases & Storage", "SUB-FURN-03", 0.42),
    ("Furniture", "Conference Tables", "SUB-FURN-04", 0.55),
    ("Office Supplies", "Paper & Stationery", "SUB-OFF-01", 0.60),
    ("Office Supplies", "Pens, Inks & Markers", "SUB-OFF-02", 0.65),
    ("Office Supplies", "Storage & Organization", "SUB-OFF-03", 0.50),
    ("Office Supplies", "Desk Accessories", "SUB-OFF-04", 0.58),
    ("Apparel & Gear", "Corporate Apparel", "SUB-APP-01", 0.60),
    ("Apparel & Gear", "Backpacks & Laptop Bags", "SUB-APP-02", 0.52),
]

with open(
    os.path.join(CLEANED_DIR, "dim_category.csv"), "w", newline="", encoding="utf-8"
) as f:
  writer = csv.writer(f)
  writer.writerow(["sub_category_id", "sub_category_name", "category_name"])
  for cat, sub, sub_id, _ in categories_data:
    writer.writerow([sub_id, sub, cat])
print("Created: dim_category.csv (15 sub-categories)")

# ==========================================
# 2. REGIONS
# ==========================================
regions_data = [
    ("REG-NA", "North America", "United States", "Marcus Vance"),
    ("REG-EU", "Europe", "United Kingdom", "Elena Rostova"),
    ("REG-APAC", "Asia-Pacific", "Singapore", "Kenji Takahashi"),
    ("REG-LATAM", "Latin America", "Brazil", "Sofia Mendoza"),
]

with open(
    os.path.join(CLEANED_DIR, "dim_region.csv"), "w", newline="", encoding="utf-8"
) as f:
  writer = csv.writer(f)
  writer.writerow(
      ["region_id", "region_name", "country", "regional_manager"]
  )
  for r in regions_data:
    writer.writerow(r)
print("Created: dim_region.csv (4 global regions)")

# ==========================================
# 3. DATE DIMENSION (2023-01-01 to 2025-12-31)
# ==========================================
start_date = datetime.date(2023, 1, 1)
end_date = datetime.date(2025, 12, 31)
curr = start_date
date_rows = []

while curr <= end_date:
  date_key = int(curr.strftime("%Y%m%d"))
  full_date = curr.strftime("%Y-%m-%d")
  year = curr.year
  quarter = (curr.month - 1) // 3 + 1
  month_num = curr.month
  month_name = curr.strftime("%B")
  week_num = int(curr.strftime("%U")) + 1
  day_num = curr.day
  day_name = curr.strftime("%A")
  is_weekend = 1 if curr.weekday() in [5, 6] else 0
  date_rows.append([
      full_date,
      date_key,
      year,
      f"Q{quarter}",
      month_num,
      month_name,
      week_num,
      day_num,
      day_name,
      is_weekend,
  ])
  curr += datetime.timedelta(days=1)

with open(
    os.path.join(CLEANED_DIR, "dim_date.csv"), "w", newline="", encoding="utf-8"
) as f:
  writer = csv.writer(f)
  writer.writerow([
      "full_date",
      "date_key",
      "year",
      "quarter",
      "month_num",
      "month_name",
      "week_num",
      "day_num",
      "day_name",
      "is_weekend",
  ])
  writer.writerows(date_rows)
print(f"Created: dim_date.csv ({len(date_rows):,} calendar days)")

# ==========================================
# 4. PRODUCTS (500 Realistic SKUs)
# ==========================================
brands = {
    "Technology": [
        "ApexTech",
        "Novacore",
        "QuantumByte",
        "ZenithLogix",
        "AeroSonic",
        "Hyperion",
    ],
    "Furniture": [
        "ErgoComfort",
        "SteelForm",
        "NordicCraft",
        "ModuDesk",
        "Kinetix",
    ],
    "Office Supplies": [
        "OptimaPrint",
        "EverWrite",
        "AccuBinder",
        "EcoPaper",
        "SafeKeep",
    ],
    "Apparel & Gear": [
        "UrbanShield",
        "VanguardPro",
        "AeroWeave",
        "TrekLine",
        "ApexGear",
    ],
}

products_clean = []
products_raw = []

for i in range(1, 501):
  prod_id = f"PRD-{i:04d}"
  sub_cat_tuple = random.choice(categories_data)
  cat_name = sub_cat_tuple[0]
  sub_name = sub_cat_tuple[1]
  sub_id = sub_cat_tuple[2]
  markup = sub_cat_tuple[3]
  brand = random.choice(brands[cat_name])

  # Base costs by category
  if cat_name == "Technology":
    cost_price = round(random.uniform(35.0, 950.0), 2)
  elif cat_name == "Furniture":
    cost_price = round(random.uniform(45.0, 650.0), 2)
  elif cat_name == "Office Supplies":
    cost_price = round(random.uniform(4.50, 45.0), 2)
  else:
    cost_price = round(random.uniform(15.0, 140.0), 2)

  selling_price = round(cost_price * (1 + markup + random.uniform(-0.08, 0.15)), 2)
  if selling_price <= cost_price:
    selling_price = round(cost_price * 1.15, 2)

  reorder_level = random.choice([20, 35, 50, 75, 100, 150])
  prod_name = f"{brand} {sub_name[:-1] if sub_name.endswith('s') else sub_name} Model-{random.randint(100, 999)}"

  products_clean.append([
      prod_id,
      prod_name,
      cat_name,
      sub_name,
      brand,
      cost_price,
      selling_price,
      reorder_level,
  ])

  # Raw version with realistic defects (whitespace, casing, missing brand, negative price anomaly in 1.5% of rows)
  raw_name = prod_name
  raw_cat = cat_name
  raw_brand = brand
  raw_sp = selling_price

  if random.random() < 0.05:
    raw_name = f"  {prod_name}  "
  if random.random() < 0.04:
    raw_cat = cat_name.lower()
  if random.random() < 0.03:
    raw_brand = ""
  if random.random() < 0.015:
    raw_sp = -selling_price  # intentional negative price anomaly

  products_raw.append([
      prod_id,
      raw_name,
      raw_cat,
      sub_name,
      raw_brand,
      cost_price,
      raw_sp,
      reorder_level,
  ])

with open(
    os.path.join(RAW_DIR, "raw_products_with_defects.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
  writer = csv.writer(f)
  writer.writerow([
      "product_id",
      "product_name",
      "category",
      "sub_category",
      "brand",
      "cost_price",
      "selling_price",
      "reorder_level",
  ])
  writer.writerows(products_raw)

print("Created raw_products_with_defects.csv (500 SKUs)")

# ==========================================
# 5. CUSTOMERS (8,000 Unique Customers)
# ==========================================
first_names = [
    "James",
    "Mary",
    "John",
    "Patricia",
    "Robert",
    "Jennifer",
    "Michael",
    "Linda",
    "William",
    "Elizabeth",
    "David",
    "Barbara",
    "Richard",
    "Susan",
    "Joseph",
    "Jessica",
    "Thomas",
    "Sarah",
    "Charles",
    "Karen",
    "Christopher",
    "Nancy",
    "Daniel",
    "Lisa",
    "Matthew",
    "Margaret",
    "Anthony",
    "Betty",
    "Mark",
    "Sandra",
    "Paul",
    "Ashley",
    "Steven",
    "Kimberly",
    "Andrew",
    "Emily",
    "Kenneth",
    "Donna",
    "Joshua",
    "Michelle",
    "Kevin",
    "Carol",
    "Brian",
    "Amanda",
    "George",
    "Melissa",
    "Edward",
    "Deborah",
    "Ronald",
    "Stephanie",
    "Timothy",
    "Rebecca",
    "Jason",
    "Laura",
    "Jeffrey",
    "Sharon",
    "Ryan",
    "Cynthia",
    "Jacob",
    "Kathleen",
    "Gary",
    "Amy",
    "Nicholas",
    "Shirley",
    "Eric",
    "Angela",
    "Jonathan",
    "Helen",
    "Stephen",
    "Anna",
    "Larry",
    "Brenda",
    "Justin",
    "Pamela",
    "Scott",
    "Nicole",
    "Brandon",
    "Emma",
    "Benjamin",
    "Samantha",
    "Samuel",
    "Katherine",
    "Gregory",
    "Christine",
    "Frank",
    "Debra",
    "Alexander",
    "Rachel",
    "Raymond",
    "Catherine",
    "Patrick",
    "Carolyn",
    "Jack",
    "Janet",
    "Dennis",
    "Ruth",
    "Jerry",
    "Maria",
    "Tyler",
    "Heather",
    "Aaron",
    "Diane",
]
last_names = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
    "Lee",
    "Perez",
    "Thompson",
    "White",
    "Harris",
    "Sanchez",
    "Clark",
    "Ramirez",
    "Lewis",
    "Robinson",
    "Walker",
    "Young",
    "Allen",
    "King",
    "Wright",
    "Scott",
    "Torres",
    "Nguyen",
    "Hill",
    "Flores",
    "Green",
    "Adams",
    "Nelson",
    "Baker",
    "Hall",
    "Rivera",
    "Campbell",
    "Mitchell",
    "Carter",
    "Roberts",
    "Gomez",
    "Phillips",
    "Evans",
    "Turner",
    "Diaz",
    "Parker",
    "Cruz",
    "Edwards",
    "Collins",
    "Reyes",
    "Stewart",
    "Morris",
    "Morales",
    "Murphy",
    "Cook",
    "Rogers",
    "Gutierrez",
    "Ortiz",
    "Morgan",
    "Cooper",
    "Peterson",
    "Bailey",
    "Reed",
    "Kelly",
    "Howard",
    "Ramos",
    "Kim",
    "Cox",
    "Ward",
    "Richardson",
    "Watson",
    "Brooks",
    "Chavez",
    "Wood",
    "James",
    "Bennett",
    "Gray",
    "Mendoza",
    "Ruiz",
    "Hughes",
    "Price",
    "Alvarez",
    "Castillo",
    "Sanders",
    "Patel",
    "Myers",
    "Long",
    "Ross",
    "Foster",
    "Jimenez",
]

cities_by_region = {
    "REG-NA": [
        ("New York", "New York"),
        ("Los Angeles", "California"),
        ("Chicago", "Illinois"),
        ("Houston", "Texas"),
        ("Phoenix", "Arizona"),
        ("Seattle", "Washington"),
        ("Atlanta", "Georgia"),
        ("Toronto", "Ontario"),
        ("Boston", "Massachusetts"),
        ("Denver", "Colorado"),
    ],
    "REG-EU": [
        ("London", "Greater London"),
        ("Manchester", "Greater Manchester"),
        ("Berlin", "Berlin"),
        ("Munich", "Bavaria"),
        ("Paris", "Ile-de-France"),
        ("Lyon", "Auvergne-Rhone-Alpes"),
        ("Amsterdam", "North Holland"),
        ("Madrid", "Community of Madrid"),
        ("Dublin", "Leinster"),
        ("Stockholm", "Stockholm County"),
    ],
    "REG-APAC": [
        ("Singapore", "Central"),
        ("Tokyo", "Kanto"),
        ("Osaka", "Kansai"),
        ("Sydney", "New South Wales"),
        ("Melbourne", "Victoria"),
        ("Hong Kong", "Hong Kong"),
        ("Seoul", "Gyeonggi"),
        ("Bangalore", "Karnataka"),
        ("Mumbai", "Maharashtra"),
        ("Auckland", "Auckland Region"),
    ],
    "REG-LATAM": [
        ("Sao Paulo", "Sao Paulo State"),
        ("Rio de Janeiro", "Rio de Janeiro State"),
        ("Mexico City", "CDMX"),
        ("Guadalajara", "Jalisco"),
        ("Bogota", "Cundinamarca"),
        ("Santiago", "Santiago Metro"),
        ("Buenos Aires", "Buenos Aires"),
        ("Lima", "Lima Province"),
        ("Monterrey", "Nuevo Leon"),
        ("Medellin", "Antioquia"),
    ],
}

segments = ["Consumer", "Corporate", "Home Office", "Enterprise"]
segment_weights = [0.48, 0.28, 0.16, 0.08]

customers_clean = []
customers_raw = []

for i in range(1, 8001):
  cust_id = f"CUST-{i:05d}"
  fn = random.choice(first_names)
  ln = random.choice(last_names)
  full_name = f"{fn} {ln}"
  gender = random.choice(["Male", "Female", "Other"])
  age = random.randint(18, 72)
  reg_id = random.choices(
      ["REG-NA", "REG-EU", "REG-APAC", "REG-LATAM"], weights=[0.42, 0.28, 0.20, 0.10]
  )[0]
  city, state = random.choice(cities_by_region[reg_id])
  segment = random.choices(segments, weights=segment_weights)[0]

  # Customer joined between 2021-01-01 and 2025-06-30
  days_offset = random.randint(0, 1600)
  cust_since = datetime.date(2021, 1, 1) + datetime.timedelta(days=days_offset)

  customers_clean.append([
      cust_id,
      full_name,
      gender,
      age,
      city,
      state,
      reg_id,
      segment,
      cust_since.strftime("%Y-%m-%d"),
  ])

  # Raw version with defects (missing age, lowercase segment, duplicate customer rows)
  raw_name = full_name
  raw_age = age
  raw_seg = segment
  raw_gen = gender

  if random.random() < 0.03:
    raw_age = ""  # missing value
  if random.random() < 0.04:
    raw_name = f"  {full_name.lower()}  "  # casing & whitespace
  if random.random() < 0.03:
    raw_seg = segment.upper()
  if random.random() < 0.02:
    raw_gen = "M" if gender == "Male" else "F" if gender == "Female" else "O"

  customers_raw.append([
      cust_id,
      raw_name,
      raw_gen,
      raw_age,
      city,
      state,
      reg_id,
      raw_seg,
      cust_since.strftime("%Y-%m-%d"),
  ])

# Add 80 deliberate duplicate customer rows in raw data
for _ in range(80):
  dup = list(random.choice(customers_raw))
  customers_raw.append(dup)

with open(
    os.path.join(RAW_DIR, "raw_customers_with_defects.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
  writer = csv.writer(f)
  writer.writerow([
      "customer_id",
      "customer_name",
      "gender",
      "age",
      "city",
      "state",
      "region_id",
      "customer_segment",
      "customer_since",
  ])
  writer.writerows(customers_raw)

print(
    f"Created raw_customers_with_defects.csv ({len(customers_raw):,} records)"
)

# ==========================================
# 6. ORDERS & ORDER DETAILS (105,000+ line items)
# ==========================================
sales_channels = ["Direct Web", "Mobile App", "B2B Portal", "Affiliate Partner"]
channel_weights = [0.45, 0.35, 0.12, 0.08]
payment_methods = [
    "Credit Card",
    "PayPal",
    "Apple Pay",
    "Wire Transfer",
    "Debit Card",
]
payment_weights = [0.50, 0.22, 0.14, 0.08, 0.06]
shipping_modes = ["Standard Ground", "Express Air", "Same-Day Priority", "Freight"]
shipping_weights = [0.60, 0.25, 0.10, 0.05]
order_statuses = ["Delivered", "Delivered", "Delivered", "Delivered", "Shipped", "Cancelled"]

NUM_ORDERS = 52000
orders_clean = []
orders_raw = []
order_details_clean = []
order_details_raw = []
returns_clean = []

order_detail_counter = 1
return_counter = 1

return_reasons = [
    "Defective Component",
    "Incorrect Item Delivered",
    "Size / Fit Mismatch",
    "Damaged in Transit",
    "Arrived Late",
    "Buyer Remorse / Changed Mind",
]

print(f"Generating {NUM_ORDERS:,} orders and 100k+ line items...")

for o_idx in range(1, NUM_ORDERS + 1):
  order_id = f"ORD-{o_idx:06d}"
  cust = random.choice(customers_clean)
  cust_id = cust[0]
  cust_reg = cust[6]

  # Order date distribution (2023: 28%, 2024: 34%, 2025: 38% - showing positive growth)
  year_choice = random.choices([2023, 2024, 2025], weights=[0.28, 0.34, 0.38])[0]
  # Seasonality: Q4 (Nov/Dec) has heavier volume
  month_choice = random.choices(
      list(range(1, 13)),
      weights=[0.07, 0.06, 0.08, 0.07, 0.08, 0.08, 0.08, 0.08, 0.09, 0.09, 0.14, 0.15],
  )[0]
  max_day = 28 if month_choice == 2 else 30 if month_choice in [4, 6, 9, 11] else 31
  day_choice = random.randint(1, max_day)
  o_date = datetime.date(year_choice, month_choice, day_choice)
  order_date_str = o_date.strftime("%Y-%m-%d")

  sales_channel = random.choices(sales_channels, weights=channel_weights)[0]
  payment_method = random.choices(payment_methods, weights=payment_weights)[0]
  shipping_mode = random.choices(shipping_modes, weights=shipping_weights)[0]
  order_status = random.choice(order_statuses)

  orders_clean.append([
      order_id,
      order_date_str,
      cust_id,
      cust_reg,
      sales_channel,
      payment_method,
      shipping_mode,
      order_status,
  ])

  # Raw order with defects (date format variations, missing customer id, uppercase)
  raw_date = order_date_str
  raw_cust_id = cust_id
  raw_status = order_status

  if random.random() < 0.04:
    raw_date = o_date.strftime("%m/%d/%Y")  # US format
  elif random.random() < 0.02:
    raw_date = o_date.strftime("%d-%m-%Y")  # Hyphen format

  if random.random() < 0.015:
    raw_cust_id = ""  # missing foreign key

  if random.random() < 0.03:
    raw_status = order_status.lower()

  orders_raw.append([
      order_id,
      raw_date,
      raw_cust_id,
      cust_reg,
      sales_channel,
      payment_method,
      shipping_mode,
      raw_status,
  ])

  # 1 to 5 items per order (average ~2.2 items -> ~105k+ line items total)
  num_items = random.choices([1, 2, 3, 4, 5], weights=[0.42, 0.30, 0.15, 0.08, 0.05])[0]

  for _ in range(num_items):
    prod = random.choice(products_clean)
    prod_id = prod[0]
    prod_cost = prod[5]
    prod_sp = prod[6]

    qty = random.choices([1, 2, 3, 4, 5, 8, 10], weights=[0.60, 0.22, 0.09, 0.04, 0.03, 0.01, 0.01])[0]

    # Discounts: 0%, 5%, 10%, 15%, 20%, 25%, 30%
    discount_rate = random.choices(
        [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
        weights=[0.38, 0.22, 0.18, 0.10, 0.06, 0.04, 0.02],
    )[0]

    gross_sales = round(qty * prod_sp, 2)
    discount_amount = round(gross_sales * discount_rate, 2)
    net_sales = round(gross_sales - discount_amount, 2)
    total_cost = round(qty * prod_cost, 2)
    net_profit = round(net_sales - total_cost, 2)

    detail_id = f"DTL-{order_detail_counter:07d}"
    order_detail_counter += 1

    order_details_clean.append([
        detail_id,
        order_id,
        prod_id,
        qty,
        prod_sp,
        discount_rate,
        gross_sales,
        discount_amount,
        net_sales,
        total_cost,
        net_profit,
    ])

    # Raw order details with defects (negative quantity anomaly, string percentage, missing detail ID)
    raw_qty = qty
    raw_disc = discount_rate
    raw_sales = gross_sales

    if random.random() < 0.008:
      raw_qty = -qty  # negative quantity anomaly
    if random.random() < 0.03:
      raw_disc = f"{int(discount_rate * 100)}%"  # text percentage
    if random.random() < 0.005:
      raw_sales = 0.00

    order_details_raw.append([
        detail_id,
        order_id,
        prod_id,
        raw_qty,
        prod_sp,
        raw_disc,
        raw_sales,
        discount_amount,
        net_sales,
        total_cost,
        net_profit,
    ])

    # Returns generation (approx 4.2% return rate for delivered orders)
    if order_status == "Delivered" and random.random() < 0.042:
      return_id = f"RET-{return_counter:06d}"
      return_counter += 1
      ret_days_after = random.randint(2, 28)
      ret_date = o_date + datetime.timedelta(days=ret_days_after)
      ret_reason = random.choice(return_reasons)
      ret_qty = random.randint(1, qty)
      refund_amount = round(ret_qty * prod_sp * (1 - discount_rate), 2)

      returns_clean.append([
          return_id,
          order_id,
          detail_id,
          prod_id,
          ret_date.strftime("%Y-%m-%d"),
          ret_reason,
          ret_qty,
          refund_amount,
      ])

# Add duplicate order rows to raw orders
for _ in range(150):
  dup_order = list(random.choice(orders_raw))
  orders_raw.append(dup_order)

# Save Orders
with open(
    os.path.join(RAW_DIR, "raw_orders_with_defects.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
  writer = csv.writer(f)
  writer.writerow([
      "order_id",
      "order_date",
      "customer_id",
      "region_id",
      "sales_channel",
      "payment_method",
      "shipping_mode",
      "order_status",
  ])
  writer.writerows(orders_raw)

with open(
    os.path.join(RAW_DIR, "raw_order_details_with_defects.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
  writer = csv.writer(f)
  writer.writerow([
      "order_detail_id",
      "order_id",
      "product_id",
      "quantity",
      "unit_price",
      "discount_rate",
      "gross_sales",
      "discount_amount",
      "net_sales",
      "total_cost",
      "net_profit",
  ])
  writer.writerows(order_details_raw)

# Save Returns
with open(
    os.path.join(SOURCE_DIR, "fact_returns_generated.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
  writer = csv.writer(f)
  writer.writerow([
      "return_id",
      "order_id",
      "order_detail_id",
      "product_id",
      "return_date",
      "return_reason",
      "return_quantity",
      "refund_amount",
  ])
  writer.writerows(returns_clean)

print(
    f"Created: fact_orders.csv ({len(orders_clean):,} orders) &"
    f" fact_order_details.csv ({len(order_details_clean):,} line items)"
)
print(
    "Created generated return source: "
    f"{len(returns_clean):,} returned records"
)

# ==========================================
# 7. INVENTORY (Monthly Snapshots per Product)
# ==========================================
inventory_rows = []
inv_id_counter = 1

# 36 months (2023-01 to 2025-12)
for yr in [2023, 2024, 2025]:
  for mo in range(1, 13):
    snap_date = datetime.date(yr, mo, 1)
    for prod in products_clean:
      p_id = prod[0]
      reorder_lvl = prod[7]
      open_stock = random.randint(40, 450)
      received = random.choice([0, 50, 100, 150, 200, 300])
      sold = random.randint(15, min(open_stock + received, 220))
      close_stock = open_stock + received - sold

      stock_status = (
          "Critical Low"
          if close_stock <= reorder_lvl
          else (
              "Optimal"
              if close_stock <= reorder_lvl * 3
              else "Overstocked"
          )
      )

      inventory_rows.append([
          f"INV-{inv_id_counter:06d}",
          p_id,
          snap_date.strftime("%Y-%m-%d"),
          open_stock,
          received,
          sold,
          close_stock,
          stock_status,
      ])
      inv_id_counter += 1

with open(
    os.path.join(CLEANED_DIR, "fact_inventory.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
  writer = csv.writer(f)
  writer.writerow([
      "inventory_id",
      "product_id",
      "snapshot_date",
      "opening_stock",
      "units_received",
      "units_sold",
      "closing_stock",
      "stock_status",
  ])
  writer.writerows(inventory_rows)
print(f"Created: fact_inventory.csv ({len(inventory_rows):,} monthly inventory snapshots)")

# ==========================================
# 8. SALES TARGETS (Monthly per Region & Category)
# ==========================================
targets_rows = []
tgt_counter = 1
categories_unique = ["Technology", "Furniture", "Office Supplies", "Apparel & Gear"]

for yr in [2023, 2024, 2025]:
  for mo in range(1, 13):
    ym_str = f"{yr}-{mo:02d}"
    for reg in regions_data:
      reg_id = reg[0]
      for cat in categories_unique:
        # Base targets scaled by region and category
        if cat == "Technology":
          base_target = 85000 * (1 + (yr - 2023) * 0.15)
        elif cat == "Furniture":
          base_target = 65000 * (1 + (yr - 2023) * 0.12)
        elif cat == "Office Supplies":
          base_target = 35000 * (1 + (yr - 2023) * 0.10)
        else:
          base_target = 45000 * (1 + (yr - 2023) * 0.18)

        # Region multiplier
        if reg_id == "REG-NA":
          multiplier = 1.4
        elif reg_id == "REG-EU":
          multiplier = 1.0
        elif reg_id == "REG-APAC":
          multiplier = 0.8
        else:
          multiplier = 0.5

        sales_target = round(base_target * multiplier * random.uniform(0.92, 1.08), 2)
        profit_target = round(sales_target * random.uniform(0.20, 0.28), 2)
        order_target = int(sales_target / random.uniform(180, 260))

        targets_rows.append([
            f"TGT-{tgt_counter:05d}",
            ym_str,
            reg_id,
            cat,
            sales_target,
            profit_target,
            order_target,
        ])
        tgt_counter += 1

with open(
    os.path.join(CLEANED_DIR, "fact_sales_targets.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
  writer = csv.writer(f)
  writer.writerow([
      "target_id",
      "year_month",
      "region_id",
      "category_name",
      "sales_target",
      "profit_target",
      "order_target",
  ])
  writer.writerows(targets_rows)
print(f"Created: fact_sales_targets.csv ({len(targets_rows):,} regional targets)")

print("\nAll 10 Relational & Raw Datasets Successfully Generated!")
