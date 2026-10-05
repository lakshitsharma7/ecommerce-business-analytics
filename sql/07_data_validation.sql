-- Project data validation queries (SQLite).
-- Repeat-customer rate = customers with at least 2 distinct orders /
-- customers with at least 1 distinct order. Customer rows with no orders
-- are excluded from this rate; one-time customers remain in its denominator.

SELECT
    (SELECT COUNT(*) FROM dim_customer) AS customer_dimension_rows,
    COUNT(*) AS customers_with_orders,
    SUM(CASE WHEN order_count = 1 THEN 1 ELSE 0 END) AS one_time_customers,
    SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END) AS repeat_customers,
    ROUND(
        100.0 * SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        4
    ) AS repeat_customer_rate_pct,
    ROUND(
        100.0 * SUM(CASE WHEN order_count = 1 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        4
    ) AS one_time_customer_rate_pct
FROM (
    SELECT customer_id, COUNT(DISTINCT order_id) AS order_count
    FROM fact_orders
    GROUP BY customer_id
);

SELECT
    'dim_customer' AS table_name,
    COUNT(*) AS row_count
FROM dim_customer
UNION ALL SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL SELECT 'fact_orders', COUNT(*) FROM fact_orders
UNION ALL SELECT 'fact_order_details', COUNT(*) FROM fact_order_details
UNION ALL SELECT 'fact_returns', COUNT(*) FROM fact_returns
UNION ALL SELECT 'fact_inventory', COUNT(*) FROM fact_inventory
UNION ALL SELECT 'fact_sales_targets', COUNT(*) FROM fact_sales_targets;

SELECT
    ROUND(SUM(gross_sales), 2) AS gross_sales,
    ROUND(SUM(discount_amount), 2) AS discounts,
    ROUND(SUM(net_sales), 2) AS net_sales,
    ROUND(SUM(total_cost), 2) AS cost_of_goods_sold,
    ROUND(SUM(net_profit), 2) AS line_item_profit,
    ROUND(100.0 * SUM(net_profit) / NULLIF(SUM(net_sales), 0), 4) AS line_item_margin_pct
FROM fact_order_details;

SELECT
    (SELECT COUNT(*) FROM fact_orders WHERE customer_id IS NULL) AS missing_order_customer_keys,
    (SELECT COUNT(*) FROM fact_order_details WHERE quantity <= 0) AS invalid_line_quantities,
    (SELECT COUNT(*) FROM fact_order_details WHERE discount_rate NOT BETWEEN 0 AND 1) AS invalid_discounts,
    (SELECT COUNT(*) FROM pragma_foreign_key_check) AS foreign_key_violations;
