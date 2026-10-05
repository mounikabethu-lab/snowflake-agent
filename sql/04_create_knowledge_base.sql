-- ============================================================================
-- KNOWLEDGE BASE SETUP
-- ============================================================================

USE DATABASE SALES_DATA;
USE SCHEMA PUBLIC;

-- ============================================================================
-- CREATE KNOWLEDGE BASE TABLE
-- ============================================================================

CREATE OR REPLACE TABLE KNOWLEDGE_BASE (
    KNOWLEDGE_ID VARCHAR DEFAULT UUID_STRING(),
    KNOWLEDGE_CATEGORY VARCHAR,
    KNOWLEDGE_CONTENT VARCHAR,
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

INSERT INTO KNOWLEDGE_BASE (KNOWLEDGE_CATEGORY, KNOWLEDGE_CONTENT)
VALUES
('SCHEMA_OVERVIEW', 'CUSTOMERS: Master customer data with industry and company size'),
('SCHEMA_OVERVIEW', 'ORDERS: Sales orders containing transaction data'),
('SCHEMA_OVERVIEW', 'ORDER_ITEMS: Line items with product and quantity details'),
('SCHEMA_OVERVIEW', 'PRODUCTS: Product catalog with pricing'),
('SCHEMA_OVERVIEW', 'SALES_REPS: Sales representative information and territory'),
('SCHEMA_OVERVIEW', 'SALES_PERFORMANCE: Monthly sales metrics and quota attainment'),
('SCHEMA_OVERVIEW', 'CUSTOMER_SEGMENTS: Customer segmentation and behavior'),
('SCHEMA_OVERVIEW', 'PRODUCT_INVENTORY: Current inventory levels and reorder points'),
('SCHEMA_OVERVIEW', 'CUSTOMER_LIFETIME_VALUE: Customer value and churn risk analysis'),
('COMMON_ANALYSIS', 'Top customers by revenue: JOIN CUSTOMERS to ORDERS and sum FINAL_VALUE'),
('COMMON_ANALYSIS', 'Sales rep performance: JOIN SALES_REPS to SALES_PERFORMANCE and check QUOTA_ATTAINMENT_PERCENT'),
('COMMON_ANALYSIS', 'Product trends: Analyze PRODUCT_DEMAND_FREQUENCY for GROWTH_TREND_PERCENT'),
('COMMON_ANALYSIS', 'Churn risk: Check CUSTOMER_LIFETIME_VALUE for CHURN_RISK_PERCENT > 25%'),
('COMMON_ANALYSIS', 'Inventory alerts: Compare PRODUCT_INVENTORY QUANTITY_AVAILABLE to REORDER_LEVEL'),
('BEST_PRACTICES', 'Always use meaningful WHERE clauses to filter data efficiently'),
('BEST_PRACTICES', 'Use INNER JOIN for required relationships, LEFT JOIN for optional'),
('BEST_PRACTICES', 'Apply business context thresholds from BUSINESS_CONTEXT table'),
('BEST_PRACTICES', 'Return results sorted by most relevant column'),
('BEST_PRACTICES', 'Include meaningful column aliases for clarity');

-- ============================================================================
-- CREATE METRICS CALCULATION VIEW
-- ============================================================================

CREATE OR REPLACE VIEW KEY_METRICS AS
SELECT 
    'Total Customers' AS METRIC,
    COUNT(DISTINCT CUSTOMER_ID) AS VALUE
FROM CUSTOMERS
UNION ALL
SELECT 
    'Total Orders',
    COUNT(DISTINCT ORDER_ID)
FROM ORDERS
UNION ALL
SELECT 
    'Total Products',
    COUNT(DISTINCT PRODUCT_ID)
FROM PRODUCTS
UNION ALL
SELECT 
    'Active Sales Reps',
    COUNT(DISTINCT REP_ID)
FROM SALES_REPS;

-- ============================================================================
-- VERIFY KNOWLEDGE BASE
-- ============================================================================

SELECT KNOWLEDGE_CATEGORY, COUNT(*) AS COUNT
FROM KNOWLEDGE_BASE
GROUP BY KNOWLEDGE_CATEGORY;