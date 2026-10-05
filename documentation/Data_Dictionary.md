# Data Dictionary

The warehouse is synthetic. Declared types below follow `sql/02_create_tables.sql`; SQLite stores values using its dynamic type system. Current row counts are from the checked-in warehouse.

## Dimensions

| Table | Rows | Key | Columns |
| --- | ---: | --- | --- |
| `dim_date` | 1,096 | `full_date` | `date_key`, `year`, `quarter`, `month_num`, `month_name`, `week_num`, `day_num`, `day_name`, `is_weekend` |
| `dim_region` | 4 | `region_id` | `region_name`, `country`, `regional_manager` |
| `dim_category` | 15 | `sub_category_id` | `sub_category_name`, `category_name` |
| `dim_product` | 500 | `product_id` | `product_name`, `category`, `sub_category`, `brand`, `cost_price`, `selling_price`, `reorder_level` |
| `dim_customer` | 8,000 | `customer_id` | `customer_name`, `gender`, `age`, `city`, `state`, `region_id`, `customer_segment`, `customer_since` |

## Facts

| Table | Rows | Key | Grain and important columns |
| --- | ---: | --- | --- |
| `fact_orders` | 51,180 | `order_id` | One order header: `order_date`, `customer_id`, `region_id`, `sales_channel`, `payment_method`, `shipping_mode`, `order_status` |
| `fact_order_details` | 104,673 | `order_detail_id` | One product line per order: `order_id`, `product_id`, `quantity`, `unit_price`, `discount_rate`, `gross_sales`, `discount_amount`, `net_sales`, `total_cost`, `net_profit` |
| `fact_returns` | 2,983 | `return_id` | One return incident: order and line keys, product, `return_date`, `return_reason`, `return_quantity`, `refund_amount` |
| `fact_inventory` | 18,000 | `inventory_id` | One product/month snapshot: `snapshot_date`, `opening_stock`, `units_received`, `units_sold`, `closing_stock`, `stock_status` |
| `fact_sales_targets` | 576 | `target_id` | One month/region/category target: `year_month`, `region_id`, `category_name`, `sales_target`, `profit_target`, `order_target` |

## Relationships and interpretation

- Orders reference the date, customer, and region dimensions.
- Order lines reference orders and products.
- Returns reference orders, order lines, and products.
- Inventory references products; inventory is a snapshot and has no region/channel/segment key.
- Targets reference regions and store a month string and category label; they do not contain sales channel or customer segment.
- `dim_product` stores category and sub-category labels directly. `dim_category` is a separate lookup by sub-category, not a foreign-key column on `dim_product`.
- Financial fields are stored at order-line grain. `net_profit` means `net_sales - total_cost`, before refunds and operating expenses.
