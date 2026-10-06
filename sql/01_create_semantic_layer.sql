-- ============================================================================
-- SEMANTIC LAYER CREATION
-- ============================================================================

USE DATABASE SALES_DATA;
USE SCHEMA PUBLIC;

DROP TABLE IF EXISTS DATA_DICTIONARY;
DROP TABLE IF EXISTS TABLE_RELATIONSHIPS;
DROP TABLE IF EXISTS BUSINESS_CONTEXT;
DROP TABLE IF EXISTS AGENT_QUERY_LOG;
DROP TABLE IF EXISTS AGENT_SAMPLE_QUERIES;

-- ============================================================================
-- CREATE DATA_DICTIONARY TABLE
-- ============================================================================

CREATE TABLE DATA_DICTIONARY (
    TABLE_ID VARCHAR,
    TABLE_NAME VARCHAR,
    TABLE_DESCRIPTION VARCHAR,
    COLUMN_NAME VARCHAR,
    COLUMN_TYPE VARCHAR,
    COLUMN_DESCRIPTION VARCHAR,
    IS_KEY BOOLEAN,
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

INSERT INTO DATA_DICTIONARY VALUES
('T001', 'CUSTOMERS', 'Master customer data', 'CUSTOMER_ID', 'NUMBER', 'Unique customer identifier', TRUE, CURRENT_TIMESTAMP()),
('T001', 'CUSTOMERS', 'Master customer data', 'CUSTOMER_NAME', 'VARCHAR', 'Customer company name', FALSE, CURRENT_TIMESTAMP()),
('T001', 'CUSTOMERS', 'Master customer data', 'INDUSTRY', 'VARCHAR', 'Industry sector', FALSE, CURRENT_TIMESTAMP()),
('T001', 'CUSTOMERS', 'Master customer data', 'COMPANY_SIZE', 'VARCHAR', 'Company size category', FALSE, CURRENT_TIMESTAMP()),
('T002', 'ORDERS', 'Sales orders fact table', 'ORDER_ID', 'NUMBER', 'Unique order identifier', TRUE, CURRENT_TIMESTAMP()),
('T002', 'ORDERS', 'Sales orders fact table', 'CUSTOMER_ID', 'NUMBER', 'Reference to customer', FALSE, CURRENT_TIMESTAMP()),
('T002', 'ORDERS', 'Sales orders fact table', 'REP_ID', 'NUMBER', 'Reference to sales rep', FALSE, CURRENT_TIMESTAMP()),
('T002', 'ORDERS', 'Sales orders fact table', 'ORDER_DATE', 'DATE', 'Date order was placed', FALSE, CURRENT_TIMESTAMP()),
('T002', 'ORDERS', 'Sales orders fact table', 'FINAL_VALUE', 'NUMBER', 'Total order value', FALSE, CURRENT_TIMESTAMP()),
('T003', 'ORDER_ITEMS', 'Line items detail', 'ORDER_ITEM_ID', 'NUMBER', 'Unique line item id', TRUE, CURRENT_TIMESTAMP()),
('T003', 'ORDER_ITEMS', 'Line items detail', 'ORDER_ID', 'NUMBER', 'Reference to order', FALSE, CURRENT_TIMESTAMP()),
('T003', 'ORDER_ITEMS', 'Line items detail', 'PRODUCT_ID', 'NUMBER', 'Reference to product', FALSE, CURRENT_TIMESTAMP()),
('T003', 'ORDER_ITEMS', 'Line items detail', 'QUANTITY', 'NUMBER', 'Quantity ordered', FALSE, CURRENT_TIMESTAMP()),
('T003', 'ORDER_ITEMS', 'Line items detail', 'UNIT_PRICE', 'NUMBER', 'Price per unit', FALSE, CURRENT_TIMESTAMP()),
('T004', 'PRODUCTS', 'Product catalog', 'PRODUCT_ID', 'NUMBER', 'Unique product identifier', TRUE, CURRENT_TIMESTAMP()),
('T004', 'PRODUCTS', 'Product catalog', 'PRODUCT_NAME', 'VARCHAR', 'Product name', FALSE, CURRENT_TIMESTAMP()),
('T004', 'PRODUCTS', 'Product catalog', 'CATEGORY', 'VARCHAR', 'Product category', FALSE, CURRENT_TIMESTAMP()),
('T004', 'PRODUCTS', 'Product catalog', 'PRICE', 'NUMBER', 'List price', FALSE, CURRENT_TIMESTAMP()),
('T005', 'SALES_REPS', 'Sales representative data', 'REP_ID', 'NUMBER', 'Unique sales rep id', TRUE, CURRENT_TIMESTAMP()),
('T005', 'SALES_REPS', 'Sales representative data', 'REP_NAME', 'VARCHAR', 'Sales rep name', FALSE, CURRENT_TIMESTAMP()),
('T005', 'SALES_REPS', 'Sales representative data', 'TERRITORY', 'VARCHAR', 'Territory assignment', FALSE, CURRENT_TIMESTAMP()),
('T005', 'SALES_REPS', 'Sales representative data', 'MANAGER', 'VARCHAR', 'Manager name', FALSE, CURRENT_TIMESTAMP()),
('T006', 'REP_TERRITORIES', 'Territory assignments', 'TERRITORY_ID', 'NUMBER', 'Unique territory id', TRUE, CURRENT_TIMESTAMP()),
('T006', 'REP_TERRITORIES', 'Territory assignments', 'REP_ID', 'NUMBER', 'Reference to sales rep', FALSE, CURRENT_TIMESTAMP()),
('T006', 'REP_TERRITORIES', 'Territory assignments', 'REGION', 'VARCHAR', 'Geographic region', FALSE, CURRENT_TIMESTAMP()),
('T006', 'REP_TERRITORIES', 'Territory assignments', 'QUOTA', 'NUMBER', 'Territory sales quota', FALSE, CURRENT_TIMESTAMP()),
('T007', 'SALES_PERFORMANCE', 'Monthly sales metrics', 'PERF_ID', 'NUMBER', 'Unique performance record id', TRUE, CURRENT_TIMESTAMP()),
('T007', 'SALES_PERFORMANCE', 'Monthly sales metrics', 'REP_ID', 'NUMBER', 'Reference to sales rep', FALSE, CURRENT_TIMESTAMP()),
('T007', 'SALES_PERFORMANCE', 'Monthly sales metrics', 'PERFORMANCE_MONTH', 'VARCHAR', 'Month in YYYY-MM format', FALSE, CURRENT_TIMESTAMP()),
('T007', 'SALES_PERFORMANCE', 'Monthly sales metrics', 'QUOTA', 'NUMBER', 'Monthly quota', FALSE, CURRENT_TIMESTAMP()),
('T007', 'SALES_PERFORMANCE', 'Monthly sales metrics', 'ACTUAL_REVENUE', 'NUMBER', 'Actual revenue achieved', FALSE, CURRENT_TIMESTAMP()),
('T007', 'SALES_PERFORMANCE', 'Monthly sales metrics', 'QUOTA_ATTAINMENT_PERCENT', 'NUMBER', 'Percentage of quota achieved', FALSE, CURRENT_TIMESTAMP()),
('T007', 'SALES_PERFORMANCE', 'Monthly sales metrics', 'DEALS_WON', 'NUMBER', 'Number of deals won', FALSE, CURRENT_TIMESTAMP()),
('T007', 'SALES_PERFORMANCE', 'Monthly sales metrics', 'DEALS_LOST', 'NUMBER', 'Number of deals lost', FALSE, CURRENT_TIMESTAMP()),
('T007', 'SALES_PERFORMANCE', 'Monthly sales metrics', 'PIPELINE_VALUE', 'NUMBER', 'Open pipeline value', FALSE, CURRENT_TIMESTAMP()),
('T008', 'CUSTOMER_SEGMENTS', 'Customer segmentation', 'SEGMENT_ID', 'NUMBER', 'Unique segment id', TRUE, CURRENT_TIMESTAMP()),
('T008', 'CUSTOMER_SEGMENTS', 'Customer segmentation', 'CUSTOMER_ID', 'NUMBER', 'Reference to customer', FALSE, CURRENT_TIMESTAMP()),
('T008', 'CUSTOMER_SEGMENTS', 'Customer segmentation', 'SEGMENT_NAME', 'VARCHAR', 'Segment classification', FALSE, CURRENT_TIMESTAMP()),
('T008', 'CUSTOMER_SEGMENTS', 'Customer segmentation', 'BEHAVIOR_SCORE', 'NUMBER', 'Engagement score 0-100', FALSE, CURRENT_TIMESTAMP()),
('T009', 'PRODUCT_INVENTORY', 'Inventory levels', 'INVENTORY_ID', 'NUMBER', 'Unique inventory record id', TRUE, CURRENT_TIMESTAMP()),
('T009', 'PRODUCT_INVENTORY', 'Inventory levels', 'PRODUCT_ID', 'NUMBER', 'Reference to product', FALSE, CURRENT_TIMESTAMP()),
('T009', 'PRODUCT_INVENTORY', 'Inventory levels', 'QUANTITY_AVAILABLE', 'NUMBER', 'Units in stock', FALSE, CURRENT_TIMESTAMP()),
('T009', 'PRODUCT_INVENTORY', 'Inventory levels', 'REORDER_LEVEL', 'NUMBER', 'Minimum quantity threshold', FALSE, CURRENT_TIMESTAMP()),
('T009', 'PRODUCT_INVENTORY', 'Inventory levels', 'LAST_RESTOCKED_DATE', 'DATE', 'Last restock date', FALSE, CURRENT_TIMESTAMP()),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis', 'CLV_ID', 'NUMBER', 'Unique CLV record id', TRUE, CURRENT_TIMESTAMP()),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis', 'CUSTOMER_ID', 'NUMBER', 'Reference to customer', FALSE, CURRENT_TIMESTAMP()),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis', 'TOTAL_REVENUE', 'NUMBER', 'Total revenue from customer', FALSE, CURRENT_TIMESTAMP()),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis', 'PREDICTED_LTV', 'NUMBER', 'Predicted lifetime value', FALSE, CURRENT_TIMESTAMP()),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis', 'CHURN_RISK_PERCENT', 'NUMBER', 'Churn risk percentage 0-100', FALSE, CURRENT_TIMESTAMP()),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis', 'RENEWAL_LIKELIHOOD_PERCENT', 'NUMBER', 'Renewal likelihood 0-100', FALSE, CURRENT_TIMESTAMP()),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis', 'AVERAGE_ORDER_VALUE', 'NUMBER', 'Average transaction value', FALSE, CURRENT_TIMESTAMP()),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis', 'TOTAL_ORDERS', 'NUMBER', 'Total orders from customer', FALSE, CURRENT_TIMESTAMP()),
('T010', 'CUSTOMER_LIFETIME_VALUE', 'Customer value analysis', 'LAST_ORDER_DATE', 'DATE', 'Date of most recent order', FALSE, CURRENT_TIMESTAMP());

-- ============================================================================
-- CREATE TABLE_RELATIONSHIPS TABLE
-- ============================================================================

CREATE TABLE TABLE_RELATIONSHIPS (
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

INSERT INTO TABLE_RELATIONSHIPS VALUES
('R001', 'ORDERS', 'CUSTOMER_ID', 'CUSTOMERS', 'CUSTOMER_ID', 'FOREIGN_KEY', 'MANY_TO_ONE', 'Each order belongs to one customer', CURRENT_TIMESTAMP()),
('R002', 'ORDERS', 'REP_ID', 'SALES_REPS', 'REP_ID', 'FOREIGN_KEY', 'MANY_TO_ONE', 'Each order handled by one sales rep', CURRENT_TIMESTAMP()),
('R003', 'ORDER_ITEMS', 'ORDER_ID', 'ORDERS', 'ORDER_ID', 'FOREIGN_KEY', 'MANY_TO_ONE', 'Each line item belongs to one order', CURRENT_TIMESTAMP()),
('R004', 'ORDER_ITEMS', 'PRODUCT_ID', 'PRODUCTS', 'PRODUCT_ID', 'FOREIGN_KEY', 'MANY_TO_ONE', 'Each line item references one product', CURRENT_TIMESTAMP()),
('R005', 'SALES_PERFORMANCE', 'REP_ID', 'SALES_REPS', 'REP_ID', 'FOREIGN_KEY', 'MANY_TO_ONE', 'Each performance record belongs to one rep', CURRENT_TIMESTAMP()),
('R006', 'CUSTOMER_SEGMENTS', 'CUSTOMER_ID', 'CUSTOMERS', 'CUSTOMER_ID', 'FOREIGN_KEY', 'MANY_TO_ONE', 'Each segment belongs to one customer', CURRENT_TIMESTAMP()),
('R007', 'PRODUCT_INVENTORY', 'PRODUCT_ID', 'PRODUCTS', 'PRODUCT_ID', 'FOREIGN_KEY', 'ONE_TO_ONE', 'Each product has one inventory record', CURRENT_TIMESTAMP()),
('R008', 'CUSTOMER_LIFETIME_VALUE', 'CUSTOMER_ID', 'CUSTOMERS', 'CUSTOMER_ID', 'FOREIGN_KEY', 'ONE_TO_ONE', 'Each customer has one CLV record', CURRENT_TIMESTAMP());

-- ============================================================================
-- CREATE BUSINESS_CONTEXT TABLE
-- ============================================================================

CREATE TABLE BUSINESS_CONTEXT (
    CONTEXT_ID VARCHAR,
    RULE_TYPE VARCHAR,
    RULE_NAME VARCHAR,
    RULE_DESCRIPTION VARCHAR,
    THRESHOLD_VALUE NUMBER,
    RULE_VALUE VARCHAR,
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

INSERT INTO BUSINESS_CONTEXT VALUES
('BC001', 'CHURN_RISK', 'HIGH_RISK', 'Churn risk > 25%', 25.00, 'HIGH_RISK', CURRENT_TIMESTAMP()),
('BC002', 'CHURN_RISK', 'MEDIUM_RISK', 'Churn risk 15-25%', 15.00, 'MEDIUM_RISK', CURRENT_TIMESTAMP()),
('BC003', 'CHURN_RISK', 'LOW_RISK', 'Churn risk < 15%', 15.00, 'LOW_RISK', CURRENT_TIMESTAMP()),
('BC004', 'QUOTA_ATTAINMENT', 'EXCEEDING', 'Quota > 110%', 110.00, 'EXCEEDING', CURRENT_TIMESTAMP()),
('BC005', 'QUOTA_ATTAINMENT', 'ON_TRACK', 'Quota 85-110%', 85.00, 'ON_TRACK', CURRENT_TIMESTAMP()),
('BC006', 'QUOTA_ATTAINMENT', 'UNDERPERFORMING', 'Quota < 85%', 85.00, 'UNDERPERFORMING', CURRENT_TIMESTAMP()),
('BC007', 'INVENTORY_STATUS', 'CRITICAL', 'Below safety stock', 0.00, 'CRITICAL', CURRENT_TIMESTAMP()),
('BC008', 'INVENTORY_STATUS', 'WARNING', 'Below 1.5x safety stock', 1.50, 'WARNING', CURRENT_TIMESTAMP()),
('BC009', 'INVENTORY_STATUS', 'OK', 'At or above recommended', 1.50, 'OK', CURRENT_TIMESTAMP()),
('BC010', 'PRODUCT_GROWTH', 'HIGH_GROWTH', 'Growth > 15%', 15.00, 'HIGH_GROWTH', CURRENT_TIMESTAMP()),
('BC011', 'PRODUCT_GROWTH', 'MODERATE_GROWTH', 'Growth 5-15%', 5.00, 'MODERATE_GROWTH', CURRENT_TIMESTAMP()),
('BC012', 'PRODUCT_GROWTH', 'DECLINING', 'Growth < 5%', 5.00, 'DECLINING', CURRENT_TIMESTAMP());

-- ============================================================================
-- CREATE ANALYST_QUERY_LOG TABLE
-- ============================================================================


CREATE OR REPLACE TABLE ANALYST_QUERY_LOG
(
    REQUEST_ID              VARCHAR,
    QUERY_TIMESTAMP         TIMESTAMP_NTZ,
    USER_NAME               VARCHAR,
    USER_QUESTION           VARCHAR,
    GENERATED_SQL           VARCHAR,
    RESPONSE                VARCHAR,
    EXECUTION_TIME_SECONDS  NUMBER(12,2),
    SEMANTIC_MODEL_NAME     VARCHAR,
    RESPONSE_STATUS_CODE    NUMBER,
    AGENT_REQUEST_ID        VARCHAR
);
-- ============================================================================
-- CREATE AGENT_SAMPLE_QUERIES TABLE
-- ============================================================================

CREATE TABLE AGENT_SAMPLE_QUERIES (
    QUERY_ID VARCHAR DEFAULT UUID_STRING(),
    QUESTION_CATEGORY VARCHAR,
    SAMPLE_QUESTION VARCHAR,
    TABLES_INVOLVED VARCHAR,
    BUSINESS_RULES_APPLIED VARCHAR,
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

INSERT INTO AGENT_SAMPLE_QUERIES VALUES
('Q001', 'CUSTOMER_ANALYSIS', 'Show me top 10 customers by revenue', 'CUSTOMERS, ORDERS', 'NONE', CURRENT_TIMESTAMP()),
('Q002', 'CUSTOMER_ANALYSIS', 'Which customers have high churn risk?', 'CUSTOMERS, CUSTOMER_LIFETIME_VALUE', 'CHURN_RISK', CURRENT_TIMESTAMP()),
('Q003', 'SALES_PERFORMANCE', 'Which sales reps are underperforming?', 'SALES_REPS, SALES_PERFORMANCE', 'QUOTA_ATTAINMENT', CURRENT_TIMESTAMP()),
('Q004', 'PRODUCT_ANALYSIS', 'What products are trending?', 'PRODUCTS', 'PRODUCT_GROWTH', CURRENT_TIMESTAMP()),
('Q005', 'INVENTORY', 'Show inventory alerts', 'PRODUCTS, PRODUCT_INVENTORY', 'INVENTORY_STATUS', CURRENT_TIMESTAMP()),
('Q006', 'CUSTOMER_VALUE', 'Customer lifetime value analysis', 'CUSTOMERS, CUSTOMER_LIFETIME_VALUE', 'LTV_METRICS', CURRENT_TIMESTAMP());

-- ============================================================================
-- VERIFY TABLES
-- ============================================================================

SELECT 'Semantic Layer Created Successfully' AS STATUS;

CREATE TABLE IF NOT EXISTS SALES_DATA.PUBLIC.ANALYST_QUERY_AUDIT_LOG
(
    QUERY_ID              STRING,
    QUERY_TIMESTAMP       TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
    USER_NAME             STRING,
    REQUEST_ID            STRING,
    USER_QUESTION         STRING,
    ANALYST_QUESTION      STRING,
    RESPONSE              STRING,
    GENERATED_SQL         STRING,
    EXECUTION_STATUS      STRING,
    ANALYST_SECONDS       NUMBER(18,3),
    EXECUTION_SECONDS     NUMBER(18,3),
    ROWS_RETURNED         NUMBER,
    ERROR_MESSAGE         STRING,
    SEMANTIC_MODEL_NAME   STRING,
    APPLICATION_NAME      STRING
);

CREATE TABLE IF NOT EXISTS SALES_DATA.PUBLIC.ANALYST_QUERY_FEEDBACK
(
    QUERY_ID              STRING,
    FEEDBACK_TIMESTAMP     TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
    USER_NAME             STRING,
    FEEDBACK              STRING
);