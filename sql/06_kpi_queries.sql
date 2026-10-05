-- ==============================================================================
-- 06_kpi_queries.sql
-- PROJECT: E-Commerce Sales, Customer & Business Performance Analytics
-- DESCRIPTION: Materialized Views & High-Frequency KPI Reporting Queries
-- ==============================================================================

-- 1. View: Monthly Executive Performance Summary
DROP VIEW IF EXISTS vw_monthly_executive_kpis;
CREATE VIEW vw_monthly_executive_kpis AS
SELECT 
    dd.year,
    dd.month_num,
    dd.month_name,
    COUNT(DISTINCT fo.order_id) AS total_orders,
    SUM(fod.quantity) AS total_quantity_sold,
    ROUND(SUM(fod.gross_sales), 2) AS gross_revenue,
    ROUND(SUM(fod.discount_amount), 2) AS total_discount_cost,
    ROUND(SUM(fod.net_sales), 2) AS net_revenue,
    ROUND(SUM(fod.total_cost), 2) AS total_cogs,
    ROUND(SUM(fod.net_profit), 2) AS net_profit,
    ROUND(100.0 * SUM(fod.net_profit) / NULLIF(SUM(fod.net_sales), 0), 2) AS profit_margin_pct,
    ROUND(SUM(fod.net_sales) / NULLIF(COUNT(DISTINCT fo.order_id), 0), 2) AS average_order_value
FROM fact_order_details fod
JOIN fact_orders fo ON fod.order_id = fo.order_id
JOIN dim_date dd ON fo.order_date = dd.full_date
GROUP BY dd.year, dd.month_num, dd.month_name;


-- 2. View: Regional & Category Target Achievement
DROP VIEW IF EXISTS vw_regional_target_achievement;
CREATE VIEW vw_regional_target_achievement AS
WITH actuals AS (
    SELECT 
        SUBSTR(fo.order_date, 1, 7) AS year_month,
        fo.region_id,
        dp.category,
        ROUND(SUM(fod.net_sales), 2) AS actual_sales,
        ROUND(SUM(fod.net_profit), 2) AS actual_profit
    FROM fact_orders fo
    JOIN fact_order_details fod ON fo.order_id = fod.order_id
    JOIN dim_product dp ON fod.product_id = dp.product_id
    GROUP BY SUBSTR(fo.order_date, 1, 7), fo.region_id, dp.category
)
SELECT 
    fst.year_month,
    dr.region_name,
    dr.regional_manager,
    fst.category_name,
    fst.sales_target,
    COALESCE(a.actual_sales, 0) AS actual_sales,
    ROUND(COALESCE(a.actual_sales, 0) - fst.sales_target, 2) AS sales_variance,
    ROUND(100.0 * COALESCE(a.actual_sales, 0) / NULLIF(fst.sales_target, 0), 2) AS sales_achievement_pct,
    fst.profit_target,
    COALESCE(a.actual_profit, 0) AS actual_profit,
    ROUND(100.0 * COALESCE(a.actual_profit, 0) / NULLIF(fst.profit_target, 0), 2) AS profit_achievement_pct
FROM fact_sales_targets fst
JOIN dim_region dr ON fst.region_id = dr.region_id
LEFT JOIN actuals a ON fst.year_month = a.year_month 
                   AND fst.region_id = a.region_id 
                   AND fst.category_name = a.category;


-- 3. View: Customer RFM Segmentation Matrix
DROP VIEW IF EXISTS vw_customer_rfm_segments;
CREATE VIEW vw_customer_rfm_segments AS
WITH customer_rfm_raw AS (
    SELECT 
        fo.customer_id,
        MAX(fo.order_date) AS last_order_date,
        CAST((JULIANDAY('2025-12-31') - JULIANDAY(MAX(fo.order_date))) AS INT) AS recency_days,
        COUNT(DISTINCT fo.order_id) AS frequency,
        ROUND(SUM(fod.net_sales), 2) AS monetary_value
    FROM fact_orders fo
    JOIN fact_order_details fod ON fo.order_id = fod.order_id
    GROUP BY fo.customer_id
),
rfm_scores AS (
    SELECT 
        customer_id,
        recency_days,
        frequency,
        monetary_value,
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(4) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(4) OVER (ORDER BY monetary_value ASC) AS m_score
    FROM customer_rfm_raw
)
SELECT 
    customer_id,
    recency_days,
    frequency,
    monetary_value,
    (r_score + f_score + m_score) AS composite_rfm_score,
    CASE 
        WHEN (r_score >= 3 AND f_score >= 3 AND m_score >= 3) THEN 'Champions (VIP)'
        WHEN (r_score >= 3 AND f_score >= 2) THEN 'Loyal Active Buyers'
        WHEN (r_score >= 3 AND f_score = 1) THEN 'New / Recent Prospects'
        WHEN (r_score <= 2 AND f_score >= 3) THEN 'At-Risk High-Value Customers'
        ELSE 'Hibernating / Churned'
    END AS rfm_segment
FROM rfm_scores;
