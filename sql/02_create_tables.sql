-- ==============================================================================
-- 02_create_tables.sql
-- PROJECT: E-Commerce Sales, Customer & Business Performance Analytics
-- DESCRIPTION: Normalized Relational Star Schema DDL with Keys and Indexes
-- ==============================================================================

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS fact_returns;
DROP TABLE IF EXISTS fact_inventory;
DROP TABLE IF EXISTS fact_sales_targets;
DROP TABLE IF EXISTS fact_order_details;
DROP TABLE IF EXISTS fact_orders;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_category;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_region;
DROP TABLE IF EXISTS dim_date;

-- ==========================================
-- 1. DIMENSION TABLES
-- ==========================================

-- Dim Region
CREATE TABLE dim_region (
    region_id VARCHAR(20) PRIMARY KEY,
    region_name VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL,
    regional_manager VARCHAR(100) NOT NULL
);

-- Dim Category
CREATE TABLE dim_category (
    sub_category_id VARCHAR(30) PRIMARY KEY,
    sub_category_name VARCHAR(100) NOT NULL,
    category_name VARCHAR(100) NOT NULL
);

-- Dim Product
CREATE TABLE dim_product (
    product_id VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    sub_category VARCHAR(100) NOT NULL,
    brand VARCHAR(50) NOT NULL,
    cost_price DECIMAL(10, 2) NOT NULL CHECK (cost_price >= 0),
    selling_price DECIMAL(10, 2) NOT NULL CHECK (selling_price >= 0),
    reorder_level INT NOT NULL DEFAULT 50
);

-- Dim Customer
CREATE TABLE dim_customer (
    customer_id VARCHAR(20) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    age INT CHECK (age >= 18 AND age <= 100),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    region_id VARCHAR(20) NOT NULL,
    customer_segment VARCHAR(50) NOT NULL,
    customer_since DATE NOT NULL,
    FOREIGN KEY (region_id) REFERENCES dim_region(region_id)
);

-- Dim Date
CREATE TABLE dim_date (
    full_date DATE PRIMARY KEY,
    date_key INT NOT NULL UNIQUE,
    year INT NOT NULL,
    quarter VARCHAR(5) NOT NULL,
    month_num INT NOT NULL CHECK (month_num BETWEEN 1 AND 12),
    month_name VARCHAR(20) NOT NULL,
    week_num INT NOT NULL,
    day_num INT NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    is_weekend INT NOT NULL CHECK (is_weekend IN (0, 1))
);

-- ==========================================
-- 2. FACT TABLES
-- ==========================================

-- Fact Orders (Header Level)
CREATE TABLE fact_orders (
    order_id VARCHAR(20) PRIMARY KEY,
    order_date DATE NOT NULL,
    customer_id VARCHAR(20) NOT NULL,
    region_id VARCHAR(20) NOT NULL,
    sales_channel VARCHAR(50) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    shipping_mode VARCHAR(50) NOT NULL,
    order_status VARCHAR(50) NOT NULL,
    FOREIGN KEY (order_date) REFERENCES dim_date(full_date),
    FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
    FOREIGN KEY (region_id) REFERENCES dim_region(region_id)
);

-- Fact Order Details (Line Item Level)
CREATE TABLE fact_order_details (
    order_detail_id VARCHAR(30) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    product_id VARCHAR(20) NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL,
    discount_rate DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    gross_sales DECIMAL(12, 2) NOT NULL,
    discount_amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    net_sales DECIMAL(12, 2) NOT NULL,
    total_cost DECIMAL(12, 2) NOT NULL,
    net_profit DECIMAL(12, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES fact_orders(order_id),
    FOREIGN KEY (product_id) REFERENCES dim_product(product_id)
);

-- Fact Returns
CREATE TABLE fact_returns (
    return_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    order_detail_id VARCHAR(30) NOT NULL,
    product_id VARCHAR(20) NOT NULL,
    return_date DATE NOT NULL,
    return_reason VARCHAR(100) NOT NULL,
    return_quantity INT NOT NULL CHECK (return_quantity > 0),
    refund_amount DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES fact_orders(order_id),
    FOREIGN KEY (order_detail_id) REFERENCES fact_order_details(order_detail_id),
    FOREIGN KEY (product_id) REFERENCES dim_product(product_id)
);

-- Fact Inventory (Monthly Snapshot)
CREATE TABLE fact_inventory (
    inventory_id VARCHAR(20) PRIMARY KEY,
    product_id VARCHAR(20) NOT NULL,
    snapshot_date DATE NOT NULL,
    opening_stock INT NOT NULL,
    units_received INT NOT NULL DEFAULT 0,
    units_sold INT NOT NULL DEFAULT 0,
    closing_stock INT NOT NULL,
    stock_status VARCHAR(30) NOT NULL,
    FOREIGN KEY (product_id) REFERENCES dim_product(product_id)
);

-- Fact Sales Targets (Monthly Target by Region & Category)
CREATE TABLE fact_sales_targets (
    target_id VARCHAR(20) PRIMARY KEY,
    year_month VARCHAR(10) NOT NULL,
    region_id VARCHAR(20) NOT NULL,
    category_name VARCHAR(50) NOT NULL,
    sales_target DECIMAL(12, 2) NOT NULL,
    profit_target DECIMAL(12, 2) NOT NULL,
    order_target INT NOT NULL,
    FOREIGN KEY (region_id) REFERENCES dim_region(region_id)
);

-- ==========================================
-- 3. INDEXES FOR PERFORMANCE OPTIMIZATION
-- ==========================================
CREATE INDEX idx_orders_customer ON fact_orders(customer_id);
CREATE INDEX idx_orders_date ON fact_orders(order_date);
CREATE INDEX idx_orders_region ON fact_orders(region_id);
CREATE INDEX idx_order_details_order ON fact_order_details(order_id);
CREATE INDEX idx_order_details_product ON fact_order_details(product_id);
CREATE INDEX idx_returns_order ON fact_returns(order_id);
CREATE INDEX idx_returns_product ON fact_returns(product_id);
CREATE INDEX idx_inventory_product ON fact_inventory(product_id);
CREATE INDEX idx_inventory_date ON fact_inventory(snapshot_date);
