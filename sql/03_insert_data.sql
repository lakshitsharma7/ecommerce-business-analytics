-- ==============================================================================
-- 03_insert_data.sql
-- PROJECT: E-Commerce Sales, Customer & Business Performance Analytics
-- DESCRIPTION: Data Ingestion and ETL Load Instructions
-- ==============================================================================

-- ==========================================
-- PostgreSQL COPY Commands (Execute as superuser)
-- ==========================================
/*
\copy dim_region FROM 'data/cleaned/dim_region.csv' WITH (FORMAT csv, HEADER true);
\copy dim_category FROM 'data/cleaned/dim_category.csv' WITH (FORMAT csv, HEADER true);
\copy dim_date FROM 'data/cleaned/dim_date.csv' WITH (FORMAT csv, HEADER true);
\copy dim_product FROM 'data/cleaned/dim_product.csv' WITH (FORMAT csv, HEADER true);
\copy dim_customer FROM 'data/cleaned/dim_customer.csv' WITH (FORMAT csv, HEADER true);
\copy fact_orders FROM 'data/cleaned/fact_orders.csv' WITH (FORMAT csv, HEADER true);
\copy fact_order_details FROM 'data/cleaned/fact_order_details.csv' WITH (FORMAT csv, HEADER true);
\copy fact_returns FROM 'data/cleaned/fact_returns.csv' WITH (FORMAT csv, HEADER true);
\copy fact_inventory FROM 'data/cleaned/fact_inventory.csv' WITH (FORMAT csv, HEADER true);
\copy fact_sales_targets FROM 'data/cleaned/fact_sales_targets.csv' WITH (FORMAT csv, HEADER true);
*/

-- ==========================================
-- MySQL LOAD DATA LOCAL INFILE Commands
-- ==========================================
/*
LOAD DATA LOCAL INFILE 'data/cleaned/dim_region.csv' INTO TABLE dim_region FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'data/cleaned/dim_category.csv' INTO TABLE dim_category FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'data/cleaned/dim_date.csv' INTO TABLE dim_date FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'data/cleaned/dim_product.csv' INTO TABLE dim_product FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'data/cleaned/dim_customer.csv' INTO TABLE dim_customer FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'data/cleaned/fact_orders.csv' INTO TABLE fact_orders FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'data/cleaned/fact_order_details.csv' INTO TABLE fact_order_details FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'data/cleaned/fact_returns.csv' INTO TABLE fact_returns FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'data/cleaned/fact_inventory.csv' INTO TABLE fact_inventory FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'data/cleaned/fact_sales_targets.csv' INTO TABLE fact_sales_targets FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
*/

-- Verify Row Counts After Load
SELECT 'dim_region' AS table_name, COUNT(*) AS total_rows FROM dim_region
UNION ALL SELECT 'dim_category', COUNT(*) FROM dim_category
UNION ALL SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL SELECT 'dim_customer', COUNT(*) FROM dim_customer
UNION ALL SELECT 'fact_orders', COUNT(*) FROM fact_orders
UNION ALL SELECT 'fact_order_details', COUNT(*) FROM fact_order_details
UNION ALL SELECT 'fact_returns', COUNT(*) FROM fact_returns
UNION ALL SELECT 'fact_inventory', COUNT(*) FROM fact_inventory
UNION ALL SELECT 'fact_sales_targets', COUNT(*) FROM fact_sales_targets;
