-- ==============================================================================
-- 01_create_database.sql
-- PROJECT: E-Commerce Sales, Customer & Business Performance Analytics
-- SYSTEM: PostgreSQL / MySQL / SQLite Compatible DDL
-- ==============================================================================

-- PostgreSQL Database Creation
-- CREATE DATABASE ecommerce_analytics WITH ENCODING = 'UTF8';
-- \c ecommerce_analytics;

-- MySQL Database Creation
-- CREATE DATABASE IF NOT EXISTS ecommerce_analytics CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE ecommerce_analytics;

-- SQLite Database Setup
-- Run: sqlite3 data/ecommerce_analytics.db
PRAGMA foreign_keys = ON;
