"""Build the executive PDF from the current SQLite warehouse."""

import sqlite3
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "data" / "ecommerce_analytics.db"
OUTPUT = ROOT / "reports" / "Executive_Report.pdf"


def fetch_report_data() -> dict:
    if not DATABASE.is_file():
        raise FileNotFoundError(
            f"Warehouse not found at {DATABASE}; run scripts/load_sql_database.py."
        )

    with sqlite3.connect(DATABASE) as connection:
        connection.row_factory = sqlite3.Row
        financial = dict(
            connection.execute(
                """
                SELECT
                    ROUND(SUM(gross_sales), 2) AS gross_sales,
                    ROUND(SUM(discount_amount), 2) AS discounts,
                    ROUND(SUM(net_sales), 2) AS net_sales,
                    ROUND(SUM(total_cost), 2) AS cogs,
                    ROUND(SUM(net_profit), 2) AS line_profit,
                    COUNT(DISTINCT order_id) AS orders,
                    SUM(quantity) AS units
                FROM fact_order_details
                """
            ).fetchone()
        )
        customers = dict(
            connection.execute(
                """
                WITH customer_orders AS (
                    SELECT customer_id, COUNT(DISTINCT order_id) AS order_count
                    FROM fact_orders
                    GROUP BY customer_id
                )
                SELECT COUNT(*) AS with_orders,
                       SUM(order_count >= 2) AS repeat_customers,
                       SUM(order_count = 1) AS one_time_customers
                FROM customer_orders
                """
            ).fetchone()
        )
        returns = dict(
            connection.execute(
                """
                SELECT COUNT(DISTINCT return_id) AS incidents,
                       SUM(return_quantity) AS units,
                       ROUND(SUM(refund_amount), 2) AS refunds
                FROM fact_returns
                """
            ).fetchone()
        )
        inventory = dict(
            connection.execute(
                """
                SELECT i.snapshot_date,
                       SUM(i.closing_stock) AS closing_units,
                       ROUND(SUM(i.closing_stock * p.cost_price), 2) AS value
                FROM fact_inventory AS i
                JOIN dim_product AS p USING (product_id)
                WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM fact_inventory)
                GROUP BY i.snapshot_date
                """
            ).fetchone()
        )
        inventory["below_reorder"] = connection.execute(
            """
            SELECT COUNT(DISTINCT i.product_id)
            FROM fact_inventory AS i
            JOIN dim_product AS p USING (product_id)
            WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM fact_inventory)
              AND i.closing_stock <= p.reorder_level
            """
        ).fetchone()[0]
        target = connection.execute(
            "SELECT ROUND(SUM(sales_target), 2) FROM fact_sales_targets"
        ).fetchone()[0]
        date_range = connection.execute(
            "SELECT MIN(order_date), MAX(order_date) FROM fact_orders"
        ).fetchone()
        categories = [
            dict(row)
            for row in connection.execute(
                """
                SELECT p.category,
                       ROUND(SUM(d.net_sales), 2) AS net_sales,
                       100.0 * SUM(d.net_profit) / NULLIF(SUM(d.net_sales), 0)
                           AS margin_pct
                FROM fact_order_details AS d
                JOIN dim_product AS p USING (product_id)
                GROUP BY p.category ORDER BY net_sales DESC
                """
            )
        ]
        discount_tiers = {
            row["tier"]: dict(row)
            for row in connection.execute(
                """
                SELECT CASE
                         WHEN discount_rate = 0 THEN '0%'
                         WHEN discount_rate <= 0.10 THEN '>0%-10%'
                         WHEN discount_rate <= 0.20 THEN '>10%-20%'
                         ELSE '>20%'
                       END AS tier,
                       COUNT(*) AS lines,
                       100.0 * SUM(net_profit) / NULLIF(SUM(net_sales), 0)
                           AS margin_pct
                FROM fact_order_details
                GROUP BY tier ORDER BY MIN(discount_rate)
                """
            )
        }
        return_reasons = [
            dict(row)
            for row in connection.execute(
                """
                SELECT return_reason AS reason,
                       COUNT(DISTINCT return_id) AS incidents,
                       ROUND(SUM(refund_amount), 2) AS refunds
                FROM fact_returns
                GROUP BY return_reason ORDER BY incidents DESC
                """
            )
        ]
        return {
            "financial": financial,
            "customers": customers,
            "returns": returns,
            "inventory": inventory,
            "target": target,
            "date_range": date_range,
            "categories": categories,
            "discount_tiers": discount_tiers,
            "return_reasons": return_reasons,
        }


def money(value: float) -> str:
    return f"${value:,.2f}"


def build_report() -> Path:
    data = fetch_report_data()
    f = data["financial"]
    c = data["customers"]
    r = data["returns"]
    i = data["inventory"]
    repeat_rate = c["repeat_customers"] / c["with_orders"]
    return_rate = r["units"] / f["units"]
    line_margin = f["line_profit"] / f["net_sales"]
    adjusted_profit = f["line_profit"] - r["refunds"]
    target_attainment = f["net_sales"] / data["target"]
    category_by_name = {row["category"]: row for row in data["categories"]}
    discount_high = data["discount_tiers"][">20%"]
    discount_zero = data["discount_tiers"]["0%"]
    most_frequent_return = data["return_reasons"][0]

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#14243a"),
            fontSize=19,
            leading=23,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#52677f"),
            fontSize=9,
            leading=13,
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#14243a"),
            fontSize=12,
            leading=15,
            spaceBefore=8,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["BodyText"],
            fontSize=8.5,
            leading=12,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableSmall",
            parent=styles["BodyText"],
            fontSize=7.5,
            leading=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["BodyText"],
            fontSize=7.5,
            leading=10,
            textColor=colors.white,
            fontName="Helvetica-Bold",
        )
    )

    def paragraph(text: str, style: str = "BodySmall") -> Paragraph:
        return Paragraph(text, styles[style])

    story = [
        paragraph(
            "E-Commerce Sales, Customer &amp; Business Performance Analytics",
            "ReportTitle",
        ),
        paragraph(
            "ApexCart Retail Inc. · Synthetic dataset · "
            f"{escape(data['date_range'][0])} to {escape(data['date_range'][1])}",
            "ReportSubtitle",
        ),
        paragraph(
            "This report summarizes the current SQLite warehouse. All inputs are "
            "synthetic; findings are descriptive and are not forecasts or claims "
            "about a real retailer.",
            "BodySmall",
        ),
        paragraph("Executive scorecard", "SectionHeading"),
    ]
    scorecard = [
        [
            paragraph("Measure", "TableHeader"),
            paragraph("Result", "TableHeader"),
            paragraph("Definition", "TableHeader"),
        ],
        ["Gross sales", money(f["gross_sales"]), "Stored line gross sales."],
        ["Discounts", money(f["discounts"]), "Stored line discount amounts."],
        ["Net sales", money(f["net_sales"]), "Gross sales less discounts."],
        ["COGS", money(f["cogs"]), "Stored order-line cost."],
        [
            "Line-item profit",
            money(f["line_profit"]),
            "Net sales less COGS; before refunds and operating expenses.",
        ],
        ["Line-item margin", f"{line_margin:.2%}", "Line-item profit / net sales."],
        [
            "Average order value",
            money(f["net_sales"] / f["orders"]),
            "Net sales / distinct order IDs represented by order lines.",
        ],
        [
            "Refund-adjusted profit",
            money(adjusted_profit),
            "Line-item profit less recorded refunds; not operating profit or EBITDA.",
        ],
        [
            "Aggregate target attainment",
            f"{target_attainment:.2%}",
            "Net sales / summed stored sales targets.",
        ],
    ]
    table_data = [
        [paragraph(str(cell), "TableHeader") for cell in scorecard[0]],
        *[
            [paragraph(str(cell), "TableSmall") for cell in row]
            for row in scorecard[1:]
        ],
    ]
    scorecard_table = Table(
        table_data,
        colWidths=[1.45 * inch, 1.25 * inch, 4.05 * inch],
        repeatRows=1,
        hAlign="LEFT",
    )
    scorecard_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                    colors.white,
                    colors.HexColor("#f1f5f9"),
                ]),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend([scorecard_table, Spacer(1, 8)])

    technology = category_by_name["Technology"]
    office = category_by_name["Office Supplies"]
    size_reason = next(
        row
        for row in data["return_reasons"]
        if row["reason"] == "Size / Fit Mismatch"
    )
    story.extend(
        [
            paragraph("Observed patterns", "SectionHeading"),
            paragraph(
                f"Technology contributes {money(technology['net_sales'])} in net "
                f"sales at a {technology['margin_pct']:.1f}% line margin. "
                f"Office Supplies has an observed {office['margin_pct']:.1f}% "
                "margin on a smaller sales base.",
                "BodySmall",
            ),
            paragraph(
                f"The &gt;20% discount tier has a {discount_high['margin_pct']:.1f}% "
                f"line margin across {discount_high['lines']:,} lines; the 0% "
                f"tier is {discount_zero['margin_pct']:.1f}% across "
                f"{discount_zero['lines']:,} lines. These are descriptive "
                "comparisons and do not control for product/channel mix or "
                "measure incremental sales.",
                "BodySmall",
            ),
            paragraph(
                f"{c['repeat_customers']:,} of {c['with_orders']:,} customers "
                f"with an order header have 2+ distinct order headers "
                f"({repeat_rate:.2%}); {c['one_time_customers']:,} have one. "
                "All statuses, including cancelled, are included.",
                "BodySmall",
            ),
            paragraph(
                f"Returns include {r['incidents']:,} incidents and "
                f"{r['units']:,} returned units ({return_rate:.2%} of all "
                f"order-line units), with {money(r['refunds'])} in recorded "
                f"refunds. {most_frequent_return['reason']} is most frequent "
                f"({most_frequent_return['incidents']:,}); "
                f"{size_reason['reason']} has the largest reason-level refund "
                f"amount ({money(size_reason['refunds'])}).",
                "BodySmall",
            ),
            paragraph(
                f"The {i['snapshot_date']} inventory snapshot has "
                f"{i['closing_units']:,} closing units valued at "
                f"{money(i['value'])} using product cost; "
                f"{i['below_reorder']} SKUs are at or below reorder level.",
                "BodySmall",
            ),
            paragraph("Scope and decision cautions", "SectionHeading"),
            paragraph(
                "Sales and line-item profit include all stored order statuses, "
                "including cancelled orders. Line-item profit excludes refunds; "
                "refund-adjusted profit subtracts recorded refunds only and "
                "excludes operating, fulfillment, reverse-freight, and handling "
                "costs. Targets are monthly by region/category and do not have "
                "channel or customer-segment dimensions. Inventory is a monthly "
                "product snapshot with no region/channel/segment dimension. "
                "Validate these definitions before using aggregate comparisons "
                "for management decisions.",
                "BodySmall",
            ),
        ]
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        title="ApexCart Executive Analytics Report",
        author="ApexCart Analytics Portfolio Project",
    )
    document.build(story)
    return OUTPUT


if __name__ == "__main__":
    print(f"Report saved to {build_report()}")
