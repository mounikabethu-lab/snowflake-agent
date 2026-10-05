-- ============================================================================
-- SEMANTIC LAYER CREATION
-- Purpose: Create and populate semantic layer tables for AI Agent
-- Environment: DEV/TEST/PROD (environment-agnostic)
-- ============================================================================

USE DATABASE SALES_DATA;
USE SCHEMA PUBLIC;

-- ============================================================================
-- STEP 1: CREATE DATA DICTIONARY TABLE
-- ============================================================================

CREATE OR REPLACE TABLE DATA_DICTIONARY (
    TABLE_ID VARCHAR,
    TABLE_NAME VARCHAR,
    TABLE_DESCRIPTION VARCHAR,
    COLUMN_NAME VARCHAR,
    COLUMN_TYPE VARCHAR,
    COLUMN_DESCRIPTION VARCHAR,
    IS_KEY BOOLEAN,
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- STEP 2: POPULATE DATA DICTIONARY
-- ============================================================================

INSERT INTO DATA_DICTIONARY (TABLE_ID, TABLE_NAME, TABLE_DESCRIPTION, COLUMN_NAME, COLUMN_TYPE, COLUMN_DESCRIPTION, IS_KEY)
VALUES
-- CUSTOMERS TABLE
('T001', 'CUSTOMERS', 'Master customer data with industry and company size information', 'CUSTOMER_ID', 'NUMBER', 'Unique customer identifier', TRUE),
('T001', 'CUSTOMERS', 'Master customer data with industry and company size information', 'CUSTOMER_NAME', 'VARCHAR', 'Name of the customer company', FALSE),
('T001', 'CUSTOMERS', 'Master customer data with industry and company size information', 'INDUSTRY', 'VARCHAR', 'Customer industry sector', FALSE),
('T001', 'CUSTOMERS', 'Master customer data with industry and company size information', 'COMPANY_SIZE', 'VARCHAR', 'Size category: Small, Medium, Large, Enterprise', FALSE),

-- ORDERS TABLE
('T002', 'ORDERS', 'Sales orders fact table containing transaction data', 'ORDER_ID', 'NUMBER', 'Unique order identifier', TRUE),
('T002', 'ORDERS', 'Sales orders fact table containing transaction data', 'CUSTOMER_ID', 'NUMBER', 'Reference to CUSTOMERS table', FALSE),
('T002', 'ORDERS', 'Sales orders fact table containing transaction data', 'REP_ID', 'NUMBER', 'Reference to SALES_REPS table', FALSE),
('T002', 'ORDERS', 'Sales orders fact table containing transaction data', 'ORDER_DATE', 'DATE', 'Date when order was placed', FALSE),
('T002', 'ORDERS', 'Sales orders fact table containing transaction data', 'FINAL_VALUE', 'NUMBER(10,2)', 'Total order value in currency', FALSE),

-- ORDER_ITEMS TABLE
('T003', 'ORDER_ITEMS', 'Line items detail for each order', 'ORDER_ITEM_ID', 'NUMBER', 'Unique line item identifier', TRUE),
('T003', 'ORDER_ITEMS', 'Line items detail for each order', 'ORDER_ID', 'NUMBER', 'Reference to ORDERS table', FALSE),
('T003', 'ORDER_ITEMS', 'Line items detail for each order', 'PRODUCT_ID', 'NUMBER', 'Reference to PRODUCTS table', FALSE),
('T003', 'ORDER_ITEMS', 'Line items detail for each order', 'QUANTITY', 'NUMBER', 'Quantity ordered', FALSE),
('T003', 'ORDER_ITEMS', 'Line items detail for each order', 'UNIT_PRICE', 'NUMBER(10,2)', 'Price per unit', FALSE),

-- PRODUCTS TABLE
('T004', 'PRODUCTS', 'Product catalog with pricing information', 'PRODUCT_ID', 'NUMBER', 'Unique product identifier', TRUE),
('T004', 'PRODUCTS', 'Product catalog with pricing information', 'PRODUCT_NAME', 'VARCHAR', 'Name of the product', FALSE),
('T004', 'PRODUCTS', 'Product catalog with pricing information', 'CATEGORY', 'VARCHAR', 'Product category classification', FALSE),
('T004', 'PRODUCTS', 'Product catalog with pricing information', 'PRICE', 'NUMBER(10,2)', 'List price of product', FALSE),

-- SALES_REPS TABLE
('T005', 'SALES_REPS', 'Sales representative information and territory', 'REP_ID', 'NUMBER', 'Unique sales rep identifier', TRUE),
('T005', 'SALES_REPS', 'Sales representative information and territory', 'REP_NAME', 'VARCHAR', 'Name of sales representative', FALSE),
('T005', 'SALES_REPS', 'Sales representative information and territory', 'TERRITORY', 'VARCHAR', 'Geographic territory assignment', FALSE),
('T005', 'SALES_REPS', 'Sales representative information and territory', 'MANAGER', 'VARCHAR', 'Manager name', FALSE),

-- REP_TERRITORIES TABLE
('T006', 'REP_TERRITORIES', 'Territory assignments and details', 'TERRITORY_ID', 'NUMBER', 'Unique territory identifier', TRUE),
('T006', 'REP_TERRITORIES', 'Territory assignments and details', 'REP_ID', 'NUMBER', 'Reference to SALES_REPS table', FALSE),
('T006', 'REP_TERRITORIES', 'Territory assignments and details', 'REGION', 'VARCHAR', 'Geographic region', FALSE),
('T006', 'REP_TERRITORIES', 'Territory assignments and details', 'QUOTA', 'NUMBER(15,2)', 'Territory sales quota', FALSE),

-- SALES_PERFORMANCE TABLE
('T007', 'SALES_PERFORMANCE', 'Monthly sales performance metrics and quota attainment', 'PERF_ID', 'NUMBER', 'Unique performance record id', TRUE),
('T007', 'SALES_PERFORMANCE', 'Monthly sales performance metrics and quota attainment', 'REP_ID', 'NUMBER', 'Reference to SALES_REPS table', FALSE),
('T007', 'SALES_PERFORMANCE', 'Monthly sales performance metrics and quota attainment', 'PERFORMANCE_MONTH', 'VARCHAR', 'Month in YYYY-MM format', FALSE),
('T007', 'SALES_PERFORMANCE', 'Monthly sales performance metrics and quota attainment', 'QUOTA', 'NUMBER(15,2)', 'Monthly sales quota', FALSE),
('T007', 'SALES_PERFORMANCE', 'Monthly sales performance metrics and quota attainment', 'ACTUAL_REVENUE', 'NUMBER(15,2)', 'Actual revenue achieved', FALSE),
('T007', 'SALES_PERFORMANCE', 'Monthly sales performance metrics and quota attainment', 'QUOTA_ATTAINMENT_PERCENT', 'NUMBER(5,2)', 'Percentage of quota achieved', FALSE),
('T007', 'SALES_PERFORMANCE', 'Monthly sales performance metrics and quota attainment', 'DEALS_WON', 'NUMBER', 'Count of deals won', FALSE),
('T007', 'SALES_PERFORMANCE', 'Monthly sales performance metrics and quota attainment', 'DEALS_LOST', 'NUMBER', 'Count of deals lost', FALSE),
('T007', 'SALES_PERFORMANCE', 'Monthly sales performance metrics and quota attainment', 'PIPELINE_VALUE', 'NUMBER(15,2)', 'Value of open pipeline', FALSE),

-- CUSTOMER_SEGMENTS TABLE
('T008', 'CUSTOMER_SEGMENTS', 'Customer segmentation and behavioral data', 'SEGMENT_ID', 'NUMBER', 'Unique segment identifier', TRUE),
('T008', 'CUSTOMER_SEGMENTS', 'Customer segmentation and behavioral data', 'CUSTOMER_ID', 'NUMBER', 'Reference to CUSTOMERS table', FALSE),
('T008', 'CUSTOMER_SEGMENTS', 'Customer segmentation and behavioral data', 'SEGMENT_NAME', 'VARCHAR', 'Segment classification', FALSE),
('T008', 'CUSTOMER_SEGMENTS', 'Customer segmentation and behavioral data', 'BEHAVIOR_SCORE', 'NUMBER(5,2)', 'Engagement score 0-100', FALSE),

-- PRODUCT_INVENTORY TABLE
('T009', 'PRODUCT_INVENTORY', 'Current product inventory levels and reorder information', 'INVENTORY_ID', 'NUMBER', 'Unique inventory record id', TRUE),
('T009', 'PRODUCT_INVENTORY', 'Current product inventory levels and reorder information', 'PRODUCT_ID', 'NUMBER', 'Reference to PRODUCTS table', FALSE),
('T009', 'PRODUCT_INVENTORY', 'Current product inventory levels and reorder information', 'QUANTITY_AVAILABLE', 'NUMBER', 'Units currently in stock', FALSE),
('T009', 'PRODUCT_INVENTORY', 'Current product inventory levels and reorder information', 'REORDER_LEVEL', 'NUMBER', 'Minimum quantity before reorder', FALSE),
('T009', 'PRODUCT_INVENTORY', 'Current product inventory levels and reorder information', 'LAST_RESTOCKED_DATE', 'DATE', 'Date of last restock', FALSE),

-- CUSTOMER_LIFETIME_VALUE TABLE
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis including churn risk and renewal probability', 'CLV_ID', 'NUMBER', 'Unique CLV record id', TRUE),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis including churn risk and renewal probability', 'CUSTOMER_ID', 'NUMBER', 'Reference to CUSTOMERS table', FALSE),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis including churn risk and renewal probability', 'TOTAL_REVENUE', 'NUMBER(15,2)', 'Total revenue from customer', FALSE),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis including churn risk and renewal probability', 'PREDICTED_LTV', 'NUMBER(15,2)', 'Predicted lifetime value', FALSE),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis including churn risk and renewal probability', 'CHURN_RISK_PERCENT', 'NUMBER(5,2)', 'Percentage chance of churn 0-100', FALSE),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis including churn risk and renewal probability', 'RENEWAL_LIKELIHOOD_PERCENT', 'NUMBER(5,2)', 'Percentage chance of renewal 0-100', FALSE),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis including churn risk and renewal probability', 'AVERAGE_ORDER_VALUE', 'NUMBER(10,2)', 'Average transaction value', FALSE),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis including churn risk and renewal probability', 'TOTAL_ORDERS', 'NUMBER', 'Total orders from customer', FALSE),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis including churn risk and renewal probability', 'LAST_ORDER_DATE', 'DATE', 'Date of most recent order', FALSE),

-- PRODUCT_DEMAND_FREQUENCY TABLE
('T011', 'PRODUCT_DEMAND_FREQUENCY', 'Product demand trends and growth analysis', 'DEMAND_ID', 'NUMBER', 'Unique demand record id', TRUE),
('T011', 'PRODUCT_DEMAND_FREQUENCY', 'Product demand trends and growth analysis', 'PRODUCT_ID', 'NUMBER', 'Reference to PRODUCTS table', FALSE),
('T011', 'PRODUCT_DEMAND_FREQUENCY', 'Product demand trends and growth analysis', 'PRODUCT_NAME', 'VARCHAR', 'Product name for easy reference', FALSE),
('T011', 'PRODUCT_DEMAND_FREQUENCY', 'Product demand trends and growth analysis', 'PURCHASE_FREQUENCY', 'NUMBER', 'How often purchased per year', FALSE),
('T011', 'PRODUCT_DEMAND_FREQUENCY', 'Product demand trends and growth analysis', 'GROWTH_TREND_PERCENT', 'NUMBER(5,2)', 'YoY growth percentage', FALSE),
('T011', 'PRODUCT_DEMAND_FREQUENCY', 'Product demand trends and growth analysis', 'TOTAL_REVENUE', 'NUMBER(15,2)', 'Total revenue from product', FALSE),
('T011', 'PRODUCT_DEMAND_FREQUENCY', 'Product demand trends and growth analysis', 'PEAK_SEASON', 'VARCHAR', 'Season when demand peaks', FALSE),
('T011', 'PRODUCT_DEMAND_FREQUENCY', 'Product demand trends and growth analysis', 'INVENTORY_RECOMMENDATION', 'VARCHAR', 'Recommended inventory level', FALSE),
('T011', 'PRODUCT_DEMAND_FREQUENCY', 'Product demand trends and growth analysis', 'SAFETY_STOCK', 'NUMBER', 'Minimum safety stock level', FALSE),

-- MONTHLY_SALES_TRENDS TABLE
('T012', 'MONTHLY_SALES_TRENDS', 'Historical monthly sales trends for forecasting', 'TREND_ID', 'NUMBER', 'Unique trend record id', TRUE),
('T012', 'MONTHLY_SALES_TRENDS', 'Historical monthly sales trends for forecasting', 'MONTH_DATE', 'DATE', 'Month for the trend', FALSE),
('T012', 'MONTHLY_SALES_TRENDS', 'Historical monthly sales trends for forecasting', 'TOTAL_SALES', 'NUMBER(15,2)', 'Total sales for month', FALSE),
('T012', 'MONTHLY_SALES_TRENDS', 'Historical monthly sales trends for forecasting', 'UNITS_SOLD', 'NUMBER', 'Total units sold', FALSE),

-- DEMAND_FORECAST TABLE
('T013', 'DEMAND_FORECAST', 'Product demand forecast for manufacturing planning', 'FORECAST_ID', 'NUMBER', 'Unique forecast record id', TRUE),
('T013', 'DEMAND_FORECAST', 'Product demand forecast for manufacturing planning', 'PRODUCT_ID', 'NUMBER', 'Reference to PRODUCTS table', FALSE),
('T013', 'DEMAND_FORECAST', 'Product demand forecast for manufacturing planning', 'PRODUCT_NAME', 'VARCHAR', 'Product name for reference', FALSE),
('T013', 'DEMAND_FORECAST', 'Product demand forecast for manufacturing planning', 'FORECAST_MONTH', 'VARCHAR', 'Forecast month in YYYY-MM format', FALSE),
('T013', 'DEMAND_FORECAST', 'Product demand forecast for manufacturing planning', 'FORECASTED_UNITS', 'NUMBER', 'Predicted units to be sold', FALSE),
('T013', 'DEMAND_FORECAST', 'Product demand forecast for manufacturing planning', 'LEAD_TIME_DAYS', 'NUMBER', 'Manufacturing lead time', FALSE),
('T013', 'DEMAND_FORECAST', 'Product demand forecast for manufacturing planning', 'MANUFACTURING_DEADLINE', 'DATE', 'Last date to start manufacturing', FALSE),
('T013', 'DEMAND_FORECAST', 'Product demand forecast for manufacturing planning', 'RISK_LEVEL', 'VARCHAR', 'Risk assessment: Low, Medium, High', FALSE);

-- ============================================================================
-- STEP 3: CREATE TABLE RELATIONSHIPS TABLE
-- ============================================================================

CREATE OR REPLACE TABLE TABLE_RELATIONSHIPS (
    RELATIONSHIP_ID VARCHAR,
    SOURCE_TABLE VARCHAR,
    SOURCE_COLUMN VARCHAR,
    TARGET_TABLE VARCHAR,
    TARGET_COLUMN VARCHAR,
    RELATIONSHIP_TYPE VARCHAR,
    CARDINALITY VARCHAR,
    RELATIONSHIP_DESCRIPTION VARCHAR,
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- STEP 4: POPULATE TABLE RELATIONSHIPS
-- ============================================================================

INSERT INTO TABLE_RELATIONSHIPS (RELATIONSHIP_ID, SOURCE_TABLE, SOURCE_COLUMN, TARGET_TABLE, TARGET_COLUMN, RELATIONSHIP_TYPE, CARDINALITY, RELATIONSHIP_DESCRIPTION)
VALUES
('R001', 'ORDERS', 'CUSTOMER_ID', 'CUSTOMERS', 'CUSTOMER_ID', 'FOREIGN_KEY', 'MANY_TO_ONE', 'Each order belongs to one customer'),
('R002', 'ORDERS', 'REP_ID', 'SALES_REPS', 'REP_ID', 'FOREIGN_KEY', 'MANY_TO_ONE', 'Each order is handled by one sales rep'),
('R003', 'ORDER_ITEMS', 'ORDER_ID', 'ORDERS', 'ORDER_ID', 'FOREIGN_KEY', 'MANY_TO_ONE', 'Each line item belongs to one order'),
('R004', 'ORDER_ITEMS', 'PRODUCT_ID', 'PRODUCTS', 'PRODUCT_ID', 'FOREIGN_KEY', 'MANY_TO_ONE', 'Each line item references one product'),
('R005', 'SALES_PERFORMANCE', 'REP_ID', 'SALES_REPS', 'REP_ID', 'FOREIGN_KEY', 'MANY_TO_ONE', 'Each performance record belongs to one rep'),
('R006', 'CUSTOMER_SEGMENTS', 'CUSTOMER_ID', 'CUSTOMERS', 'CUSTOMER_ID', 'FOREIGN_KEY', 'MANY_TO_ONE', 'Each segment belongs to one customer'),
('R007', 'PRODUCT_INVENTORY', 'PRODUCT_ID', 'PRODUCTS', 'PRODUCT_ID', 'FOREIGN_KEY', 'ONE_TO_ONE', 'Each product has one inventory record'),
('R008', 'CUSTOMER_LIFETIME_VALUE', 'CUSTOMER_ID', 'CUSTOMERS', 'CUSTOMER_ID', 'FOREIGN_KEY', 'ONE_TO_ONE', 'Each customer has one CLV record'),
('R009', 'PRODUCT_DEMAND_FREQUENCY', 'PRODUCT_ID', 'PRODUCTS', 'PRODUCT_ID', 'FOREIGN_KEY', 'ONE_TO_ONE', 'Each product has one demand frequency record'),
('R010', 'DEMAND_FORECAST', 'PRODUCT_ID', 'PRODUCTS', 'PRODUCT_ID', 'FOREIGN_KEY', 'MANY_TO_ONE', 'Each product can have multiple forecasts');

-- ============================================================================
-- STEP 5: CREATE BUSINESS CONTEXT TABLE
-- ============================================================================

CREATE OR REPLACE TABLE BUSINESS_CONTEXT (
    CONTEXT_ID VARCHAR,
    RULE_TYPE VARCHAR,
    RULE_NAME VARCHAR,
    RULE_DESCRIPTION VARCHAR,
    THRESHOLD_VALUE NUMBER(10,2),
    RULE_VALUE VARCHAR,
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- STEP 6: POPULATE BUSINESS CONTEXT
-- ============================================================================

INSERT INTO BUSINESS_CONTEXT (CONTEXT_ID, RULE_TYPE, RULE_NAME, RULE_DESCRIPTION, THRESHOLD_VALUE, RULE_VALUE)
VALUES
-- Churn Risk Thresholds
('BC001', 'CHURN_RISK', 'HIGH_RISK_THRESHOLD', 'Churn risk percentage for HIGH risk classification', 25.00, 'HIGH_RISK'),
('BC002', 'CHURN_RISK', 'MEDIUM_RISK_THRESHOLD', 'Churn risk percentage for MEDIUM risk classification', 15.00, 'MEDIUM_RISK'),
('BC003', 'CHURN_RISK', 'LOW_RISK_THRESHOLD', 'Churn risk percentage below which is LOW risk', 15.00, 'LOW_RISK'),

-- Quota Attainment Thresholds
('BC004', 'QUOTA_ATTAINMENT', 'EXCEEDING_THRESHOLD', 'Percentage above which rep is EXCEEDING quota', 110.00, 'EXCEEDING'),
('BC005', 'QUOTA_ATTAINMENT', 'ON_TRACK_MIN', 'Minimum percentage to be ON_TRACK', 85.00, 'ON_TRACK_MIN'),
('BC006', 'QUOTA_ATTAINMENT', 'ON_TRACK_MAX', 'Maximum percentage to be ON_TRACK', 110.00, 'ON_TRACK_MAX'),
('BC007', 'QUOTA_ATTAINMENT', 'UNDERPERFORMING_THRESHOLD', 'Percentage below which rep is UNDERPERFORMING', 85.00, 'UNDERPERFORMING'),

-- Inventory Status Thresholds
('BC008', 'INVENTORY_STATUS', 'CRITICAL_THRESHOLD', 'Inventory below safety stock is CRITICAL', 0.00, 'CRITICAL'),
('BC009', 'INVENTORY_STATUS', 'WARNING_THRESHOLD_MULTIPLIER', 'Inventory below safety stock * 1.5 is WARNING', 1.50, 'WARNING'),
('BC010', 'INVENTORY_STATUS', 'OK_THRESHOLD', 'Inventory at or above recommended level is OK', 1.50, 'OK'),

-- Product Growth Thresholds
('BC011', 'PRODUCT_GROWTH', 'HIGH_GROWTH_THRESHOLD', 'Growth percentage above which product is HIGH_GROWTH', 15.00, 'HIGH_GROWTH'),
('BC012', 'PRODUCT_GROWTH', 'MODERATE_GROWTH_THRESHOLD', 'Growth percentage above which is MODERATE_GROWTH', 5.00, 'MODERATE_GROWTH'),
('BC013', 'PRODUCT_GROWTH', 'DECLINING_THRESHOLD', 'Growth below moderate threshold is DECLINING', 5.00, 'DECLINING'),

-- Manufacturing Risk Levels
('BC014', 'MANUFACTURING_RISK', 'HIGH_RISK_LEVEL', 'Manufacturing risk level HIGH', 0.00, 'HIGH'),
('BC015', 'MANUFACTURING_RISK', 'MEDIUM_RISK_LEVEL', 'Manufacturing risk level MEDIUM', 0.00, 'MEDIUM'),
('BC016', 'MANUFACTURING_RISK', 'LOW_RISK_LEVEL', 'Manufacturing risk level LOW', 0.00, 'LOW'),

-- Business KPIs
('BC017', 'KPI', 'AVERAGE_DEAL_SIZE_TARGET', 'Target average deal size in currency', 50000.00, 'FINANCIAL'),
('BC018', 'KPI', 'CUSTOMER_RETENTION_TARGET', 'Target customer retention percentage', 95.00, 'RETENTION'),
('BC019', 'KPI', 'INVENTORY_TURNOVER_TARGET', 'Target inventory turnover ratio', 4.00, 'OPERATIONAL'),
('BC020', 'KPI', 'FORECAST_ACCURACY_TARGET', 'Target forecast accuracy percentage', 85.00, 'PLANNING');

