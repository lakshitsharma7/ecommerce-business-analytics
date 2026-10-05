-- ==============================================================================
-- 05_business_analysis.sql
-- PROJECT: E-Commerce Sales, Customer & Business Performance Analytics
-- DESCRIPTION: 30+ Advanced Business Analytical SQL Queries
-- TECHNIQUES: CTEs, Window Functions (LAG, LEAD, RANK, DENSE_RANK, SUM OVER), 
--             Customer Cohorts, RFM Scoring, Margin Elasticity, and Pareto 80/20.
-- ==============================================================================

-- ==============================================================================
-- DOMAIN 1: OVERALL REVENUE & GROWTH DYNAMICS (Queries 1 - 6)
-- ==============================================================================

-- QUERY 1: Monthly Enterprise Revenue, COGS, Profit, and Profit Margin %
-- Business Question: How has revenue and profit evolved across the 36-month timeline?
SELECT 
    dd.year,
    dd.month_num,
    dd.month_name,
    COUNT(DISTINCT fo.order_id) AS total_orders,
    SUM(fod.quantity) AS total_units_sold,
    ROUND(SUM(fod.gross_sales), 2) AS gross_sales,
    ROUND(SUM(fod.discount_amount), 2) AS total_discounts,
    ROUND(SUM(fod.net_sales), 2) AS net_revenue,
    ROUND(SUM(fod.total_cost), 2) AS total_cogs,
    ROUND(SUM(fod.net_profit), 2) AS net_profit,
    ROUND(100.0 * SUM(fod.net_profit) / NULLIF(SUM(fod.net_sales), 0), 2) AS profit_margin_pct
FROM fact_order_details fod
JOIN fact_orders fo ON fod.order_id = fo.order_id
JOIN dim_date dd ON fo.order_date = dd.full_date
GROUP BY dd.year, dd.month_num, dd.month_name
ORDER BY dd.year, dd.month_num;


-- QUERY 2: Month-over-Month (MoM) Revenue & Profit Growth using LAG() Window Function
-- Business Question: What is the monthly rate of revenue expansion and margin acceleration?
WITH monthly_metrics AS (
    SELECT 
        dd.year,
        dd.month_num,
        dd.month_name,
        ROUND(SUM(fod.net_sales), 2) AS current_net_sales,
        ROUND(SUM(fod.net_profit), 2) AS current_net_profit
    FROM fact_order_details fod
    JOIN fact_orders fo ON fod.order_id = fo.order_id
    JOIN dim_date dd ON fo.order_date = dd.full_date
    GROUP BY dd.year, dd.month_num, dd.month_name
)
SELECT 
    year,
    month_num,
    month_name,
    current_net_sales,
    LAG(current_net_sales, 1) OVER (ORDER BY year, month_num) AS prev_month_sales,
    ROUND(100.0 * (current_net_sales - LAG(current_net_sales, 1) OVER (ORDER BY year, month_num)) 
          / NULLIF(LAG(current_net_sales, 1) OVER (ORDER BY year, month_num), 0), 2) AS mom_sales_growth_pct,
    current_net_profit,
    LAG(current_net_profit, 1) OVER (ORDER BY year, month_num) AS prev_month_profit,
    ROUND(100.0 * (current_net_profit - LAG(current_net_profit, 1) OVER (ORDER BY year, month_num)) 
          / NULLIF(LAG(current_net_profit, 1) OVER (ORDER BY year, month_num), 0), 2) AS mom_profit_growth_pct
FROM monthly_metrics
ORDER BY year, month_num;


-- QUERY 3: Year-over-Year (YoY) Performance & Annual Expansion
-- Business Question: How do full fiscal year revenues and profit margins compare across 2023, 2024, and 2025?
WITH annual_summary AS (
    SELECT 
        dd.year,
        COUNT(DISTINCT fo.order_id) AS annual_orders,
        ROUND(SUM(fod.net_sales), 2) AS annual_net_sales,
        ROUND(SUM(fod.net_profit), 2) AS annual_net_profit,
        ROUND(100.0 * SUM(fod.net_profit) / NULLIF(SUM(fod.net_sales), 0), 2) AS annual_margin_pct
    FROM fact_order_details fod
    JOIN fact_orders fo ON fod.order_id = fo.order_id
    JOIN dim_date dd ON fo.order_date = dd.full_date
    GROUP BY dd.year
)
SELECT 
    year,
    annual_orders,
    annual_net_sales,
    LAG(annual_net_sales, 1) OVER (ORDER BY year) AS prev_year_sales,
    ROUND(100.0 * (annual_net_sales - LAG(annual_net_sales, 1) OVER (ORDER BY year)) 
          / NULLIF(LAG(annual_net_sales, 1) OVER (ORDER BY year), 0), 2) AS yoy_sales_growth_pct,
    annual_net_profit,
    LAG(annual_net_profit, 1) OVER (ORDER BY year) AS prev_year_profit,
    ROUND(100.0 * (annual_net_profit - LAG(annual_net_profit, 1) OVER (ORDER BY year)) 
          / NULLIF(LAG(annual_net_profit, 1) OVER (ORDER BY year), 0), 2) AS yoy_profit_growth_pct,
    annual_margin_pct
FROM annual_summary
ORDER BY year;


-- QUERY 4: Cumulative Running Total Revenue & Running Profit by Year using SUM() OVER
-- Business Question: What is the cumulative revenue pacing within each fiscal year?
WITH monthly_base AS (
    SELECT 
        dd.year,
        dd.month_num,
        dd.month_name,
        ROUND(SUM(fod.net_sales), 2) AS month_sales,
        ROUND(SUM(fod.net_profit), 2) AS month_profit
    FROM fact_order_details fod
    JOIN fact_orders fo ON fod.order_id = fo.order_id
    JOIN dim_date dd ON fo.order_date = dd.full_date
    GROUP BY dd.year, dd.month_num, dd.month_name
)
SELECT 
    year,
    month_num,
    month_name,
    month_sales,
    ROUND(SUM(month_sales) OVER (PARTITION BY year ORDER BY month_num ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_annual_sales,
    month_profit,
    ROUND(SUM(month_profit) OVER (PARTITION BY year ORDER BY month_num ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_annual_profit
FROM monthly_base
ORDER BY year, month_num;


-- QUERY 5: 3-Month Moving Average of Net Revenue (Smoothing Seasonality)
-- Business Question: What is the underlying moving revenue trend when dampening monthly volatility?
WITH monthly_revenue AS (
    SELECT 
        dd.year,
        dd.month_num,
        ROUND(SUM(fod.net_sales), 2) AS monthly_sales
    FROM fact_order_details fod
    JOIN fact_orders fo ON fod.order_id = fo.order_id
    JOIN dim_date dd ON fo.order_date = dd.full_date
    GROUP BY dd.year, dd.month_num
)
SELECT 
    year,
    month_num,
    monthly_sales,
    ROUND(AVG(monthly_sales) OVER (ORDER BY year, month_num ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m
FROM monthly_revenue
ORDER BY year, month_num;


-- QUERY 6: Day of Week & Weekend Performance Diagnostics
-- Business Question: Does sales volume skew heavily towards weekdays or weekends?
SELECT 
    dd.day_name,
    dd.is_weekend,
    COUNT(DISTINCT fo.order_id) AS total_orders,
    ROUND(SUM(fod.net_sales), 2) AS total_net_revenue,
    ROUND(AVG(fod.net_sales), 2) AS avg_line_value,
    ROUND(100.0 * SUM(fod.net_profit) / NULLIF(SUM(fod.net_sales), 0), 2) AS profit_margin_pct
FROM fact_order_details fod
JOIN fact_orders fo ON fod.order_id = fo.order_id
JOIN dim_date dd ON fo.order_date = dd.full_date
GROUP BY dd.day_name, dd.is_weekend
ORDER BY total_net_revenue DESC;


-- ==============================================================================
-- DOMAIN 2: CUSTOMER BEHAVIOR, RETENTION & RFM SEGMENTATION (Queries 7 - 13)
-- ==============================================================================

-- QUERY 7: Customer Order Frequency Distribution (One-Time vs Repeat Buyers)
-- Business Question: What proportion of our customer base are repeat buyers versus one-and-done?
WITH customer_order_counts AS (
    SELECT 
        fo.customer_id,
        COUNT(DISTINCT fo.order_id) AS total_orders,
        SUM(fod.net_sales) AS total_customer_spend
    FROM fact_orders fo
    JOIN fact_order_details fod ON fo.order_id = fod.order_id
    GROUP BY fo.customer_id
)
SELECT 
    CASE 
        WHEN total_orders = 1 THEN '1 Order (One-Time)'
        WHEN total_orders = 2 THEN '2 Orders (Repeat)'
        WHEN total_orders BETWEEN 3 AND 5 THEN '3-5 Orders (Loyal)'
        ELSE '6+ Orders (VIP Super-User)'
    END AS customer_loyalty_segment,
    COUNT(*) AS total_customers,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM customer_order_counts), 2) AS customer_share_pct,
    ROUND(SUM(total_customer_spend), 2) AS total_revenue_generated,
    ROUND(100.0 * SUM(total_customer_spend) / (SELECT SUM(total_customer_spend) FROM customer_order_counts), 2) AS revenue_contribution_pct,
    ROUND(AVG(total_customer_spend), 2) AS avg_spend_per_customer
FROM customer_order_counts
GROUP BY 1
ORDER BY total_revenue_generated DESC;


-- QUERY 8: New vs. Returning Customers Monthly Velocity
-- Business Question: How many first-time customers vs returning customers make purchases each month?
WITH customer_first_order AS (
    SELECT 
        customer_id,
        MIN(order_date) AS first_order_date
    FROM fact_orders
    GROUP BY customer_id
),
order_classification AS (
    SELECT 
        fo.order_id,
        fo.order_date,
        fo.customer_id,
        fod.net_sales,
        CASE 
            WHEN fo.order_date = cfo.first_order_date THEN 'New Customer'
            ELSE 'Returning Customer'
        END AS customer_type
    FROM fact_orders fo
    JOIN customer_first_order cfo ON fo.customer_id = cfo.customer_id
    JOIN fact_order_details fod ON fo.order_id = fod.order_id
)
SELECT 
    SUBSTR(order_date, 1, 7) AS year_month,
    COUNT(DISTINCT CASE WHEN customer_type = 'New Customer' THEN customer_id END) AS new_customers,
    COUNT(DISTINCT CASE WHEN customer_type = 'Returning Customer' THEN customer_id END) AS returning_customers,
    ROUND(SUM(CASE WHEN customer_type = 'New Customer' THEN net_sales ELSE 0 END), 2) AS new_customer_revenue,
    ROUND(SUM(CASE WHEN customer_type = 'Returning Customer' THEN net_sales ELSE 0 END), 2) AS returning_customer_revenue,
    ROUND(100.0 * SUM(CASE WHEN customer_type = 'Returning Customer' THEN net_sales ELSE 0 END) 
          / NULLIF(SUM(net_sales), 0), 2) AS returning_revenue_share_pct
FROM order_classification
GROUP BY SUBSTR(order_date, 1, 7)
ORDER BY year_month;


-- QUERY 9: RFM (Recency, Frequency, Monetary) Customer Scoring
-- Business Question: How can we segment customers into actionable marketing tiers (Champions, Loyal, At-Risk, Lost)?
WITH customer_rfm_raw AS (
    SELECT 
        fo.customer_id,
        MAX(fo.order_date) AS last_order_date,
        -- Days since 2025-12-31 (Project Cutoff Reference Date)
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
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score, -- Higher score = more recent
        NTILE(4) OVER (ORDER BY frequency ASC) AS f_score,     -- Higher score = more frequent
        NTILE(4) OVER (ORDER BY monetary_value ASC) AS m_score -- Higher score = higher spend
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
FROM rfm_scores
ORDER BY monetary_value DESC
LIMIT 50;


-- QUERY 10: Customer Lifetime Value (LTV) Decile Breakdown
-- Business Question: What is the revenue distribution across customer wealth deciles?
WITH customer_spend AS (
    SELECT 
        dc.customer_id,
        dc.customer_name,
        dc.customer_segment,
        COUNT(DISTINCT fo.order_id) AS lifetime_orders,
        ROUND(SUM(fod.net_sales), 2) AS lifetime_net_spend,
        ROUND(SUM(fod.net_profit), 2) AS lifetime_profit_generated
    FROM dim_customer dc
    JOIN fact_orders fo ON dc.customer_id = fo.customer_id
    JOIN fact_order_details fod ON fo.order_id = fod.order_id
    GROUP BY dc.customer_id, dc.customer_name, dc.customer_segment
),
customer_deciles AS (
    SELECT 
        *,
        NTILE(10) OVER (ORDER BY lifetime_net_spend DESC) AS spend_decile
    FROM customer_spend
)
SELECT 
    spend_decile,
    COUNT(*) AS total_customers_in_decile,
    ROUND(MIN(lifetime_net_spend), 2) AS min_spend,
    ROUND(MAX(lifetime_net_spend), 2) AS max_spend,
    ROUND(SUM(lifetime_net_spend), 2) AS total_decile_revenue,
    ROUND(100.0 * SUM(lifetime_net_spend) / (SELECT SUM(lifetime_net_spend) FROM customer_spend), 2) AS decile_revenue_share_pct,
    ROUND(SUM(lifetime_profit_generated), 2) AS total_decile_profit
FROM customer_deciles
GROUP BY spend_decile
ORDER BY spend_decile ASC;


-- QUERY 11: Top 20 Most Profitable Customers (All-Time)
-- Business Question: Who are our single most lucrative accounts?
SELECT 
    dc.customer_id,
    dc.customer_name,
    dc.customer_segment,
    dc.city,
    dr.region_name,
    COUNT(DISTINCT fo.order_id) AS total_orders_placed,
    SUM(fod.quantity) AS total_units_bought,
    ROUND(SUM(fod.net_sales), 2) AS total_net_revenue,
    ROUND(SUM(fod.net_profit), 2) AS total_profit_contributed,
    ROUND(100.0 * SUM(fod.net_profit) / NULLIF(SUM(fod.net_sales), 0), 2) AS customer_margin_pct
FROM dim_customer dc
JOIN dim_region dr ON dc.region_id = dr.region_id
JOIN fact_orders fo ON dc.customer_id = fo.customer_id
JOIN fact_order_details fod ON fo.order_id = fod.order_id
GROUP BY dc.customer_id, dc.customer_name, dc.customer_segment, dc.city, dr.region_name
ORDER BY total_profit_contributed DESC
LIMIT 20;


-- QUERY 12: Customer Demographic Analysis (Age Bracket & Gender Performance)
-- Business Question: Which demographic cohorts generate the strongest basket sizes and margins?
SELECT 
    CASE 
        WHEN dc.age < 25 THEN '18-24 (Gen Z)'
        WHEN dc.age < 35 THEN '25-34 (Young Pros)'
        WHEN dc.age < 50 THEN '35-49 (Mid-Career)'
        ELSE '50+ (Mature)'
    END AS age_cohort,
    dc.gender,
    COUNT(DISTINCT dc.customer_id) AS unique_customers,
    COUNT(DISTINCT fo.order_id) AS total_orders,
    ROUND(SUM(fod.net_sales), 2) AS total_revenue,
    ROUND(SUM(fod.net_profit), 2) AS total_profit,
    ROUND(SUM(fod.net_sales) / NULLIF(COUNT(DISTINCT fo.order_id), 0), 2) AS avg_order_value,
    ROUND(100.0 * SUM(fod.net_profit) / NULLIF(SUM(fod.net_sales), 0), 2) AS profit_margin_pct
FROM dim_customer dc
JOIN fact_orders fo ON dc.customer_id = fo.customer_id
JOIN fact_order_details fod ON fo.order_id = fod.order_id
GROUP BY 1, dc.gender
ORDER BY age_cohort, total_revenue DESC;


-- QUERY 13: Average Days Between 1st and 2nd Order (Repeat Purchase Velocity)
-- Business Question: How long does it take for a newly converted customer to make their second purchase?
WITH ranked_orders AS (
    SELECT 
        customer_id,
        order_id,
        order_date,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date ASC) AS order_seq
    FROM fact_orders
),
first_second_lag AS (
    SELECT 
        o1.customer_id,
        o1.order_date AS first_order_date,
        o2.order_date AS second_order_date,
        CAST((JULIANDAY(o2.order_date) - JULIANDAY(o1.order_date)) AS INT) AS days_to_repeat
    FROM ranked_orders o1
    JOIN ranked_orders o2 ON o1.customer_id = o2.customer_id AND o1.order_seq = 1 AND o2.order_seq = 2
)
SELECT 
    COUNT(*) AS total_repeat_customers,
    ROUND(AVG(days_to_repeat), 1) AS avg_days_to_second_order,
    MIN(days_to_repeat) AS fastest_repeat_days,
    MAX(days_to_repeat) AS slowest_repeat_days
FROM first_second_lag;


-- ==============================================================================
-- DOMAIN 3: PRODUCT PORTFOLIO, MARGIN MATRIX & PARETO ANALYSIS (Queries 14 - 20)
-- ==============================================================================

-- QUERY 14: Top 10 Best-Selling SKUs by Net Revenue
-- Business Question: Which individual products generate the highest gross dollar volume?
SELECT 
    dp.product_id,
    dp.product_name,
    dp.category,
    dp.sub_category,
    dp.brand,
    SUM(fod.quantity) AS total_units_sold,
    ROUND(SUM(fod.net_sales), 2) AS total_net_revenue,
    ROUND(SUM(fod.net_profit), 2) AS total_net_profit,
    ROUND(100.0 * SUM(fod.net_profit) / NULLIF(SUM(fod.net_sales), 0), 2) AS realized_margin_pct,
    DENSE_RANK() OVER (ORDER BY SUM(fod.net_sales) DESC) AS revenue_rank
FROM dim_product dp
JOIN fact_order_details fod ON dp.product_id = fod.product_id
GROUP BY dp.product_id, dp.product_name, dp.category, dp.sub_category, dp.brand
ORDER BY total_net_revenue DESC
LIMIT 10;


-- QUERY 15: Bottom 10 Profit-Dragging SKUs (Lowest Profit / Negative Margin)
-- Business Question: Which products are actively hurting company profitability?
SELECT 
    dp.product_id,
    dp.product_name,
    dp.category,
    dp.sub_category,
    dp.brand,
    SUM(fod.quantity) AS units_sold,
    ROUND(AVG(fod.discount_rate) * 100, 1) AS avg_discount_rate_pct,
    ROUND(SUM(fod.net_sales), 2) AS total_net_revenue,
    ROUND(SUM(fod.net_profit), 2) AS total_net_profit,
    ROUND(100.0 * SUM(fod.net_profit) / NULLIF(SUM(fod.net_sales), 0), 2) AS profit_margin_pct
FROM dim_product dp
JOIN fact_order_details fod ON dp.product_id = fod.product_id
GROUP BY dp.product_id, dp.product_name, dp.category, dp.sub_category, dp.brand
ORDER BY total_net_profit ASC
LIMIT 10;


-- QUERY 16: Pareto 80/20 Analysis (Revenue Concentration)
-- Business Question: What percentage of our product catalog accounts for 80% of total revenue?
WITH product_revenue AS (
    SELECT 
        dp.product_id,
        dp.product_name,
        dp.category,
        ROUND(SUM(fod.net_sales), 2) AS product_sales
    FROM dim_product dp
    JOIN fact_order_details fod ON dp.product_id = fod.product_id
    GROUP BY dp.product_id, dp.product_name, dp.category
),
cumulative_revenue AS (
    SELECT 
        product_id,
        product_name,
        category,
        product_sales,
        SUM(product_sales) OVER (ORDER BY product_sales DESC) AS running_revenue,
        SUM(product_sales) OVER () AS total_enterprise_revenue
    FROM product_revenue
)
SELECT 
    product_id,
    product_name,
    category,
    product_sales,
    ROUND(100.0 * product_sales / total_enterprise_revenue, 3) AS product_revenue_share_pct,
    ROUND(100.0 * running_revenue / total_enterprise_revenue, 2) AS cumulative_revenue_pct,
    CASE 
        WHEN (100.0 * running_revenue / total_enterprise_revenue) <= 80.0 THEN 'Core 80% Revenue Driver (Tier A)'
        ELSE 'Long-Tail 20% Product (Tier B/C)'
    END AS pareto_tier
FROM cumulative_revenue
ORDER BY product_sales DESC
LIMIT 50;


-- QUERY 17: Product Margin Matrix / BCG Quadrant Segmentation
-- Business Question: How do products categorize across High/Low Volume vs High/Low Profitability?
WITH sku_metrics AS (
    SELECT 
        dp.product_id,
        dp.product_name,
        dp.category,
        SUM(fod.quantity) AS units_sold,
        ROUND(SUM(fod.net_sales), 2) AS net_revenue,
        ROUND(SUM(fod.net_profit), 2) AS net_profit,
        ROUND(100.0 * SUM(fod.net_profit) / NULLIF(SUM(fod.net_sales), 0), 2) AS margin_pct
    FROM dim_product dp
    JOIN fact_order_details fod ON dp.product_id = fod.product_id
    GROUP BY dp.product_id, dp.product_name, dp.category
),
benchmarks AS (
    SELECT 
        AVG(net_revenue) AS avg_revenue,
        AVG(margin_pct) AS avg_margin
    FROM sku_metrics
)
SELECT 
    sm.product_id,
    sm.product_name,
    sm.category,
    sm.units_sold,
    sm.net_revenue,
    sm.net_profit,
    sm.margin_pct,
    CASE 
        WHEN sm.net_revenue >= b.avg_revenue AND sm.margin_pct >= b.avg_margin THEN 'Star (High Sales, High Margin)'
        WHEN sm.net_revenue >= b.avg_revenue AND sm.margin_pct < b.avg_margin THEN 'Profit Trap (High Sales, Low Margin)'
        WHEN sm.net_revenue < b.avg_revenue AND sm.margin_pct >= b.avg_margin THEN 'Niche Gem (Low Sales, High Margin)'
        ELSE 'Underperformer (Low Sales, Low Margin)'
    END AS strategic_quadrant
FROM sku_metrics sm
CROSS JOIN benchmarks b
ORDER BY sm.net_revenue DESC;


-- QUERY 18: Category & Sub-Category Performance League Table
-- Business Question: Which category-sub-category hierarchies deliver the strongest return on sales?
SELECT 
    dp.category,
    dp.sub_category,
    COUNT(DISTINCT fo.order_id) AS total_orders,
    SUM(fod.quantity) AS total_units_sold,
    ROUND(SUM(fod.gross_sales), 2) AS gross_sales,
    ROUND(SUM(fod.discount_amount), 2) AS total_discounts,
    ROUND(SUM(fod.net_sales), 2) AS net_revenue,
    ROUND(SUM(fod.total_cost), 2) AS total_cogs,
    ROUND(SUM(fod.net_profit), 2) AS net_profit,
    ROUND(100.0 * SUM(fod.net_profit) / NULLIF(SUM(fod.net_sales), 0), 2) AS profit_margin_pct,
    DENSE_RANK() OVER (PARTITION BY dp.category ORDER BY SUM(fod.net_profit) DESC) AS rank_within_category
FROM dim_product dp
JOIN fact_order_details fod ON dp.product_id = fod.product_id
JOIN fact_orders fo ON fod.order_id = fo.order_id
GROUP BY dp.category, dp.sub_category
ORDER BY dp.category, net_profit DESC;


-- QUERY 19: Discount Tier Elasticity & Profit Erosion Analysis
-- Business Question: What is the empirical impact of increasing discounts on realized profit margins?
SELECT 
    CASE 
        WHEN discount_rate = 0.00 THEN '1. Full Price (0% Discount)'
        WHEN discount_rate <= 0.05 THEN '2. Low (5% Discount)'
        WHEN discount_rate <= 0.10 THEN '3. Standard (10% Discount)'
        WHEN discount_rate <= 0.15 THEN '4. Moderate (15% Discount)'
        WHEN discount_rate <= 0.20 THEN '5. High (20% Discount)'
        WHEN discount_rate <= 0.25 THEN '6. Aggressive (25% Discount)'
        ELSE '7. Deep Clearance (30%+ Discount)'
    END AS discount_tier,
    COUNT(*) AS line_item_count,
    SUM(quantity) AS total_units_sold,
    ROUND(SUM(gross_sales), 2) AS gross_sales,
    ROUND(SUM(discount_amount), 2) AS discount_cost,
    ROUND(SUM(net_sales), 2) AS realized_net_sales,
    ROUND(SUM(net_profit), 2) AS realized_net_profit,
    ROUND(100.0 * SUM(net_profit) / NULLIF(SUM(net_sales), 0), 2) AS profit_margin_pct,
    ROUND(AVG(net_sales / quantity), 2) AS realized_avg_selling_price
FROM fact_order_details
GROUP BY 1
ORDER BY 1 ASC;


-- QUERY 20: High Discount & Negative/Low Profit Drag Items (Margin Leakage SKU Audit)
-- Business Question: Which line items had heavy discounts (>20%) resulting in razor-thin margins?
SELECT 
    dp.product_name,
    dp.category,
    COUNT(*) AS heavily_discounted_orders,
    SUM(fod.quantity) AS units_sold,
    ROUND(SUM(fod.gross_sales), 2) AS gross_sales,
    ROUND(SUM(fod.discount_amount), 2) AS discount_dollars_lost,
    ROUND(SUM(fod.net_sales), 2) AS net_revenue,
    ROUND(SUM(fod.net_profit), 2) AS net_profit,
    ROUND(100.0 * SUM(fod.net_profit) / NULLIF(SUM(fod.net_sales), 0), 2) AS heavily_discounted_margin_pct
FROM fact_order_details fod
JOIN dim_product dp ON fod.product_id = dp.product_id
WHERE fod.discount_rate >= 0.20
GROUP BY dp.product_name, dp.category
HAVING (100.0 * SUM(fod.net_profit) / NULLIF(SUM(fod.net_sales), 0)) < 12.0
ORDER BY discount_dollars_lost DESC
LIMIT 15;


-- ==============================================================================
-- DOMAIN 4: REGIONAL, CHANNEL & SALES TARGET ANALYSIS (Queries 21 - 25)
-- ==============================================================================

-- QUERY 21: Regional Sales Targets vs. Actual Performance & Variance %
-- Business Question: Did regional managers meet their monthly sales and profit quotas?
WITH actuals AS (
    SELECT 
        SUBSTR(fo.order_date, 1, 7) AS year_month,
        fo.region_id,
        dp.category,
        ROUND(SUM(fod.net_sales), 2) AS actual_sales,
        ROUND(SUM(fod.net_profit), 2) AS actual_profit,
        COUNT(DISTINCT fo.order_id) AS actual_orders
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
    ROUND(100.0 * COALESCE(a.actual_profit, 0) / NULLIF(fst.profit_target, 0), 2) AS profit_achievement_pct,
    CASE 
        WHEN COALESCE(a.actual_sales, 0) >= fst.sales_target THEN 'Target Achieved'
        ELSE 'Missed Target'
    END AS quota_status
FROM fact_sales_targets fst
JOIN dim_region dr ON fst.region_id = dr.region_id
LEFT JOIN actuals a ON fst.year_month = a.year_month 
                   AND fst.region_id = a.region_id 
                   AND fst.category_name = a.category
ORDER BY fst.year_month DESC, sales_achievement_pct DESC
LIMIT 40;


-- QUERY 22: Annual Regional Performance League Table & Quota Health
-- Business Question: Which regional directors consistently exceed quotas and generate the highest return?
WITH regional_annual AS (
    SELECT 
        dr.region_id,
        dr.region_name,
        dr.regional_manager,
        dd.year,
        ROUND(SUM(fod.net_sales), 2) AS total_sales,
        ROUND(SUM(fod.net_profit), 2) AS total_profit,
        COUNT(DISTINCT fo.order_id) AS total_orders
    FROM fact_orders fo
    JOIN dim_region dr ON fo.region_id = dr.region_id
    JOIN dim_date dd ON fo.order_date = dd.full_date
    JOIN fact_order_details fod ON fo.order_id = fod.order_id
    GROUP BY dr.region_id, dr.region_name, dr.regional_manager, dd.year
)
SELECT 
    year,
    region_name,
    regional_manager,
    total_orders,
    total_sales,
    total_profit,
    ROUND(100.0 * total_profit / NULLIF(total_sales, 0), 2) AS margin_pct,
    ROUND(100.0 * total_sales / SUM(total_sales) OVER (PARTITION BY year), 2) AS global_sales_share_pct,
    RANK() OVER (PARTITION BY year ORDER BY total_sales DESC) AS sales_rank
FROM regional_annual
ORDER BY year DESC, total_sales DESC;


-- QUERY 23: Sales Channel Profitability Matrix (Web vs App vs B2B vs Affiliate)
-- Business Question: What is the margin profile across distinct digital and B2B sales channels?
SELECT 
    fo.sales_channel,
    COUNT(DISTINCT fo.order_id) AS total_orders,
    ROUND(SUM(fod.gross_sales), 2) AS gross_sales,
    ROUND(SUM(fod.discount_amount), 2) AS total_discounts,
    ROUND(100.0 * SUM(fod.discount_amount) / NULLIF(SUM(fod.gross_sales), 0), 2) AS avg_discount_pct,
    ROUND(SUM(fod.net_sales), 2) AS net_revenue,
    ROUND(SUM(fod.net_profit), 2) AS net_profit,
    ROUND(100.0 * SUM(fod.net_profit) / NULLIF(SUM(fod.net_sales), 0), 2) AS profit_margin_pct,
    ROUND(SUM(fod.net_sales) / NULLIF(COUNT(DISTINCT fo.order_id), 0), 2) AS channel_aov
FROM fact_orders fo
JOIN fact_order_details fod ON fo.order_id = fod.order_id
GROUP BY fo.sales_channel
ORDER BY net_revenue DESC;


-- QUERY 24: Payment Method Distribution and Transaction Economics
-- Business Question: How does customer payment method choice correlate with order value and refund risk?
SELECT 
    fo.payment_method,
    COUNT(DISTINCT fo.order_id) AS total_transactions,
    ROUND(SUM(fod.net_sales), 2) AS total_net_revenue,
    ROUND(AVG(fod.net_sales), 2) AS avg_item_value,
    ROUND(SUM(fod.net_sales) / NULLIF(COUNT(DISTINCT fo.order_id), 0), 2) AS avg_order_value,
    ROUND(100.0 * COUNT(DISTINCT fo.order_id) / (SELECT COUNT(*) FROM fact_orders), 2) AS transaction_share_pct
FROM fact_orders fo
JOIN fact_order_details fod ON fo.order_id = fod.order_id
GROUP BY fo.payment_method
ORDER BY total_net_revenue DESC;


-- QUERY 25: Shipping Mode Speed, Cost and Profitability
-- Business Question: How does delivery mode (Ground vs Express vs Priority) impact net margin?
SELECT 
    fo.shipping_mode,
    COUNT(DISTINCT fo.order_id) AS total_shipments,
    SUM(fod.quantity) AS total_units_shipped,
    ROUND(SUM(fod.net_sales), 2) AS total_net_revenue,
    ROUND(SUM(fod.net_profit), 2) AS total_net_profit,
    ROUND(100.0 * SUM(fod.net_profit) / NULLIF(SUM(fod.net_sales), 0), 2) AS realized_margin_pct
FROM fact_orders fo
JOIN fact_order_details fod ON fo.order_id = fod.order_id
GROUP BY fo.shipping_mode
ORDER BY total_net_revenue DESC;


-- ==============================================================================
-- DOMAIN 5: RETURNS, INVENTORY HEALTH & OPERATIONS (Queries 26 - 32)
-- ==============================================================================

-- QUERY 26: Return Rate & Financial Refund Loss by Product Category
-- Business Question: Which categories suffer the highest product return rates and financial refund drain?
WITH category_sales AS (
    SELECT 
        dp.category,
        SUM(fod.quantity) AS total_units_sold,
        ROUND(SUM(fod.net_sales), 2) AS total_category_revenue
    FROM dim_product dp
    JOIN fact_order_details fod ON dp.product_id = fod.product_id
    GROUP BY dp.category
),
category_returns AS (
    SELECT 
        dp.category,
        SUM(fr.return_quantity) AS total_units_returned,
        ROUND(SUM(fr.refund_amount), 2) AS total_refunds_issued
    FROM dim_product dp
    JOIN fact_returns fr ON dp.product_id = fr.product_id
    GROUP BY dp.category
)
SELECT 
    cs.category,
    cs.total_units_sold,
    COALESCE(cr.total_units_returned, 0) AS units_returned,
    ROUND(100.0 * COALESCE(cr.total_units_returned, 0) / NULLIF(cs.total_units_sold, 0), 2) AS return_rate_pct,
    cs.total_category_revenue,
    COALESCE(cr.total_refunds_issued, 0) AS total_refunds_issued,
    ROUND(100.0 * COALESCE(cr.total_refunds_issued, 0) / NULLIF(cs.total_category_revenue, 0), 2) AS refund_revenue_loss_pct
FROM category_sales cs
LEFT JOIN category_returns cr ON cs.category = cr.category
ORDER BY return_rate_pct DESC;


-- QUERY 27: Root Cause Analysis of Product Returns
-- Business Question: What are the primary defect reasons driving product returns?
SELECT 
    return_reason,
    COUNT(*) AS total_return_incidents,
    SUM(return_quantity) AS total_items_returned,
    ROUND(SUM(refund_amount), 2) AS total_refunded_dollars,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_returns), 2) AS return_incident_share_pct,
    ROUND(AVG(refund_amount), 2) AS avg_refund_per_incident
FROM fact_returns
GROUP BY return_reason
ORDER BY total_refunded_dollars DESC;


-- QUERY 28: Top 10 High-Return Products (Quality Problem SKUs)
-- Business Question: Which specific SKUs have alarming return rates that require supplier review?
WITH product_sales AS (
    SELECT 
        dp.product_id,
        dp.product_name,
        dp.category,
        dp.brand,
        SUM(fod.quantity) AS units_sold,
        ROUND(SUM(fod.net_sales), 2) AS net_sales
    FROM dim_product dp
    JOIN fact_order_details fod ON dp.product_id = fod.product_id
    GROUP BY dp.product_id, dp.product_name, dp.category, dp.brand
),
product_returns AS (
    SELECT 
        product_id,
        SUM(return_quantity) AS units_returned,
        ROUND(SUM(refund_amount), 2) AS refund_dollars
    FROM fact_returns
    GROUP BY product_id
)
SELECT 
    ps.product_id,
    ps.product_name,
    ps.category,
    ps.brand,
    ps.units_sold,
    COALESCE(pr.units_returned, 0) AS units_returned,
    ROUND(100.0 * COALESCE(pr.units_returned, 0) / NULLIF(ps.units_sold, 0), 2) AS return_rate_pct,
    ps.net_sales,
    COALESCE(pr.refund_dollars, 0) AS total_refund_loss
FROM product_sales ps
JOIN product_returns pr ON ps.product_id = pr.product_id
WHERE ps.units_sold >= 50
ORDER BY return_rate_pct DESC
LIMIT 10;


-- QUERY 29: Inventory Turnover Ratio and Stock Velocity by Category
-- Business Question: How efficiently is inventory converting into realized sales?
WITH inv_summary AS (
    SELECT 
        dp.category,
        ROUND(AVG(fi.closing_stock * dp.cost_price), 2) AS avg_inventory_holding_value,
        SUM(fi.units_sold) AS total_inventory_units_sold
    FROM fact_inventory fi
    JOIN dim_product dp ON fi.product_id = dp.product_id
    GROUP BY dp.category
),
cogs_summary AS (
    SELECT 
        dp.category,
        ROUND(SUM(fod.total_cost), 2) AS total_annual_cogs
    FROM fact_order_details fod
    JOIN dim_product dp ON fod.product_id = dp.product_id
    GROUP BY dp.category
)
SELECT 
    inv.category,
    cogs.total_annual_cogs,
    inv.avg_inventory_holding_value,
    ROUND(cogs.total_annual_cogs / NULLIF(inv.avg_inventory_holding_value, 0), 2) AS inventory_turnover_ratio,
    ROUND(365.0 / NULLIF((cogs.total_annual_cogs / NULLIF(inv.avg_inventory_holding_value, 0)), 0), 1) AS days_sales_in_inventory_dsi
FROM inv_summary inv
JOIN cogs_summary cogs ON inv.category = cogs.category
ORDER BY inventory_turnover_ratio DESC;


-- QUERY 30: Stockout Risk and Critical Inventory Alert SKUs
-- Business Question: Which SKUs are currently below reorder levels and risk lost sales?
SELECT 
    dp.product_id,
    dp.product_name,
    dp.category,
    dp.brand,
    fi.snapshot_date,
    fi.closing_stock,
    dp.reorder_level,
    (dp.reorder_level - fi.closing_stock) AS stock_deficit_units,
    fi.stock_status
FROM fact_inventory fi
JOIN dim_product dp ON fi.product_id = dp.product_id
WHERE fi.snapshot_date = '2025-12-01' AND fi.closing_stock <= dp.reorder_level
ORDER BY stock_deficit_units DESC
LIMIT 20;


-- QUERY 31: Order Cancellation Rate & Lost Opportunity
-- Business Question: What percentage of booked orders were cancelled and what is the lost gross revenue?
SELECT 
    fo.order_status,
    COUNT(DISTINCT fo.order_id) AS total_orders,
    ROUND(100.0 * COUNT(DISTINCT fo.order_id) / (SELECT COUNT(*) FROM fact_orders), 2) AS order_share_pct,
    ROUND(SUM(fod.net_sales), 2) AS total_revenue_impact,
    ROUND(SUM(fod.net_profit), 2) AS total_profit_impact
FROM fact_orders fo
JOIN fact_order_details fod ON fo.order_id = fod.order_id
GROUP BY fo.order_status
ORDER BY total_orders DESC;


-- QUERY 32: Enterprise Net Margin Waterfall Bridge (Gross -> Discounts -> Returns -> Net Profit)
-- Business Question: What is the exact waterfall leakage from Gross Potential Revenue to Realized Net Profit?
SELECT 
    ROUND(SUM(fod.gross_sales), 2) AS step_1_gross_potential_sales,
    ROUND(SUM(fod.discount_amount), 2) AS step_2_total_discounts_given,
    ROUND(SUM(fod.net_sales), 2) AS step_3_realized_net_sales,
    ROUND(SUM(fod.total_cost), 2) AS step_4_total_cogs,
    ROUND((SELECT SUM(refund_amount) FROM fact_returns), 2) AS step_5_total_returns_refunded,
    ROUND(SUM(fod.net_profit) - (SELECT SUM(refund_amount) FROM fact_returns), 2) AS step_6_final_net_operating_profit,
    ROUND(100.0 * (SUM(fod.net_profit) - (SELECT SUM(refund_amount) FROM fact_returns)) / NULLIF(SUM(fod.net_sales), 0), 2) AS final_net_profit_margin_pct
FROM fact_order_details fod;
