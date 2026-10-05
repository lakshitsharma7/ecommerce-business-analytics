"""Serve a local, filterable dashboard backed by the project SQLite warehouse."""

import json
import sqlite3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent
DATABASE = ROOT / "data" / "ecommerce_analytics.db"
HOST = "127.0.0.1"
PORT = 8000

BASE_FROM = """
FROM fact_orders o
JOIN fact_order_details d ON d.order_id = o.order_id
JOIN dim_product p ON p.product_id = d.product_id
JOIN dim_customer c ON c.customer_id = o.customer_id
JOIN dim_region r ON r.region_id = o.region_id
"""

FILTER_COLUMNS = {
    "year": "strftime('%Y', o.order_date)",
    "region": "r.region_name",
    "category": "p.category",
    "channel": "o.sales_channel",
    "segment": "c.customer_segment",
}


def connect() -> sqlite3.Connection:
    if not DATABASE.is_file():
        raise FileNotFoundError(
            f"SQLite database not found at {DATABASE}; run scripts/load_sql_database.py"
        )
    connection = sqlite3.connect(f"file:{DATABASE.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def query_rows(
    connection: sqlite3.Connection, sql: str, parameters: list[object] | None = None
) -> list[dict[str, object]]:
    return [dict(row) for row in connection.execute(sql, parameters or ())]


def filter_clause(filters: dict[str, str], include: set[str] | None = None) -> tuple[str, list[str]]:
    clauses: list[str] = []
    values: list[str] = []
    for key, column in FILTER_COLUMNS.items():
        if key in filters and (include is None or key in include):
            clauses.append(f"{column} = ?")
            values.append(filters[key])
    return (" WHERE " + " AND ".join(clauses) if clauses else ""), values


def get_options(connection: sqlite3.Connection) -> dict[str, list[str]]:
    return {
        "year": [str(row["year"]) for row in query_rows(
            connection,
            "SELECT DISTINCT strftime('%Y', order_date) AS year "
            "FROM fact_orders ORDER BY year",
        )],
        "region": [str(row["region_name"]) for row in query_rows(
            connection, "SELECT region_name FROM dim_region ORDER BY region_name"
        )],
        "category": [str(row["category"]) for row in query_rows(
            connection, "SELECT DISTINCT category FROM dim_product ORDER BY category"
        )],
        "channel": [str(row["sales_channel"]) for row in query_rows(
            connection,
            "SELECT DISTINCT sales_channel FROM fact_orders ORDER BY sales_channel",
        )],
        "segment": [str(row["customer_segment"]) for row in query_rows(
            connection,
            "SELECT DISTINCT customer_segment FROM dim_customer ORDER BY customer_segment",
        )],
    }


def get_dashboard_data(filters: dict[str, str] | None = None) -> dict[str, object]:
    filters = filters or {}
    with connect() as connection:
        options = get_options(connection)
        for key, value in filters.items():
            if key not in options or value not in options[key]:
                raise ValueError(f"Unsupported {key} filter value: {value}")

        where, parameters = filter_clause(filters)
        row = query_rows(
            connection,
            """
            SELECT
                COUNT(DISTINCT o.order_id) AS orders,
                COUNT(DISTINCT o.customer_id) AS customers,
                COUNT(DISTINCT p.product_id) AS products,
                SUM(d.quantity) AS units,
                SUM(d.gross_sales) AS gross_sales,
                SUM(d.discount_amount) AS discounts,
                SUM(d.net_sales) AS net_sales,
                SUM(d.total_cost) AS cogs,
                SUM(d.net_profit) AS line_profit
            """ + BASE_FROM + where,
            parameters,
        )[0]

        repeat_rows = query_rows(
            connection,
            """
            WITH customer_orders AS (
                SELECT o.customer_id, COUNT(DISTINCT o.order_id) AS order_count
                """ + BASE_FROM + where + """
                GROUP BY o.customer_id
            )
            SELECT
                COUNT(*) AS customers_with_orders,
                SUM(CASE WHEN order_count = 1 THEN 1 ELSE 0 END) AS one_time_customers,
                SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END) AS repeat_customers
            FROM customer_orders
            """,
            parameters,
        )[0]

        monthly = query_rows(
            connection,
            """
            SELECT strftime('%Y-%m', o.order_date) AS period,
                   SUM(d.net_sales) AS net_sales,
                   SUM(d.net_profit) AS line_profit
            """ + BASE_FROM + where + """
            GROUP BY period ORDER BY period
            """,
            parameters,
        )
        regions = query_rows(
            connection,
            """
            SELECT r.region_name AS name, SUM(d.net_sales) AS net_sales,
                   SUM(d.net_profit) AS line_profit
            """ + BASE_FROM + where + """
            GROUP BY r.region_name ORDER BY net_sales DESC
            """,
            parameters,
        )
        categories = query_rows(
            connection,
            """
            SELECT p.category AS name, SUM(d.net_sales) AS net_sales,
                   SUM(d.net_profit) AS line_profit,
                   100.0 * SUM(d.net_profit) / NULLIF(SUM(d.net_sales), 0) AS margin_pct
            """ + BASE_FROM + where + """
            GROUP BY p.category ORDER BY net_sales DESC
            """,
            parameters,
        )
        channels = query_rows(
            connection,
            """
            SELECT o.sales_channel AS name, SUM(d.net_sales) AS net_sales,
                   SUM(d.net_profit) AS line_profit,
                   COUNT(DISTINCT o.order_id) AS orders
            """ + BASE_FROM + where + """
            GROUP BY o.sales_channel ORDER BY net_sales DESC
            """,
            parameters,
        )
        products = query_rows(
            connection,
            """
            SELECT p.product_name AS name, p.category AS category,
                   SUM(d.net_sales) AS net_sales, SUM(d.net_profit) AS line_profit,
                   SUM(d.quantity) AS units
            """ + BASE_FROM + where + """
            GROUP BY p.product_id ORDER BY net_sales DESC LIMIT 8
            """,
            parameters,
        )
        segments = query_rows(
            connection,
            """
            SELECT c.customer_segment AS name,
                   COUNT(DISTINCT o.customer_id) AS customers,
                   COUNT(DISTINCT o.order_id) AS orders,
                   SUM(d.net_sales) AS net_sales
            """ + BASE_FROM + where + """
            GROUP BY c.customer_segment ORDER BY net_sales DESC
            """,
            parameters,
        )
        discounts = query_rows(
            connection,
            """
            SELECT CASE
                     WHEN d.discount_rate = 0 THEN '0%'
                     WHEN d.discount_rate <= 0.10 THEN '>0% to 10%'
                     WHEN d.discount_rate <= 0.20 THEN '>10% to 20%'
                     ELSE '>20%'
                   END AS name,
                   SUM(d.quantity) AS units,
                   SUM(d.net_sales) AS net_sales,
                   SUM(d.net_profit) AS line_profit,
                   SUM(d.gross_sales) AS gross_sales,
                   SUM(d.discount_amount) AS discounts
            """ + BASE_FROM + where + """
            GROUP BY 1 ORDER BY MIN(d.discount_rate)
            """,
            parameters,
        )

        returned_where, returned_parameters = filter_clause(filters)
        returned_rows = query_rows(
            connection,
            """
            SELECT SUM(fr.return_quantity) AS returned_units,
                   SUM(fr.refund_amount) AS refunds,
                   COUNT(DISTINCT fr.return_id) AS return_incidents
            FROM fact_returns fr
            JOIN fact_orders o ON o.order_id = fr.order_id
            JOIN fact_order_details d ON d.order_detail_id = fr.order_detail_id
            JOIN dim_product p ON p.product_id = fr.product_id
            JOIN dim_customer c ON c.customer_id = o.customer_id
            JOIN dim_region r ON r.region_id = o.region_id
            """ + returned_where,
            returned_parameters,
        )[0]
        return_reasons = query_rows(
            connection,
            """
            SELECT fr.return_reason AS name, COUNT(DISTINCT fr.return_id) AS incidents,
                   SUM(fr.return_quantity) AS units,
                   SUM(fr.refund_amount) AS refunds
            FROM fact_returns fr
            JOIN fact_orders o ON o.order_id = fr.order_id
            JOIN fact_order_details d ON d.order_detail_id = fr.order_detail_id
            JOIN dim_product p ON p.product_id = fr.product_id
            JOIN dim_customer c ON c.customer_id = o.customer_id
            JOIN dim_region r ON r.region_id = o.region_id
            """ + returned_where + """
            GROUP BY fr.return_reason ORDER BY refunds DESC
            """,
            returned_parameters,
        )

        target_filters = {
            key: value for key, value in filters.items() if key in {"year", "region", "category"}
        }
        target_clause = ""
        target_parameters: list[str] = []
        if "year" in target_filters:
            target_clause += " WHERE substr(fst.year_month, 1, 4) = ?"
            target_parameters.append(target_filters["year"])
        for key, column in (("region", "dr.region_name"), ("category", "fst.category_name")):
            if key in target_filters:
                target_clause += (" AND " if target_clause else " WHERE ") + f"{column} = ?"
                target_parameters.append(target_filters[key])
        targets = query_rows(
            connection,
            """
            SELECT SUM(fst.sales_target) AS sales_target,
                   SUM(fst.profit_target) AS profit_target,
                   SUM(fst.order_target) AS order_target
            FROM fact_sales_targets fst
            JOIN dim_region dr ON dr.region_id = fst.region_id
            """ + target_clause,
            target_parameters,
        )[0]
        target_actuals = query_rows(
            connection,
            """
            SELECT SUM(d.net_sales) AS net_sales, SUM(d.net_profit) AS line_profit,
                   COUNT(DISTINCT o.order_id) AS orders
            """ + BASE_FROM + target_clause.replace("fst.year_month", "strftime('%Y-%m', o.order_date)")
            .replace("dr.region_name", "r.region_name")
            .replace("fst.category_name", "p.category"),
            target_parameters,
        )[0]

        inventory_filters = [f"strftime('%Y', fi.snapshot_date) = ?"] if "year" in filters else []
        inventory_parameters: list[str] = [filters["year"]] if "year" in filters else []
        if "category" in filters:
            inventory_filters.append("p.category = ?")
            inventory_parameters.append(filters["category"])
        inventory_where = " WHERE " + " AND ".join(inventory_filters) if inventory_filters else ""
        snapshot = query_rows(
            connection,
            """
            SELECT MAX(fi.snapshot_date) AS snapshot_date
            FROM fact_inventory fi
            JOIN dim_product p ON p.product_id = fi.product_id
            """ + inventory_where,
            inventory_parameters,
        )[0]["snapshot_date"]
        snapshot_where = "WHERE fi.snapshot_date = ?"
        snapshot_parameters: list[object] = [snapshot]
        if "category" in filters:
            snapshot_where += " AND p.category = ?"
            snapshot_parameters.append(filters["category"])
        inventory = query_rows(
            connection,
            """
            SELECT SUM(fi.closing_stock) AS units,
                   SUM(fi.closing_stock * p.cost_price) AS inventory_value,
                   COUNT(DISTINCT CASE WHEN fi.closing_stock <= p.reorder_level
                                  THEN p.product_id END) AS below_reorder_skus
            FROM fact_inventory fi
            JOIN dim_product p ON p.product_id = fi.product_id
            """ + snapshot_where,
            snapshot_parameters,
        )[0]
        inventory_by_category = query_rows(
            connection,
            """
            SELECT p.category AS name, SUM(fi.closing_stock) AS units,
                   SUM(fi.closing_stock * p.cost_price) AS inventory_value,
                   SUM(fi.units_sold) AS units_sold
            FROM fact_inventory fi
            JOIN dim_product p ON p.product_id = fi.product_id
            WHERE fi.snapshot_date = ?
            """ + (" AND p.category = ?" if "category" in filters else "") + """
            GROUP BY p.category ORDER BY inventory_value DESC
            """,
            snapshot_parameters,
        )
        alerts = query_rows(
            connection,
            """
            SELECT p.product_id, p.product_name AS name, p.category,
                   fi.closing_stock AS stock, p.reorder_level
            FROM fact_inventory fi
            JOIN dim_product p ON p.product_id = fi.product_id
            WHERE fi.snapshot_date = ? AND fi.closing_stock <= p.reorder_level
            """ + (" AND p.category = ?" if "category" in filters else "") + """
            ORDER BY fi.closing_stock - p.reorder_level LIMIT 10
            """,
            snapshot_parameters,
        )

        customer_dimension_count = query_rows(
            connection, "SELECT COUNT(*) AS total FROM dim_customer"
        )[0]["total"]
        order_date_range = query_rows(
            connection,
            "SELECT MIN(order_date) AS start_date, MAX(order_date) AS end_date FROM fact_orders",
        )[0]
        metrics = {
            **row,
            **repeat_rows,
            **returned_rows,
            "inventory_units": inventory["units"],
            "inventory_value": inventory["inventory_value"],
            "below_reorder_skus": inventory["below_reorder_skus"],
            "profit_margin_pct": (
                100 * row["line_profit"] / row["net_sales"] if row["net_sales"] else 0
            ),
            "average_order_value": row["net_sales"] / row["orders"] if row["orders"] else 0,
            "average_discount_pct": (
                100 * row["discounts"] / row["gross_sales"] if row["gross_sales"] else 0
            ),
            "repeat_customer_rate_pct": (
                100 * repeat_rows["repeat_customers"] / repeat_rows["customers_with_orders"]
                if repeat_rows["customers_with_orders"] else 0
            ),
            "one_time_customer_rate_pct": (
                100 * repeat_rows["one_time_customers"] / repeat_rows["customers_with_orders"]
                if repeat_rows["customers_with_orders"] else 0
            ),
            "return_rate_pct": (
                100 * returned_rows["returned_units"] / row["units"] if row["units"] else 0
            ),
            "refund_adjusted_profit": (
                (row["line_profit"] or 0) - (returned_rows["refunds"] or 0)
            ),
            "refund_adjusted_margin_pct": (
                100 * ((row["line_profit"] or 0) - (returned_rows["refunds"] or 0))
                / row["net_sales"] if row["net_sales"] else 0
            ),
        }
        return {
            "filters": filters,
            "options": options,
            "metrics": metrics,
            "monthly": monthly,
            "regions": regions,
            "categories": categories,
            "channels": channels,
            "products": products,
            "segments": segments,
            "discounts": discounts,
            "returns_by_reason": return_reasons,
            "targets": {
                **targets,
                "actual_net_sales": target_actuals["net_sales"],
                "actual_line_profit": target_actuals["line_profit"],
                "actual_orders": target_actuals["orders"],
                "sales_achievement_pct": (
                    100 * target_actuals["net_sales"] / targets["sales_target"]
                    if targets["sales_target"] else None
                ),
            },
            "inventory": {
                **inventory,
                "snapshot_date": snapshot,
                "by_category": inventory_by_category,
                "alerts": alerts,
            },
            "metadata": {
                "database": "data/ecommerce_analytics.db",
                "order_date_start": order_date_range["start_date"],
                "order_date_end": order_date_range["end_date"],
                "customer_dimension_rows": customer_dimension_count,
                "targets_filters": "Year, region, and category only; target data has no channel or customer segment.",
                "inventory_filters": "Snapshot date follows the selected year; inventory data has no region, channel, or customer segment.",
                "profit_definition": "Line-item net sales less line-item cost; refund-adjusted profit is shown separately.",
            },
        }


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/dashboard":
            if parsed.path == "/":
                self.path = "/index.html"
            super().do_GET()
            return
        query = parse_qs(parsed.query, keep_blank_values=False)
        filters = {key: values[0] for key, values in query.items() if values}
        try:
            data = get_dashboard_data(filters)
            body = json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
        except (ValueError, sqlite3.Error, FileNotFoundError) as error:
            body = json.dumps({"error": str(error)}).encode("utf-8")
            self.send_response(400 if isinstance(error, ValueError) else 500)
        else:
            self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    print(f"Dashboard available at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down dashboard server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
