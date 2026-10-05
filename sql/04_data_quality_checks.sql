-- ==============================================================================
-- 04_data_quality_checks.sql
-- PROJECT: E-Commerce Sales, Customer & Business Performance Analytics
-- DESCRIPTION: Automated Data Integrity, Constraint, and Anomaly Audit Suite
-- ==============================================================================

-- 1. Check for Duplicate Primary Keys in Orders
SELECT 
    order_id, 
    COUNT(*) AS duplicate_count
FROM fact_orders
GROUP BY order_id
HAVING COUNT(*) > 1;

-- 2. Check for Orphaned Orders (Customer ID not in Dim Customer)
SELECT 
    COUNT(*) AS orphaned_orders_count
FROM fact_orders fo
LEFT JOIN dim_customer dc ON fo.customer_id = dc.customer_id
WHERE dc.customer_id IS NULL;

-- 3. Check for Orphaned Order Details (Product ID not in Dim Product)
SELECT 
    COUNT(*) AS orphaned_details_count
FROM fact_order_details fod
LEFT JOIN dim_product dp ON fod.product_id = dp.product_id
WHERE dp.product_id IS NULL;

-- 4. Check for Invalid Dates in Orders (Orders outside calendar range)
SELECT 
    COUNT(*) AS invalid_date_orders
FROM fact_orders fo
LEFT JOIN dim_date dd ON fo.order_date = dd.full_date
WHERE dd.full_date IS NULL;

-- 5. Check for Negative or Zero Quantities
SELECT 
    COUNT(*) AS negative_quantity_count
FROM fact_order_details
WHERE quantity <= 0;

-- 6. Check for Invalid Unit Selling Prices or Costs
SELECT 
    COUNT(*) AS invalid_price_count
FROM fact_order_details
WHERE unit_price <= 0 OR total_cost < 0;

-- 7. Check for Out-of-Bounds Discounts (< 0% or > 100%)
SELECT 
    COUNT(*) AS invalid_discount_count
FROM fact_order_details
WHERE discount_rate < 0.00 OR discount_rate > 1.00;

-- 8. Check for Return Quantities Exceeding Purchased Quantities
SELECT 
    fr.return_id,
    fr.order_detail_id,
    fr.return_quantity,
    fod.quantity AS original_quantity
FROM fact_returns fr
JOIN fact_order_details fod ON fr.order_detail_id = fod.order_detail_id
WHERE fr.return_quantity > fod.quantity;

-- 9. Check for Inventory Closing Stock Inconsistencies
-- (Closing Stock should equal Opening + Received - Sold)
SELECT 
    inventory_id,
    product_id,
    snapshot_date,
    opening_stock,
    units_received,
    units_sold,
    closing_stock,
    (opening_stock + units_received - units_sold) AS calculated_closing_stock
FROM fact_inventory
WHERE closing_stock <> (opening_stock + units_received - units_sold);

-- 10. Master Data Quality Health Scorecard
SELECT 
    'fact_orders' AS entity_name,
    COUNT(*) AS total_records,
    SUM(CASE WHEN customer_id IS NOT NULL AND order_date IS NOT NULL THEN 1 ELSE 0 END) AS valid_records,
    SUM(CASE WHEN customer_id IS NULL OR order_date IS NULL THEN 1 ELSE 0 END) AS invalid_records,
    ROUND(100.0 * SUM(CASE WHEN customer_id IS NOT NULL AND order_date IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS data_quality_score_pct
FROM fact_orders
UNION ALL
SELECT 
    'fact_order_details',
    COUNT(*),
    SUM(CASE WHEN quantity > 0 AND unit_price > 0 AND discount_rate BETWEEN 0 AND 1 THEN 1 ELSE 0 END),
    SUM(CASE WHEN quantity <= 0 OR unit_price <= 0 OR discount_rate NOT BETWEEN 0 AND 1 THEN 1 ELSE 0 END),
    ROUND(100.0 * SUM(CASE WHEN quantity > 0 AND unit_price > 0 AND discount_rate BETWEEN 0 AND 1 THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM fact_order_details
UNION ALL
SELECT 
    'dim_customer',
    COUNT(*),
    SUM(CASE WHEN customer_id IS NOT NULL AND age BETWEEN 18 AND 100 THEN 1 ELSE 0 END),
    SUM(CASE WHEN customer_id IS NULL OR age NOT BETWEEN 18 AND 100 THEN 1 ELSE 0 END),
    ROUND(100.0 * SUM(CASE WHEN customer_id IS NOT NULL AND age BETWEEN 18 AND 100 THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM dim_customer;
