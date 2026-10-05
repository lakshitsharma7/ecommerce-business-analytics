import csv
import sqlite3
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
CLEANED_DIR = ROOT / "data" / "cleaned"
DB_PATH = ROOT / "data" / "ecommerce_analytics.db"
OUTPUT_PATH = ROOT / "excel" / "Ecommerce_Analytics.xlsx"


def load_warehouse_snapshot() -> dict:
  if not DB_PATH.is_file():
    raise FileNotFoundError(
        f"Warehouse not found at {DB_PATH}; run scripts/load_sql_database.py."
    )

  with sqlite3.connect(DB_PATH) as connection:
    connection.row_factory = sqlite3.Row

    def rows(query):
      return [dict(row) for row in connection.execute(query)]

    financial = rows(
        """
        SELECT
            ROUND(SUM(gross_sales), 2) AS gross_sales,
            ROUND(SUM(discount_amount), 2) AS discounts,
            ROUND(SUM(net_sales), 2) AS net_sales,
            ROUND(SUM(total_cost), 2) AS cogs,
            ROUND(SUM(net_profit), 2) AS line_profit,
            COUNT(DISTINCT order_id) AS orders,
            COUNT(*) AS order_lines,
            SUM(quantity) AS units
        FROM fact_order_details
        """
    )[0]
    customer = rows(
        """
        WITH order_counts AS (
            SELECT customer_id, COUNT(DISTINCT order_id) AS order_count
            FROM fact_orders
            GROUP BY customer_id
        )
        SELECT
            COUNT(*) AS customers_with_orders,
            SUM(order_count >= 2) AS repeat_customers,
            SUM(order_count = 1) AS one_time_customers
        FROM order_counts
        """
    )[0]
    returns = rows(
        """
        SELECT
            COUNT(DISTINCT return_id) AS incidents,
            SUM(return_quantity) AS units,
            ROUND(SUM(refund_amount), 2) AS refunds
        FROM fact_returns
        """
    )[0]
    targets = rows(
        "SELECT ROUND(SUM(sales_target), 2) AS sales_target "
        "FROM fact_sales_targets"
    )[0]
    inventory = rows(
        """
        SELECT
            i.snapshot_date,
            SUM(i.closing_stock) AS closing_units,
            ROUND(SUM(i.closing_stock * p.cost_price), 2) AS inventory_value
        FROM fact_inventory AS i
        JOIN dim_product AS p USING (product_id)
        WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM fact_inventory)
        GROUP BY i.snapshot_date
        """
    )[0]
    inventory["below_reorder"] = connection.execute(
        """
        SELECT COUNT(DISTINCT i.product_id)
        FROM fact_inventory AS i
        JOIN dim_product AS p USING (product_id)
        WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM fact_inventory)
          AND i.closing_stock <= p.reorder_level
        """
    ).fetchone()[0]
    return {
        "counts": {
            row["name"]: row["row_count"]
            for row in rows(
                """
                SELECT name, (SELECT COUNT(*) FROM dim_customer) AS row_count
                FROM sqlite_master WHERE type = 'table' AND name = 'dim_customer'
                UNION ALL SELECT 'dim_category', COUNT(*) FROM dim_category
                UNION ALL SELECT 'dim_date', COUNT(*) FROM dim_date
                UNION ALL SELECT 'dim_product', COUNT(*) FROM dim_product
                UNION ALL SELECT 'dim_region', COUNT(*) FROM dim_region
                UNION ALL SELECT 'fact_inventory', COUNT(*) FROM fact_inventory
                UNION ALL SELECT 'fact_order_details', COUNT(*) FROM fact_order_details
                UNION ALL SELECT 'fact_orders', COUNT(*) FROM fact_orders
                UNION ALL SELECT 'fact_returns', COUNT(*) FROM fact_returns
                UNION ALL SELECT 'fact_sales_targets', COUNT(*) FROM fact_sales_targets
                """
            )
        },
        "date_range": rows(
            "SELECT MIN(order_date) AS start, MAX(order_date) AS end "
            "FROM fact_orders"
        )[0],
        "financial": financial,
        "customers": customer,
        "returns": returns,
        "targets": targets,
        "inventory": inventory,
        "categories": rows(
            """
            SELECT p.category AS name, ROUND(SUM(d.net_sales), 2) AS net_sales,
                   ROUND(SUM(d.net_profit), 2) AS line_profit,
                   100.0 * SUM(d.net_profit) / NULLIF(SUM(d.net_sales), 0)
                       AS margin_pct
            FROM fact_order_details AS d
            JOIN dim_product AS p USING (product_id)
            GROUP BY p.category ORDER BY net_sales DESC
            """
        ),
        "regions": rows(
            """
            SELECT r.region_name AS name, ROUND(SUM(d.net_sales), 2) AS net_sales,
                   100.0 * SUM(d.net_profit) / NULLIF(SUM(d.net_sales), 0)
                       AS margin_pct
            FROM fact_order_details AS d
            JOIN fact_orders AS o USING (order_id)
            JOIN dim_region AS r USING (region_id)
            GROUP BY r.region_name ORDER BY net_sales DESC
            """
        ),
        "discounts": rows(
            """
            SELECT
                CASE
                    WHEN discount_rate = 0 THEN '0%'
                    WHEN discount_rate <= 0.10 THEN '>0%-10%'
                    WHEN discount_rate <= 0.20 THEN '>10%-20%'
                    ELSE '>20%'
                END AS tier,
                COUNT(*) AS lines,
                100.0 * SUM(net_profit) / NULLIF(SUM(net_sales), 0) AS margin_pct
            FROM fact_order_details
            GROUP BY tier
            ORDER BY MIN(discount_rate)
            """
        ),
        "return_reasons": rows(
            """
            SELECT return_reason AS reason, COUNT(DISTINCT return_id) AS incidents,
                   ROUND(SUM(refund_amount), 2) AS refunds
            FROM fact_returns
            GROUP BY return_reason ORDER BY incidents DESC
            """
        ),
    }


print("Building the Excel workbook from the current project data...")
warehouse = load_warehouse_snapshot()
wb = openpyxl.Workbook()
# Remove default sheet
wb.remove(wb.active)

# Color Palette: Modern Executive Slate & Indigo
NAVY_HEADER_FILL = PatternFill(
    start_color="1E293B", end_color="1E293B", fill_type="solid"
)
BLUE_ACCENT_FILL = PatternFill(
    start_color="2563EB", end_color="2563EB", fill_type="solid"
)
LIGHT_BLUE_FILL = PatternFill(
    start_color="EFF6FF", end_color="EFF6FF", fill_type="solid"
)
LIGHT_GREEN_FILL = PatternFill(
    start_color="ECFDF5", end_color="ECFDF5", fill_type="solid"
)
LIGHT_RED_FILL = PatternFill(
    start_color="FEF2F2", end_color="FEF2F2", fill_type="solid"
)
LIGHT_AMBER_FILL = PatternFill(
    start_color="FFFBEB", end_color="FFFBEB", fill_type="solid"
)
CARD_BG_FILL = PatternFill(
    start_color="F8FAFC", end_color="F8FAFC", fill_type="solid"
)

HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
TITLE_FONT = Font(name="Calibri", size=16, bold=True, color="1E293B")
SUBTITLE_FONT = Font(name="Calibri", size=10, italic=True, color="64748B")
SECTION_FONT = Font(name="Calibri", size=12, bold=True, color="1E293B")
BOLD_FONT = Font(name="Calibri", size=11, bold=True, color="1E293B")
DATA_FONT = Font(name="Calibri", size=10, color="0F172A")
KPI_VAL_FONT = Font(name="Calibri", size=18, bold=True, color="1E293B")
KPI_LABEL_FONT = Font(name="Calibri", size=9, bold=True, color="64748B")

THIN_BORDER = Border(
    left=Side(style="thin", color="E2E8F0"),
    right=Side(style="thin", color="E2E8F0"),
    top=Side(style="thin", color="E2E8F0"),
    bottom=Side(style="thin", color="E2E8F0"),
)
DOUBLE_BOTTOM_BORDER = Border(
    left=Side(style="thin", color="E2E8F0"),
    right=Side(style="thin", color="E2E8F0"),
    top=Side(style="thin", color="E2E8F0"),
    bottom=Side(style="double", color="1E293B"),
)


def style_header_row(ws, row_idx, num_cols):
  ws.row_dimensions[row_idx].height = 26
  for col_idx in range(1, num_cols + 1):
    cell = ws.cell(row=row_idx, column=col_idx)
    cell.fill = NAVY_HEADER_FILL
    cell.font = HEADER_FONT
    cell.alignment = Alignment(
        horizontal="center", vertical="center", wrap_text=True
    )
    cell.border = THIN_BORDER


def autofit_columns(ws, max_cols=20):
  for col in range(1, max_cols + 1):
    col_letter = get_column_letter(col)
    max_len = 0
    for row in range(1, min(ws.max_row + 1, 100)):
      val = ws.cell(row=row, column=col).value
      if val is not None:
        lines = str(val).split("\n")
        max_len = max(max_len, max(len(l) for l in lines))
    ws.column_dimensions[col_letter].width = max(max_len + 4, 12)


ws0 = wb.create_sheet(title="00_Read_Me")
ws0["A1"] = "APEXCART RETAIL INC. — ANALYTICS WORKBOOK"
ws0["A1"].font = TITLE_FONT
ws0["A2"] = "Synthetic portfolio data. Read the scope notes before interpreting sample worksheets."
ws0["A2"].font = SUBTITLE_FONT
ws0["A4"] = "Worksheet"
ws0["B4"] = "Scope and interpretation"
style_header_row(ws0, 4, 2)
workbook_notes = [
    ("01_Raw_Data", "A sample of up to 1,500 raw order-detail rows joined to their raw order/customer fields."),
    ("02_Data_Cleaning", "Formula demonstrations over 500 sample rows; this is not the production cleaning pipeline."),
    ("03_Customers", "The first 1,000 cleaned customer records."),
    ("04_Products", "The cleaned 500-product catalog."),
    ("05_Orders", "The first 2,000 cleaned order-detail rows with workbook formulas."),
    ("06_Pivot_Analysis", "Formula analysis of the sample in 05_Orders, not full-warehouse totals."),
    ("07_KPI_Summary", "Formula examples only; official targets are not assumed."),
    ("08_Business_Insights", "Current full-warehouse findings, computed from the SQLite database."),
    ("09_Warehouse_KPIs", "Static SQL-calculated totals and record counts for the full current warehouse."),
]
for row, (sheet, note) in enumerate(workbook_notes, 5):
  ws0.cell(row, 1, sheet).font = BOLD_FONT
  ws0.cell(row, 2, note).font = DATA_FONT
  ws0.cell(row, 1).border = THIN_BORDER
  ws0.cell(row, 2).border = THIN_BORDER
  ws0.cell(row, 2).alignment = Alignment(wrap_text=True, vertical="top")
ws0.column_dimensions["A"].width = 30
ws0.column_dimensions["B"].width = 110
ws0["A16"] = "Cleaning pipeline"
ws0["A16"].font = BOLD_FONT
ws0["B16"] = (
    "scripts/clean_raw_datasets.py is the reproducible raw-to-clean pipeline. "
    "Unlike the illustrative formulas above, it rejects orders with missing "
    "customer keys and records transformations in data/cleaned/cleaning_audit.json."
)
ws0["B16"].font = DATA_FONT
ws0["B16"].alignment = Alignment(wrap_text=True, vertical="top")
ws0["A18"] = "Financial scope"
ws0["A18"].font = BOLD_FONT
ws0["B18"] = (
    "SQL line-item sales and profit include all stored order statuses, including "
    "cancelled orders. Refund-adjusted profit subtracts recorded refunds only; "
    "it is not operating profit or EBITDA. Formula cells are calculated by Excel "
    "when the workbook is opened."
)
ws0["B18"].font = DATA_FONT
ws0["B18"].alignment = Alignment(wrap_text=True, vertical="top")


# ==========================================
# SHEET 1: 01_Raw_Data
# ==========================================
print("Creating Sheet 01_Raw_Data...")
ws1 = wb.create_sheet(title="01_Raw_Data")
ws1.views.sheetView[0].showGridLines = True

ws1["A1"] = "APEXCART RETAIL INC. — RAW TRANSACTION INGESTION FEED"
ws1["A1"].font = TITLE_FONT
ws1["A2"] = (
    "Uncleaned source transactions containing real-world anomalies: date"
    " format variances, whitespace, negative quantities, text discount %, and"
    " missing keys."
)
ws1["A2"].font = SUBTITLE_FONT

raw_headers = [
    "Order_ID",
    "Order_Date_Raw",
    "Customer_ID_Raw",
    "Customer_Name_Raw",
    "Product_ID",
    "Quantity_Raw",
    "Unit_Price",
    "Discount_Raw",
    "Shipping_Mode_Raw",
    "Sales_Channel",
    "Region_Raw",
]
for c_idx, h in enumerate(raw_headers, 1):
  ws1.cell(row=4, column=c_idx, value=h)
style_header_row(ws1, 4, len(raw_headers))

# Read a representative sample of raw records for workbook demonstration.
raw_orders_path = RAW_DIR / "raw_orders_with_defects.csv"
raw_details_path = RAW_DIR / "raw_order_details_with_defects.csv"
raw_cust_path = RAW_DIR / "raw_customers_with_defects.csv"

# Load customer map
cust_map = {}
with open(raw_cust_path, "r", encoding="utf-8", errors="ignore") as f:
  reader = csv.reader(f)
  next(reader)
  for row in reader:
    if row and row[0]:
      cust_map[row[0]] = (row[1], row[6])  # name, region

orders_map = {}
with open(raw_orders_path, "r", encoding="utf-8", errors="ignore") as f:
  reader = csv.reader(f)
  next(reader)
  for row in reader:
    if row and row[0]:
      orders_map[row[0]] = (
          row[1],
          row[2],
          row[4],
          row[6],
      )  # date, cust_id, channel, ship_mode

row_curr = 5
with open(raw_details_path, "r", encoding="utf-8", errors="ignore") as f:
  reader = csv.reader(f)
  next(reader)
  for idx, row in enumerate(reader):
    if idx >= 1500:
      break
    dtl_id, ord_id, prod_id, qty, up, disc, gsales, damt, nsales, tcost, nprof = (
        row
    )
    ord_info = orders_map.get(
        ord_id, ("2024-01-15", "CUST-00100", "Direct Web", "Standard Ground")
    )
    cust_info = cust_map.get(
        ord_info[1], ("  John Doe  ", "REG-NA") if ord_info[1] else ("", "")
    )

    ws1.append([
        ord_id,
        ord_info[0],
        ord_info[1],
        cust_info[0],
        prod_id,
        qty,
        float(up),
        disc,
        ord_info[3],
        ord_info[2],
        cust_info[1],
    ])

    for col_i in range(1, len(raw_headers) + 1):
      c = ws1.cell(row=row_curr, column=col_i)
      c.font = DATA_FONT
      c.border = THIN_BORDER
      if col_i == 7:
        c.number_format = "$#,##0.00"
    row_curr += 1

autofit_columns(ws1, len(raw_headers))

# ==========================================
# SHEET 2: 02_Data_Cleaning
# ==========================================
print("Creating Sheet 02_Data_Cleaning...")
ws2 = wb.create_sheet(title="02_Data_Cleaning")
ws2.views.sheetView[0].showGridLines = True

ws2["A1"] = "DATA AUDIT & CLEANSING TRANSFORMATION LAYER"
ws2["A1"].font = TITLE_FONT
ws2["A2"] = (
    "Illustrative formulas over sample rows; production cleaning is performed"
    " by scripts/clean_raw_datasets.py."
)
ws2["A2"].font = SUBTITLE_FONT
ws2["A3"] = (
    "Some demonstration formulas differ from production policy: missing "
    "customer keys are rejected by the Python pipeline, not imputed."
)
ws2["A3"].font = SUBTITLE_FONT

clean_headers = [
    "Order_ID",
    "Clean_Date",
    "Clean_Customer_ID",
    "Clean_Customer_Name",
    "Clean_Quantity",
    "Clean_Unit_Price",
    "Clean_Discount_Rate",
    "Clean_Sales_Channel",
    "Clean_Region",
    "Data_Quality_Flag",
    "Audit_Action_Taken",
]
for c_idx, h in enumerate(clean_headers, 1):
  ws2.cell(row=4, column=c_idx, value=h)
style_header_row(ws2, 4, len(clean_headers))

for r in range(5, 505):  # 500 audit rows demonstrated with live Excel formulas
  r_src = r
  # Live Excel formulas demonstrating transformation
  ws2.cell(row=r, column=1, value=f"='01_Raw_Data'!A{r_src}")
  ws2.cell(
      row=r,
      column=2,
      value=(
          f"=IFERROR(DATEVALUE('01_Raw_Data'!B{r_src}),"
          f" IF('01_Raw_Data'!B{r_src}=\"\", DATE(2024,1,1),"
          f" '01_Raw_Data'!B{r_src}))"
      ),
  )
  ws2.cell(
      row=r,
      column=3,
      value=(
          f"=IF(OR('01_Raw_Data'!C{r_src}=\"\",'01_Raw_Data'!C{r_src}=\"0\"),"
          f' "CUST-GUEST", TRIM(\'01_Raw_Data\'!C{r_src}))'
      ),
  )
  ws2.cell(
      row=r,
      column=4,
      value=f"=PROPER(TRIM(CLEAN('01_Raw_Data'!D{r_src})))",
  )
  ws2.cell(
      row=r,
      column=5,
      value=(
          f"=ABS(IF(ISNUMBER(VALUE('01_Raw_Data'!F{r_src})),"
          f" VALUE('01_Raw_Data'!F{r_src}), 1))"
      ),
  )
  ws2.cell(row=r, column=6, value=f"='01_Raw_Data'!G{r_src}")
  ws2.cell(
      row=r,
      column=7,
      value=(
          f"=IF(ISNUMBER('01_Raw_Data'!H{r_src}), '01_Raw_Data'!H{r_src},"
          f" IFERROR(VALUE(SUBSTITUTE('01_Raw_Data'!H{r_src}, \"%\", \"\"))/100,"
          " 0))"
      ),
  )
  ws2.cell(
      row=r,
      column=8,
      value=f"=PROPER(TRIM('01_Raw_Data'!J{r_src}))",
  )
  ws2.cell(
      row=r,
      column=9,
      value=(
          f"=IF('01_Raw_Data'!K{r_src}=\"\", \"REG-NA\","
          f" UPPER(TRIM('01_Raw_Data'!K{r_src})))"
      ),
  )
  ws2.cell(
      row=r,
      column=10,
      value=(
          f'=IF(OR(\'01_Raw_Data\'!C{r_src}="", \'01_Raw_Data\'!F{r_src}<0,'
          f' ISNUMBER(SEARCH("%", \'01_Raw_Data\'!H{r_src}))), "FIXED ANOMALY",'
          ' "PASSED")'
      ),
  )
  ws2.cell(
      row=r,
      column=11,
      value=(
          f'=IF(\'01_Raw_Data\'!F{r_src}<0, "Converted Negative Quantity to'
          f' ABS", IF(\'01_Raw_Data\'!C{r_src}="", "Imputed Missing Customer'
          ' ID", IF(ISNUMBER(SEARCH("%",'
          f' \'01_Raw_Data\'!H{r_src})), "Parsed Text % to Numeric Rate",'
          ' "Standardized Format")))'
      ),
  )

  for col_i in range(1, len(clean_headers) + 1):
    c = ws2.cell(row=r, column=col_i)
    c.font = DATA_FONT
    c.border = THIN_BORDER
    if col_i == 2:
      c.number_format = "yyyy-mm-dd"
    elif col_i == 6:
      c.number_format = "$#,##0.00"
    elif col_i == 7:
      c.number_format = "0.0%"

autofit_columns(ws2, len(clean_headers))

# ==========================================
# SHEET 3: 03_Customers
# ==========================================
print("Creating Sheet 03_Customers...")
ws3 = wb.create_sheet(title="03_Customers")
ws3.views.sheetView[0].showGridLines = True

ws3["A1"] = "CUSTOMER MASTER & SEGMENTATION PROFILE"
ws3["A1"].font = TITLE_FONT
ws3["A2"] = (
    "Demographic segmentation using IFS/LOOKUP formulas and order aggregation"
    " metrics."
)
ws3["A2"].font = SUBTITLE_FONT

cust_headers = [
    "Customer_ID",
    "Customer_Name",
    "Gender",
    "Age",
    "Age_Group",
    "City",
    "State",
    "Region_ID",
    "Customer_Segment",
    "Customer_Since",
    "Total_Orders",
    "Total_Spend",
    "Customer_Tier",
]
for c_idx, h in enumerate(cust_headers, 1):
  ws3.cell(row=4, column=c_idx, value=h)
style_header_row(ws3, 4, len(cust_headers))

clean_cust_path = CLEANED_DIR / "dim_customer.csv"
with open(clean_cust_path, "r", encoding="utf-8") as f:
  reader = csv.reader(f)
  next(reader)
  for idx, row in enumerate(reader):
    if idx >= 1000:
      break
    r_idx = idx + 5
    cid, cname, gen, age, city, state, reg, seg, csince = row
    ws3.cell(row=r_idx, column=1, value=cid)
    ws3.cell(row=r_idx, column=2, value=cname)
    ws3.cell(row=r_idx, column=3, value=gen)
    ws3.cell(row=r_idx, column=4, value=int(age))
    ws3.cell(
        row=r_idx,
        column=5,
        value=(
            f'=IF(D{r_idx}<25, "18-24", IF(D{r_idx}<35, "25-34",'
            f' IF(D{r_idx}<50, "35-49", "50+")))'
        ),
    )
    ws3.cell(row=r_idx, column=6, value=city)
    ws3.cell(row=r_idx, column=7, value=state)
    ws3.cell(row=r_idx, column=8, value=reg)
    ws3.cell(row=r_idx, column=9, value=seg)
    ws3.cell(row=r_idx, column=10, value=csince)
    ws3.cell(
        row=r_idx,
        column=11,
        value=f"=COUNTIFS('05_Orders'!$C:$C, A{r_idx})",
    )
    ws3.cell(
        row=r_idx,
        column=12,
        value=f"=SUMIFS('05_Orders'!$I:$I, '05_Orders'!$C:$C, A{r_idx})",
    )
    ws3.cell(
        row=r_idx,
        column=13,
        value=(
            f'=IF(L{r_idx}>=2000, "Platinum VIP", IF(L{r_idx}>=1000, "Gold",'
            f' IF(L{r_idx}>=500, "Silver", "Standard")))'
        ),
    )

    for col_i in range(1, len(cust_headers) + 1):
      c = ws3.cell(row=r_idx, column=col_i)
      c.font = DATA_FONT
      c.border = THIN_BORDER
      if col_i == 12:
        c.number_format = "$#,##0.00"

autofit_columns(ws3, len(cust_headers))

# ==========================================
# SHEET 4: 04_Products
# ==========================================
print("Creating Sheet 04_Products...")
ws4 = wb.create_sheet(title="04_Products")
ws4.views.sheetView[0].showGridLines = True

ws4["A1"] = "PRODUCT CATALOG & MARGIN MATRIX"
ws4["A1"].font = TITLE_FONT
ws4["A2"] = (
    "SKU pricing tiers, base cost, list selling price, gross margin %, and"
    " reorder alert flags."
)
ws4["A2"].font = SUBTITLE_FONT

prod_headers = [
    "Product_ID",
    "Product_Name",
    "Category",
    "Sub_Category",
    "Brand",
    "Cost_Price",
    "Selling_Price",
    "Markup_Amount",
    "Gross_Margin_Pct",
    "Price_Tier",
    "Reorder_Level",
]
for c_idx, h in enumerate(prod_headers, 1):
  ws4.cell(row=4, column=c_idx, value=h)
style_header_row(ws4, 4, len(prod_headers))

clean_prod_path = CLEANED_DIR / "dim_product.csv"
with open(clean_prod_path, "r", encoding="utf-8") as f:
  reader = csv.reader(f)
  next(reader)
  for idx, row in enumerate(reader):
    r_idx = idx + 5
    pid, pname, cat, subcat, brand, cp, sp, reorder = row
    ws4.cell(row=r_idx, column=1, value=pid)
    ws4.cell(row=r_idx, column=2, value=pname)
    ws4.cell(row=r_idx, column=3, value=cat)
    ws4.cell(row=r_idx, column=4, value=subcat)
    ws4.cell(row=r_idx, column=5, value=brand)
    ws4.cell(row=r_idx, column=6, value=float(cp))
    ws4.cell(row=r_idx, column=7, value=float(sp))
    ws4.cell(row=r_idx, column=8, value=f"=G{r_idx}-F{r_idx}")
    ws4.cell(row=r_idx, column=9, value=f"=IFERROR(H{r_idx}/G{r_idx}, 0)")
    ws4.cell(
        row=r_idx,
        column=10,
        value=(
            f'=IF(G{r_idx}>=400, "High-End", IF(G{r_idx}>=100, "Mid-Tier",'
            ' "Economy"))'
        ),
    )
    ws4.cell(row=r_idx, column=11, value=int(reorder))

    for col_i in range(1, len(prod_headers) + 1):
      c = ws4.cell(row=r_idx, column=col_i)
      c.font = DATA_FONT
      c.border = THIN_BORDER
      if col_i in [6, 7, 8]:
        c.number_format = "$#,##0.00"
      elif col_i == 9:
        c.number_format = "0.0%"

autofit_columns(ws4, len(prod_headers))

# ==========================================
# SHEET 5: 05_Orders
# ==========================================
print("Creating Sheet 05_Orders...")
ws5 = wb.create_sheet(title="05_Orders")
ws5.views.sheetView[0].showGridLines = True

ws5["A1"] = "ANALYTICAL ORDERS BASE TABLE"
ws5["A1"].font = TITLE_FONT
ws5["A2"] = (
    "Normalized transactional table with dynamic XLOOKUP, line revenue, cost,"
    " profit, and margin formulas."
)
ws5["A2"].font = SUBTITLE_FONT

order_headers = [
    "Order_Detail_ID",
    "Order_ID",
    "Order_Date",
    "Customer_ID",
    "Product_ID",
    "Quantity",
    "Unit_Price",
    "Unit_Cost",
    "Gross_Sales",
    "Discount_Rate",
    "Discount_Amount",
    "Net_Sales",
    "Total_Cost",
    "Net_Profit",
    "Profit_Margin_Pct",
    "Order_Year",
    "Order_Month",
    "Sales_Channel",
    "Region_ID",
]
for c_idx, h in enumerate(order_headers, 1):
  ws5.cell(row=4, column=c_idx, value=h)
style_header_row(ws5, 4, len(order_headers))

# Populate a representative 2,000 order lines with live Excel formulas.
clean_details_path = CLEANED_DIR / "fact_order_details.csv"
clean_orders_path = CLEANED_DIR / "fact_orders.csv"

orders_lookup = {}
with open(clean_orders_path, "r", encoding="utf-8") as f:
  reader = csv.reader(f)
  next(reader)
  for row in reader:
    orders_lookup[row[0]] = (row[1], row[2], row[3], row[4])

with open(clean_details_path, "r", encoding="utf-8") as f:
  reader = csv.reader(f)
  next(reader)
  for idx, row in enumerate(reader):
    if idx >= 2000:
      break
    r_idx = idx + 5
    dtl_id, ord_id, prod_id, qty, up, disc, gsales, damt, nsales, tcost, nprof = (
        row
    )
    o_info = orders_lookup.get(
        ord_id, ("2024-01-15", "CUST-00001", "REG-NA", "Direct Web")
    )

    ws5.cell(row=r_idx, column=1, value=dtl_id)
    ws5.cell(row=r_idx, column=2, value=ord_id)
    ws5.cell(row=r_idx, column=3, value=o_info[0])
    ws5.cell(row=r_idx, column=4, value=o_info[1])
    ws5.cell(row=r_idx, column=5, value=prod_id)
    ws5.cell(row=r_idx, column=6, value=int(qty))
    ws5.cell(
        row=r_idx,
        column=7,
        value=(
            f"=IFERROR(XLOOKUP(E{r_idx}, '04_Products'!$A:$A,"
            f" '04_Products'!$G:$G), {up})"
        ),
    )
    ws5.cell(
        row=r_idx,
        column=8,
        value=(
            f"=IFERROR(XLOOKUP(E{r_idx}, '04_Products'!$A:$A,"
            " '04_Products'!$F:$F), 0)"
        ),
    )
    ws5.cell(row=r_idx, column=9, value=f"=F{r_idx}*G{r_idx}")
    ws5.cell(row=r_idx, column=10, value=float(disc))
    ws5.cell(row=r_idx, column=11, value=f"=I{r_idx}*J{r_idx}")
    ws5.cell(row=r_idx, column=12, value=f"=I{r_idx}-K{r_idx}")
    ws5.cell(row=r_idx, column=13, value=f"=F{r_idx}*H{r_idx}")
    ws5.cell(row=r_idx, column=14, value=f"=L{r_idx}-M{r_idx}")
    ws5.cell(row=r_idx, column=15, value=f"=IFERROR(N{r_idx}/L{r_idx}, 0)")
    ws5.cell(row=r_idx, column=16, value=f"=YEAR(C{r_idx})")
    ws5.cell(row=r_idx, column=17, value=f'=TEXT(C{r_idx}, "yyyy-mm")')
    ws5.cell(row=r_idx, column=18, value=o_info[3])
    ws5.cell(row=r_idx, column=19, value=o_info[2])

    for col_i in range(1, len(order_headers) + 1):
      c = ws5.cell(row=r_idx, column=col_i)
      c.font = DATA_FONT
      c.border = THIN_BORDER
      if col_i in [7, 8, 9, 11, 12, 13, 14]:
        c.number_format = "$#,##0.00"
      elif col_i in [10, 15]:
        c.number_format = "0.0%"
      elif col_i == 3:
        c.number_format = "yyyy-mm-dd"

autofit_columns(ws5, len(order_headers))

# ==========================================
# SHEET 6: 06_Pivot_Analysis
# ==========================================
print("Creating Sheet 06_Pivot_Analysis...")
ws6 = wb.create_sheet(title="06_Pivot_Analysis")
ws6.views.sheetView[0].showGridLines = True

ws6["A1"] = "SAMPLE PIVOT & MULTI-DIMENSIONAL ANALYSIS"
ws6["A1"].font = TITLE_FONT
ws6["A2"] = (
    "Formula-based sample analysis of the 2,000 order lines in 05_Orders; "
    "see 09_Warehouse_KPIs for full-warehouse totals."
)
ws6["A2"].font = SUBTITLE_FONT

# Table 1: Annual Performance Summary
ws6["A4"] = "1. ANNUAL REVENUE & PROFIT SUMMARY"
ws6["A4"].font = SECTION_FONT
t1_headers = [
    "Fiscal Year",
    "Total Orders",
    "Units Sold",
    "Gross Sales",
    "Discount Given",
    "Net Revenue",
    "Total COGS",
    "Net Profit",
    "Profit Margin %",
]
for c_idx, h in enumerate(t1_headers, 1):
  ws6.cell(row=5, column=c_idx, value=h)
style_header_row(ws6, 5, len(t1_headers))

years = [2023, 2024, 2025]
for idx, yr in enumerate(years):
  r = idx + 6
  ws6.cell(row=r, column=1, value=yr)
  ws6.cell(
      row=r,
      column=2,
      value=f"=COUNTIFS('05_Orders'!$P:$P, A{r})",
  )
  ws6.cell(
      row=r,
      column=3,
      value=f"=SUMIFS('05_Orders'!$F:$F, '05_Orders'!$P:$P, A{r})",
  )
  ws6.cell(
      row=r,
      column=4,
      value=f"=SUMIFS('05_Orders'!$I:$I, '05_Orders'!$P:$P, A{r})",
  )
  ws6.cell(
      row=r,
      column=5,
      value=f"=SUMIFS('05_Orders'!$K:$K, '05_Orders'!$P:$P, A{r})",
  )
  ws6.cell(
      row=r,
      column=6,
      value=f"=SUMIFS('05_Orders'!$L:$L, '05_Orders'!$P:$P, A{r})",
  )
  ws6.cell(
      row=r,
      column=7,
      value=f"=SUMIFS('05_Orders'!$M:$M, '05_Orders'!$P:$P, A{r})",
  )
  ws6.cell(
      row=r,
      column=8,
      value=f"=SUMIFS('05_Orders'!$N:$N, '05_Orders'!$P:$P, A{r})",
  )
  ws6.cell(row=r, column=9, value=f"=IFERROR(H{r}/F{r}, 0)")

  for col_i in range(1, len(t1_headers) + 1):
    c = ws6.cell(row=r, column=col_i)
    c.font = DATA_FONT
    c.border = THIN_BORDER
    if col_i in [4, 5, 6, 7, 8]:
      c.number_format = "$#,##0.00"
    elif col_i == 9:
      c.number_format = "0.0%"
    elif col_i in [2, 3]:
      c.number_format = "#,##0"

# Total row
r_tot = 9
ws6.cell(row=r_tot, column=1, value="Total Enterprise")
ws6.cell(row=r_tot, column=2, value="=SUM(B6:B8)")
ws6.cell(row=r_tot, column=3, value="=SUM(C6:C8)")
ws6.cell(row=r_tot, column=4, value="=SUM(D6:D8)")
ws6.cell(row=r_tot, column=5, value="=SUM(E6:E8)")
ws6.cell(row=r_tot, column=6, value="=SUM(F6:F8)")
ws6.cell(row=r_tot, column=7, value="=SUM(G6:G8)")
ws6.cell(row=r_tot, column=8, value="=SUM(H6:H8)")
ws6.cell(row=r_tot, column=9, value="=IFERROR(H9/F9, 0)")
for col_i in range(1, len(t1_headers) + 1):
  c = ws6.cell(row=r_tot, column=col_i)
  c.font = BOLD_FONT
  c.fill = LIGHT_BLUE_FILL
  c.border = DOUBLE_BOTTOM_BORDER
  if col_i in [4, 5, 6, 7, 8]:
    c.number_format = "$#,##0.00"
  elif col_i == 9:
    c.number_format = "0.0%"
  elif col_i in [2, 3]:
    c.number_format = "#,##0"

# Table 2: Regional Performance
ws6["A11"] = "2. REGIONAL PERFORMANCE & MARGIN CONTRIBUTION"
ws6["A11"].font = SECTION_FONT
t2_headers = [
    "Region Code",
    "Region Name",
    "Net Revenue",
    "Net Profit",
    "Profit Margin %",
    "Revenue Share %",
]
for c_idx, h in enumerate(t2_headers, 1):
  ws6.cell(row=12, column=c_idx, value=h)
style_header_row(ws6, 12, len(t2_headers))

regions_list = [
    ("REG-NA", "North America"),
    ("REG-EU", "Europe"),
    ("REG-APAC", "Asia-Pacific"),
    ("REG-LATAM", "Latin America"),
]
for idx, (rcode, rname) in enumerate(regions_list):
  r = idx + 13
  ws6.cell(row=r, column=1, value=rcode)
  ws6.cell(row=r, column=2, value=rname)
  ws6.cell(
      row=r,
      column=3,
      value=f"=SUMIFS('05_Orders'!$L:$L, '05_Orders'!$S:$S, A{r})",
  )
  ws6.cell(
      row=r,
      column=4,
      value=f"=SUMIFS('05_Orders'!$N:$N, '05_Orders'!$S:$S, A{r})",
  )
  ws6.cell(row=r, column=5, value=f"=IFERROR(D{r}/C{r}, 0)")
  ws6.cell(row=r, column=6, value=f"=IFERROR(C{r}/$F$9, 0)")

  for col_i in range(1, len(t2_headers) + 1):
    c = ws6.cell(row=r, column=col_i)
    c.font = DATA_FONT
    c.border = THIN_BORDER
    if col_i in [3, 4]:
      c.number_format = "$#,##0.00"
    elif col_i in [5, 6]:
      c.number_format = "0.0%"

# Table 3: Discount Band vs Margin Elasticity
ws6["A19"] = "3. DISCOUNT ELASTICITY & MARGIN EROSION ANALYSIS"
ws6["A19"].font = SECTION_FONT
t3_headers = [
    "Discount Tier",
    "Transaction Count",
    "Net Revenue",
    "Total Profit",
    "Realized Margin %",
    "Pricing Health",
]
for c_idx, h in enumerate(t3_headers, 1):
  ws6.cell(row=20, column=c_idx, value=h)
style_header_row(ws6, 20, len(t3_headers))

disc_tiers = [
    ("0% Full Price", 0.00, 0.00),
    ("1% - 10% Low Discount", 0.01, 0.10),
    ("11% - 20% Moderate Discount", 0.11, 0.20),
    ("> 20% High Discount", 0.21, 1.00),
]

for idx, (tier_name, min_d, max_d) in enumerate(disc_tiers):
  r = idx + 21
  ws6.cell(row=r, column=1, value=tier_name)
  if min_d == 0:
    ws6.cell(
        row=r,
        column=2,
        value="=COUNTIFS('05_Orders'!$J:$J, 0)",
    )
    ws6.cell(
        row=r,
        column=3,
        value="=SUMIFS('05_Orders'!$L:$L, '05_Orders'!$J:$J, 0)",
    )
    ws6.cell(
        row=r,
        column=4,
        value="=SUMIFS('05_Orders'!$N:$N, '05_Orders'!$J:$J, 0)",
    )
  else:
    ws6.cell(
        row=r,
        column=2,
        value=(
            f"=COUNTIFS('05_Orders'!$J:$J, \">={min_d}\", '05_Orders'!$J:$J,"
            f" \"<={max_d}\")"
        ),
    )
    ws6.cell(
        row=r,
        column=3,
        value=(
            f"=SUMIFS('05_Orders'!$L:$L, '05_Orders'!$J:$J, \">={min_d}\","
            f" '05_Orders'!$J:$J, \"<={max_d}\")"
        ),
    )
    ws6.cell(
        row=r,
        column=4,
        value=(
            f"=SUMIFS('05_Orders'!$N:$N, '05_Orders'!$J:$J, \">={min_d}\","
            f" '05_Orders'!$J:$J, \"<={max_d}\")"
        ),
    )

  ws6.cell(row=r, column=5, value=f"=IFERROR(D{r}/C{r}, 0)")
  ws6.cell(
      row=r,
      column=6,
      value=(
          f'=IF(E{r}>=0.25, "Highly Profitable", IF(E{r}>=0.15, "Acceptable",'
          ' "Margin Drag Alert"))'
      ),
  )

  for col_i in range(1, len(t3_headers) + 1):
    c = ws6.cell(row=r, column=col_i)
    c.font = DATA_FONT
    c.border = THIN_BORDER
    if col_i in [3, 4]:
      c.number_format = "$#,##0.00"
    elif col_i == 5:
      c.number_format = "0.0%"
    elif col_i == 2:
      c.number_format = "#,##0"

autofit_columns(ws6, 10)

# ==========================================
# SHEET 7: 07_KPI_Summary
# ==========================================
print("Creating Sheet 07_KPI_Summary...")
ws7 = wb.create_sheet(title="07_KPI_Summary")
ws7.views.sheetView[0].showGridLines = True

ws7["A1"] = "SAMPLE KPI FORMULA EXAMPLES"
ws7["A1"].font = TITLE_FONT
ws7["A2"] = (
    "Formula examples based on the sample in 05_Orders; official full-warehouse"
    " metrics are in 09_Warehouse_KPIs."
)
ws7["A2"].font = SUBTITLE_FONT


# Build KPI Cards
def create_kpi_card(ws, top_left, title, formula, num_format, fill_color):
  col, row = top_left

  # Assign values to top-left cells first
  c_label = ws.cell(row=row, column=col, value=title)
  c_label.font = KPI_LABEL_FONT
  c_label.alignment = Alignment(horizontal="center", vertical="center")

  c_val = ws.cell(row=row + 1, column=col, value=formula)
  c_val.font = KPI_VAL_FONT
  c_val.alignment = Alignment(horizontal="center", vertical="center")
  c_val.number_format = num_format

  # Merge after assigning values
  ws.merge_cells(
      start_row=row, start_column=col, end_row=row, end_column=col + 1
  )
  ws.merge_cells(
      start_row=row + 1, start_column=col, end_row=row + 2, end_column=col + 1
  )

  for r_i in range(row, row + 3):
    for c_i in range(col, col + 2):
      cell = ws.cell(row=r_i, column=c_i)
      cell.fill = fill_color
      cell.border = THIN_BORDER


create_kpi_card(
    ws7,
    (1, 4),
    "TOTAL NET REVENUE",
    "='06_Pivot_Analysis'!F9",
    "$#,##0",
    LIGHT_BLUE_FILL,
)
create_kpi_card(
    ws7,
    (3, 4),
    "SAMPLE LINE-ITEM PROFIT",
    "='06_Pivot_Analysis'!H9",
    "$#,##0",
    LIGHT_GREEN_FILL,
)
create_kpi_card(
    ws7,
    (5, 4),
    "PROFIT MARGIN %",
    "='06_Pivot_Analysis'!I9",
    "0.0%",
    LIGHT_GREEN_FILL,
)
create_kpi_card(
    ws7,
    (7, 4),
    "TOTAL ORDERS",
    "='06_Pivot_Analysis'!B9",
    "#,##0",
    CARD_BG_FILL,
)
create_kpi_card(
    ws7,
    (9, 4),
    "AVERAGE ORDER VALUE (AOV)",
    "=IFERROR('06_Pivot_Analysis'!F9/'06_Pivot_Analysis'!B9, 0)",
    "$#,##0.00",
    LIGHT_AMBER_FILL,
)

# KPI formulas without invented target benchmarks
ws7["A8"] = "SAMPLE KPI FORMULAS (NO BUSINESS TARGETS SUPPLIED)"
ws7["A8"].font = SECTION_FONT

kpi_table_headers = [
    "Metric Name",
    "Sample Formula",
    "Target Supplied",
    "Variance",
    "Achievement",
    "Status",
]
for c_idx, h in enumerate(kpi_table_headers, 1):
  ws7.cell(row=9, column=c_idx, value=h)
style_header_row(ws7, 9, len(kpi_table_headers))

kpis_data = [
    ("Net Revenue", "='06_Pivot_Analysis'!F9", "$#,##0.00"),
    ("Line-item profit", "='06_Pivot_Analysis'!H9", "$#,##0.00"),
    ("Line-item margin %", "='06_Pivot_Analysis'!I9", "0.0%"),
    (
        "Average Order Value (AOV)",
        "=IFERROR('06_Pivot_Analysis'!F9/'06_Pivot_Analysis'!B9, 0)",
        "$#,##0.00",
    ),
    (
        "Discount Rate %",
        "=IFERROR('06_Pivot_Analysis'!E9/'06_Pivot_Analysis'!D9, 0)",
        "0.0%",
    ),
]

for idx, (kname, kformula, kfmt) in enumerate(kpis_data):
  r = idx + 10
  ws7.cell(row=r, column=1, value=kname)
  ws7.cell(row=r, column=2, value=kformula)
  ws7.cell(row=r, column=3, value="No")
  ws7.cell(row=r, column=6, value="Not assessed")

  for col_i in range(1, len(kpi_table_headers) + 1):
    c = ws7.cell(row=r, column=col_i)
    c.font = DATA_FONT
    c.border = THIN_BORDER
    if col_i == 2:
      c.number_format = kfmt

autofit_columns(ws7, 10)

# ==========================================
# SHEET 8: 08_Business_Insights
# ==========================================
print("Creating Sheet 08_Business_Insights...")
ws8 = wb.create_sheet(title="08_Business_Insights")
ws8.views.sheetView[0].showGridLines = True

ws8["A1"] = "FULL-WAREHOUSE BUSINESS OBSERVATIONS"
ws8["A1"].font = TITLE_FONT
ws8["A2"] = (
    "Descriptive patterns from the current full warehouse; observations are not"
    " causal estimates, forecasts, or measured financial benefits."
)
ws8["A2"].font = SUBTITLE_FONT

insight_headers = [
    "Observation #",
    "Domain",
    "Observed Pattern",
    "Quantitative Evidence",
    "Interpretation / Limitation",
    "Suggested Follow-up",
]
for c_idx, h in enumerate(insight_headers, 1):
  ws8.cell(row=4, column=c_idx, value=h)
style_header_row(ws8, 4, len(insight_headers))

discounts_by_tier = {row["tier"]: row for row in warehouse["discounts"]}
categories_by_name = {row["name"]: row for row in warehouse["categories"]}
regions_by_name = {row["name"]: row for row in warehouse["regions"]}
customer_metrics = warehouse["customers"]
financial_metrics = warehouse["financial"]
return_metrics = warehouse["returns"]
inventory_metrics = warehouse["inventory"]
target_metrics = warehouse["targets"]
top_return_reason = warehouse["return_reasons"][0]
highest_refund_reason = max(warehouse["return_reasons"], key=lambda row: row["refunds"])
repeat_rate_pct = (
    100 * customer_metrics["repeat_customers"]
    / customer_metrics["customers_with_orders"]
)
return_rate_pct = 100 * return_metrics["units"] / financial_metrics["units"]
target_attainment_pct = (
    100 * financial_metrics["net_sales"] / target_metrics["sales_target"]
)
technology_share_pct = (
    100 * categories_by_name["Technology"]["net_sales"]
    / financial_metrics["net_sales"]
)
region_margins = [row["margin_pct"] for row in warehouse["regions"]]

insights_rows = [
    (
        1,
        "Discount bands",
        "Higher discount bands have lower observed line-item margins.",
        (
            f">20%: {discounts_by_tier['>20%']['margin_pct']:.1f}% across "
            f"{discounts_by_tier['>20%']['lines']:,} lines; 0%: "
            f"{discounts_by_tier['0%']['margin_pct']:.1f}% across "
            f"{discounts_by_tier['0%']['lines']:,} lines."
        ),
        (
            "Association only; product and channel mix differ by discount tier. "
            "No incremental volume or causal elasticity was estimated."
        ),
        (
            "Review high-discount transactions and compare like-for-like products "
            "before changing discount policy."
        ),
    ),
    (
        2,
        "Product mix",
        "Technology is the largest net-sales category.",
        (
            f"Technology: ${categories_by_name['Technology']['net_sales']:,.2f} "
            f"({technology_share_pct:.1f}% of net sales), "
            f"{categories_by_name['Technology']['margin_pct']:.1f}% line margin; "
            f"Office Supplies margin: "
            f"{categories_by_name['Office Supplies']['margin_pct']:.1f}%."
        ),
        (
            "Category margins describe stored line values before refunds; mix "
            "and cost differences are not controlled."
        ),
        "Review category pricing, cost, and product mix together.",
    ),
    (
        3,
        "Regional mix",
        "North America has the highest net sales; regional margins are similar.",
        (
            f"North America: ${regions_by_name['North America']['net_sales']:,.2f}; "
            f"regional line margins range {min(region_margins):.1f}%–"
            f"{max(region_margins):.1f}%."
        ),
        "The current data shows a sales-scale difference, not a clear regional "
        "margin gap.",
        "Investigate market size, volume, and costs before reallocating spend.",
    ),
    (
        4,
        "Customer orders",
        "Most customers with order headers have two or more distinct orders.",
        (
            f"{customer_metrics['repeat_customers']:,} of "
            f"{customer_metrics['customers_with_orders']:,} customers "
            f"({repeat_rate_pct:.2f}%) have 2+ distinct order headers; "
            f"{customer_metrics['one_time_customers']:,} have one."
        ),
        "Counts include every order status, including cancelled orders; this is "
        "not a completed-purchase retention rate.",
        "Recalculate retention using completed orders and a defined cohort window.",
    ),
    (
        5,
        "Returns",
        "Recorded returns total more than one and a half million dollars in refunds.",
        (
            f"{return_metrics['incidents']:,} incidents, "
            f"{return_metrics['units']:,} units ({return_rate_pct:.2f}% of "
            f"line units), ${return_metrics['refunds']:,.2f} refunded. "
            f"Most incidents: {top_return_reason['reason']} "
            f"({top_return_reason['incidents']:,}); largest refund reason: "
            f"{highest_refund_reason['reason']} "
            f"(${highest_refund_reason['refunds']:,.2f})."
        ),
        "Refunds are recorded amounts; reverse freight, restocking, and other "
        "return costs are not modeled.",
        "Validate leading return reasons against operational and supplier records.",
    ),
    (
        6,
        "Inventory",
        "64 SKUs are at or below their reorder levels in the latest snapshot.",
        (
            f"{inventory_metrics['snapshot_date']}: "
            f"{inventory_metrics['closing_units']:,} closing units valued at "
            f"${inventory_metrics['inventory_value']:,.2f} using product cost."
        ),
        "Inventory is a monthly snapshot; its values are not attributed to "
        "region, sales channel, or customer segment.",
        "Review the flagged SKUs against lead times and replenishment plans.",
    ),
    (
        7,
        "Sales targets",
        "Aggregate net sales exceed the stored aggregate sales target.",
        (
            f"${financial_metrics['net_sales']:,.2f} net sales against "
            f"${target_metrics['sales_target']:,.2f} targets "
            f"({target_attainment_pct:.1f}%); actuals include all order statuses."
        ),
        "Actuals and targets should be aligned by period, region, and category; "
        "the overall ratio is not a channel/segment comparison.",
        "Validate status and target-scope alignment before using attainment for "
        "performance decisions.",
    ),
]

for idx, rdata in enumerate(insights_rows):
  r = idx + 5
  for col_i, val in enumerate(rdata, 1):
    c = ws8.cell(row=r, column=col_i, value=val)
    c.font = DATA_FONT
    c.border = THIN_BORDER
    if col_i == 1:
      c.alignment = Alignment(horizontal="center", vertical="top")
    else:
      c.alignment = Alignment(
          horizontal="left", vertical="top", wrap_text=True
      )

autofit_columns(ws8, len(insight_headers))
ws8.column_dimensions["C"].width = 32
ws8.column_dimensions["D"].width = 32
ws8.column_dimensions["E"].width = 30
ws8.column_dimensions["F"].width = 36

ws9 = wb.create_sheet(title="09_Warehouse_KPIs")
ws9.views.sheetView[0].showGridLines = False
ws9["A1"] = "FULL-WAREHOUSE SQL RESULTS"
ws9["A1"].font = TITLE_FONT
ws9["A2"] = (
    "Static values from data/ecommerce_analytics.db at build time. "
    "Sales and line-item profit include cancelled orders; refunds are separate."
)
ws9["A2"].font = SUBTITLE_FONT
summary_headers = ["Metric", "Full-warehouse value", "Definition / scope"]
for col, header in enumerate(summary_headers, 1):
  ws9.cell(row=4, column=col, value=header)
style_header_row(ws9, 4, len(summary_headers))

f = warehouse["financial"]
c = warehouse["customers"]
r = warehouse["returns"]
i = warehouse["inventory"]
t = warehouse["targets"]
repeat_rate = c["repeat_customers"] / c["customers_with_orders"]
return_rate = r["units"] / f["units"]
line_margin = f["line_profit"] / f["net_sales"]
refund_adjusted_profit = f["line_profit"] - r["refunds"]
summary_rows = [
    ("Gross sales", f["gross_sales"], "Order-line gross sales before discounts."),
    ("Discounts", f["discounts"], "Stored order-line discount amounts."),
    ("Net sales", f["net_sales"], "Gross sales less line-item discounts."),
    ("COGS", f["cogs"], "Stored order-line total cost."),
    ("Line-item profit", f["line_profit"], "Net sales less stored COGS; before refunds and operating expenses."),
    ("Line-item margin", line_margin, "Line-item profit / net sales."),
    ("Distinct orders", f["orders"], "Distinct order IDs represented by order lines; all statuses."),
    ("Order-detail rows", f["order_lines"], "Rows in fact_order_details."),
    ("Units on order lines", f["units"], "Sum of quantity in fact_order_details."),
    ("Average order value", f["net_sales"] / f["orders"], "Net sales / distinct order IDs represented by order lines."),
    ("Customers with order headers", c["customers_with_orders"], "Distinct customers in fact_orders; all statuses."),
    ("Repeat customers", c["repeat_customers"], "Customers with 2+ distinct order headers."),
    ("Repeat-customer rate", repeat_rate, "Repeat customers / customers with at least one order header."),
    ("One-time customers", c["one_time_customers"], "Customers with exactly one distinct order header."),
    ("Return incidents", r["incidents"], "Distinct return IDs."),
    ("Returned units", r["units"], "Sum of fact_returns.return_quantity."),
    ("Return-unit rate", return_rate, "Returned units / units on all order-detail lines."),
    ("Refunds", r["refunds"], "Recorded refund amounts."),
    ("Refund-adjusted profit", refund_adjusted_profit, "Line-item profit less recorded refunds; not operating profit or EBITDA."),
    ("Sales targets", t["sales_target"], "Sum of fact_sales_targets.sales_target."),
    ("Target attainment", f["net_sales"] / t["sales_target"], "Aggregate net sales / aggregate sales target; all order statuses."),
    ("Latest inventory snapshot", i["snapshot_date"], "Maximum snapshot_date in fact_inventory."),
    ("Latest closing units", i["closing_units"], "Closing stock at the latest snapshot."),
    ("Latest inventory value", i["inventory_value"], "Closing units × product cost at the latest snapshot."),
    ("SKUs at/below reorder", i["below_reorder"], "Distinct latest-snapshot SKUs at or below product reorder level."),
]
for row, (name, value, definition) in enumerate(summary_rows, 5):
  ws9.cell(row, 1, name)
  ws9.cell(row, 2, value)
  ws9.cell(row, 3, definition)
  for col in range(1, 4):
    cell = ws9.cell(row, col)
    cell.font = DATA_FONT
    cell.border = THIN_BORDER
    cell.alignment = Alignment(vertical="top", wrap_text=(col == 3))
  if name in {
      "Gross sales", "Discounts", "Net sales", "COGS", "Line-item profit",
      "Average order value", "Refunds", "Refund-adjusted profit", "Sales targets",
      "Latest inventory value",
  }:
    ws9.cell(row, 2).number_format = "$#,##0.00"
  elif name in {"Line-item margin", "Repeat-customer rate", "Return-unit rate", "Target attainment"}:
    ws9.cell(row, 2).number_format = "0.00%"
  elif isinstance(value, int):
    ws9.cell(row, 2).number_format = "#,##0"

count_col = 5
ws9.cell(4, count_col, "Warehouse table")
ws9.cell(4, count_col + 1, "Rows")
style_header_row(ws9, 4, count_col + 1)
for row, (table, count) in enumerate(sorted(warehouse["counts"].items()), 5):
  ws9.cell(row, count_col, table)
  ws9.cell(row, count_col + 1, count)
  ws9.cell(row, count_col).font = DATA_FONT
  ws9.cell(row, count_col + 1).font = DATA_FONT
  ws9.cell(row, count_col).border = THIN_BORDER
  ws9.cell(row, count_col + 1).border = THIN_BORDER
  ws9.cell(row, count_col + 1).number_format = "#,##0"
ws9["E17"] = "Order date range"
ws9["F17"] = f"{warehouse['date_range']['start']} to {warehouse['date_range']['end']}"
ws9["E17"].font = BOLD_FONT
ws9["F17"].font = DATA_FONT
ws9.column_dimensions["A"].width = 31
ws9.column_dimensions["B"].width = 24
ws9.column_dimensions["C"].width = 74
ws9.column_dimensions["E"].width = 28
ws9.column_dimensions["F"].width = 32
ws9.freeze_panes = "A5"

wb.calculation.fullCalcOnLoad = True
wb.calculation.forceFullCalc = True
wb.calculation.calcMode = "auto"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
wb.save(OUTPUT_PATH)
print(f"Excel workbook successfully saved to: {OUTPUT_PATH}")
