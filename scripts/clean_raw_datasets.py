"""Clean the defect-injected CSV inputs into validated warehouse tables."""

import csv
import json
import os
import statistics
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
CLEANED_DIR = ROOT / "data" / "cleaned"
CENT = Decimal("0.01")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with temporary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def money(value: Decimal) -> str:
    return str(value.quantize(CENT, rounding=ROUND_HALF_UP))


def parse_order_date(value: str) -> str:
    value = value.strip()
    formats = ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y")
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Unsupported order date: {value!r}")


def clean() -> dict[str, object]:
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    audit: dict[str, object] = {"sources": {}, "generated_clean_sources": {}}

    raw_products = read_csv(RAW_DIR / "raw_products_with_defects.csv")
    categories = read_csv(CLEANED_DIR / "dim_category.csv")
    category_names = {
        row["category_name"].strip().casefold(): row["category_name"].strip()
        for row in categories
    }
    subcategory_names = {
        row["sub_category_name"].strip().casefold(): row["sub_category_name"].strip()
        for row in categories
    }
    products: dict[str, dict[str, object]] = {}
    product_corrections = Counter()
    for row in raw_products:
        product_id = row["product_id"].strip()
        name = " ".join(row["product_name"].split())
        brand = row["brand"].strip()
        if not brand:
            brand = name.split(" ", 1)[0]
            product_corrections["brand_inferred_from_product_name"] += 1
        raw_category = row["category"].strip().casefold()
        if raw_category not in category_names:
            raise ValueError(f"Unknown product category for {product_id}: {raw_category}")
        category = category_names[raw_category]
        subcategory = subcategory_names.get(row["sub_category"].strip().casefold())
        if subcategory is None:
            raise ValueError(f"Unknown sub-category for product {product_id}")
        cost = Decimal(row["cost_price"])
        price = Decimal(row["selling_price"])
        if cost < 0:
            cost = abs(cost)
            product_corrections["negative_cost_sign_fixed"] += 1
        if price < 0:
            price = abs(price)
            product_corrections["negative_selling_price_sign_fixed"] += 1
        if price <= cost:
            raise ValueError(f"Selling price must exceed cost for {product_id}")
        if name != row["product_name"]:
            product_corrections["product_name_whitespace_normalized"] += 1
        if category != row["category"]:
            product_corrections["category_capitalization_normalized"] += 1
        products[product_id] = {
            "product_id": product_id,
            "product_name": name,
            "category": category,
            "sub_category": subcategory,
            "brand": brand,
            "cost_price": money(cost),
            "selling_price": money(price),
            "reorder_level": int(row["reorder_level"]),
        }
    product_headers = [
        "product_id", "product_name", "category", "sub_category", "brand",
        "cost_price", "selling_price", "reorder_level",
    ]
    write_csv(CLEANED_DIR / "dim_product.csv", product_headers, list(products.values()))
    audit["sources"]["raw_products_with_defects.csv"] = {
        "raw_rows": len(raw_products),
        "cleaned_rows": len(products),
        "rows_removed": len(raw_products) - len(products),
        "corrections": dict(product_corrections),
        "rows_rejected": 0,
    }

    raw_customers = read_csv(RAW_DIR / "raw_customers_with_defects.csv")
    customers_by_id: dict[str, dict[str, object]] = {}
    customer_duplicates = 0
    customer_missing_ages = 0
    ages = [int(row["age"]) for row in raw_customers if row["age"].strip()]
    if not ages:
        raise ValueError("No non-missing customer ages available for imputation")
    median_age = int(statistics.median(ages))
    customer_corrections = Counter()
    for row in raw_customers:
        customer_id = row["customer_id"].strip()
        if customer_id in customers_by_id:
            customer_duplicates += 1
            continue
        age = row["age"].strip()
        if not age:
            age = str(median_age)
            customer_missing_ages += 1
        name = " ".join(row["customer_name"].split()).title()
        gender = {"M": "Male", "F": "Female", "O": "Other"}.get(
            row["gender"].strip().upper(), row["gender"].strip().title()
        )
        segment = row["customer_segment"].strip().title()
        if name != row["customer_name"]:
            customer_corrections["customer_name_normalized"] += 1
        if gender != row["gender"]:
            customer_corrections["gender_code_normalized"] += 1
        if segment != row["customer_segment"]:
            customer_corrections["customer_segment_normalized"] += 1
        if not row["age"].strip():
            customer_corrections["missing_age_imputed_with_raw_median"] += 1
        customers_by_id[customer_id] = {
            "customer_id": customer_id,
            "customer_name": name,
            "gender": gender,
            "age": age,
            "city": row["city"].strip(),
            "state": row["state"].strip(),
            "region_id": row["region_id"].strip(),
            "customer_segment": segment,
            "customer_since": row["customer_since"].strip(),
        }
    customer_headers = [
        "customer_id", "customer_name", "gender", "age", "city", "state",
        "region_id", "customer_segment", "customer_since",
    ]
    write_csv(
        CLEANED_DIR / "dim_customer.csv",
        customer_headers,
        list(customers_by_id.values()),
    )
    audit["sources"]["raw_customers_with_defects.csv"] = {
        "raw_rows": len(raw_customers),
        "cleaned_rows": len(customers_by_id),
        "rows_removed": customer_duplicates,
        "rows_rejected": 0,
        "age_median_used": median_age,
        "missing_ages_imputed": customer_missing_ages,
        "corrections": dict(customer_corrections),
    }

    raw_orders = read_csv(RAW_DIR / "raw_orders_with_defects.csv")
    orders_by_id: dict[str, dict[str, object]] = {}
    seen_order_ids: set[str] = set()
    duplicate_orders = 0
    missing_customer_orders = 0
    invalid_dates_corrected = 0
    order_corrections = Counter()
    for row in raw_orders:
        order_id = row["order_id"].strip()
        if order_id in seen_order_ids:
            duplicate_orders += 1
            continue
        seen_order_ids.add(order_id)
        customer_id = row["customer_id"].strip()
        if not customer_id or customer_id == "0":
            missing_customer_orders += 1
            continue
        if customer_id not in customers_by_id:
            raise ValueError(f"Unknown customer {customer_id!r} on {order_id}")
        order_date = parse_order_date(row["order_date"])
        if order_date != row["order_date"].strip():
            invalid_dates_corrected += 1
        status = row["order_status"].strip().title()
        if status != row["order_status"]:
            order_corrections["order_status_case_normalized"] += 1
        orders_by_id[order_id] = {
            "order_id": order_id,
            "order_date": order_date,
            "customer_id": customer_id,
            "region_id": row["region_id"].strip(),
            "sales_channel": row["sales_channel"].strip(),
            "payment_method": row["payment_method"].strip(),
            "shipping_mode": row["shipping_mode"].strip(),
            "order_status": status,
        }
    order_headers = [
        "order_id", "order_date", "customer_id", "region_id", "sales_channel",
        "payment_method", "shipping_mode", "order_status",
    ]
    write_csv(
        CLEANED_DIR / "fact_orders.csv", order_headers, list(orders_by_id.values())
    )
    audit["sources"]["raw_orders_with_defects.csv"] = {
        "raw_rows": len(raw_orders),
        "cleaned_rows": len(orders_by_id),
        "duplicate_rows_removed": duplicate_orders,
        "rows_rejected_for_missing_customer_key": missing_customer_orders,
        "rows_removed_total": duplicate_orders + missing_customer_orders,
        "dates_normalized": invalid_dates_corrected,
        "corrections": dict(order_corrections),
    }

    raw_details = read_csv(RAW_DIR / "raw_order_details_with_defects.csv")
    details: list[dict[str, object]] = []
    detail_corrections = Counter()
    seen_details: set[str] = set()
    for row in raw_details:
        order_id = row["order_id"].strip()
        if order_id not in orders_by_id:
            continue
        detail_id = row["order_detail_id"].strip()
        if not detail_id or detail_id in seen_details:
            raise ValueError(f"Missing or duplicate order detail ID: {detail_id!r}")
        seen_details.add(detail_id)
        quantity = int(row["quantity"])
        if quantity < 0:
            quantity = abs(quantity)
            detail_corrections["negative_quantities_sign_fixed"] += 1
        if quantity == 0:
            raise ValueError(f"Zero quantity for detail {detail_id}")
        discount_text = row["discount_rate"].strip()
        if discount_text.endswith("%"):
            discount = Decimal(discount_text[:-1]) / Decimal(100)
            detail_corrections["text_percent_discounts_normalized"] += 1
        else:
            discount = Decimal(discount_text)
        if not Decimal(0) <= discount <= Decimal(1):
            raise ValueError(f"Out-of-range discount for detail {detail_id}")
        product = products.get(row["product_id"].strip())
        if product is None:
            raise ValueError(f"Unknown product for detail {detail_id}")
        unit_price = Decimal(row["unit_price"])
        if unit_price != Decimal(str(product["selling_price"])):
            raise ValueError(f"Unit price does not match product for detail {detail_id}")
        gross = (Decimal(quantity) * unit_price).quantize(CENT, rounding=ROUND_HALF_UP)
        discount_amount = (gross * discount).quantize(CENT, rounding=ROUND_HALF_UP)
        net = gross - discount_amount
        cost = (
            Decimal(quantity) * Decimal(str(product["cost_price"]))
        ).quantize(CENT, rounding=ROUND_HALF_UP)
        profit = net - cost
        if Decimal(row["gross_sales"]) == 0 and gross != 0:
            detail_corrections["zero_gross_sales_recalculated"] += 1
        details.append({
            "order_detail_id": detail_id,
            "order_id": order_id,
            "product_id": product["product_id"],
            "quantity": quantity,
            "unit_price": money(unit_price),
            "discount_rate": str(discount),
            "gross_sales": money(gross),
            "discount_amount": money(discount_amount),
            "net_sales": money(net),
            "total_cost": money(cost),
            "net_profit": money(profit),
        })
    detail_headers = [
        "order_detail_id", "order_id", "product_id", "quantity", "unit_price",
        "discount_rate", "gross_sales", "discount_amount", "net_sales",
        "total_cost", "net_profit",
    ]
    write_csv(CLEANED_DIR / "fact_order_details.csv", detail_headers, details)
    audit["sources"]["raw_order_details_with_defects.csv"] = {
        "raw_rows": len(raw_details),
        "cleaned_rows": len(details),
        "rows_removed_with_rejected_parent_orders": len(raw_details) - len(details),
        "corrections": dict(detail_corrections),
    }

    return_source = ROOT / "data" / "source" / "fact_returns_generated.csv"
    returns = read_csv(return_source)
    clean_detail_ids = {str(row["order_detail_id"]) for row in details}
    retained_returns = [
        row for row in returns
        if row["order_id"] in orders_by_id and row["order_detail_id"] in clean_detail_ids
    ]
    write_csv(
        CLEANED_DIR / "fact_returns.csv",
        list(returns[0].keys()) if returns else [
            "return_id", "order_id", "order_detail_id", "product_id",
            "return_date", "return_reason", "return_quantity", "refund_amount",
        ],
        retained_returns,
    )
    audit["generated_clean_sources"] = {
        "fact_returns.csv": {
            "source": "Generated as clean synthetic data; filtered to retained order lines.",
            "source_file": "data/source/fact_returns_generated.csv",
            "source_rows": len(returns),
            "cleaned_rows": len(retained_returns),
            "rows_removed_with_rejected_parent_orders": len(returns) - len(retained_returns),
        },
        "fact_inventory.csv": {
            "source": "Generated directly as clean synthetic data; no defect-injected raw counterpart.",
            "cleaned_rows": sum(1 for _ in read_csv(CLEANED_DIR / "fact_inventory.csv")),
        },
        "fact_sales_targets.csv": {
            "source": "Generated directly as clean synthetic data; no defect-injected raw counterpart.",
            "cleaned_rows": sum(1 for _ in read_csv(CLEANED_DIR / "fact_sales_targets.csv")),
        },
    }

    required_ids = set(orders_by_id)
    if any(row["order_id"] not in required_ids for row in details):
        raise ValueError("A cleaned order line has no retained parent order")
    if any(row["customer_id"] not in customers_by_id for row in orders_by_id.values()):
        raise ValueError("A cleaned order has no retained customer")
    if any(row["product_id"] not in products for row in details):
        raise ValueError("A cleaned order line has no product")
    for row in orders_by_id.values():
        date.fromisoformat(str(row["order_date"]))

    audit_path = CLEANED_DIR / "cleaning_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return audit


if __name__ == "__main__":
    summary = clean()
    print(json.dumps(summary, indent=2))
