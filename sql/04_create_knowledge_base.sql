-- ============================================================================
-- AGENT KNOWLEDGE BASE - HELPER FUNCTIONS
-- Purpose: Create helper functions for agent to access schema information
-- Environment: DEV/TEST/PROD (environment-agnostic)
-- ============================================================================

USE DATABASE SALES_DATA;
USE SCHEMA PUBLIC;

-- ============================================================================
-- STEP 1: GET TABLE INFORMATION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION GET_TABLE_INFO(table_name_param VARCHAR)
RETURNS TABLE (
    TABLE_NAME VARCHAR,
    TABLE_DESCRIPTION VARCHAR,
    COLUMN_NAME VARCHAR,
    COLUMN_TYPE VARCHAR,
    COLUMN_DESCRIPTION VARCHAR,
    IS_KEY BOOLEAN
)
LANGUAGE SQL
AS $$
    SELECT 
        TABLE_NAME,
        TABLE_DESCRIPTION,
        COLUMN_NAME,
        COLUMN_TYPE,
        COLUMN_DESCRIPTION,
        IS_KEY
    FROM DATA_DICTIONARY
    WHERE UPPER(TABLE_NAME) = UPPER(table_name_param)
    ORDER BY COLUMN_NAME
$$;

-- ============================================================================
-- STEP 2: GET TABLE RELATIONSHIPS FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION GET_TABLE_JOINS(table_name_param VARCHAR)
RETURNS TABLE (
    SOURCE_TABLE VARCHAR,
    SOURCE_COLUMN VARCHAR,
    TARGET_TABLE VARCHAR,
    TARGET_COLUMN VARCHAR,
    JOIN_SYNTAX VARCHAR,
    RELATIONSHIP_DESCRIPTION VARCHAR
)
LANGUAGE SQL
AS $$
    SELECT 
        SOURCE_TABLE,
        SOURCE_COLUMN,
        TARGET_TABLE,
        TARGET_COLUMN,
        CONCAT(
            'JOIN ', TARGET_TABLE, ' ON ',
            SOURCE_TABLE, '.', SOURCE_COLUMN, ' = ',
            TARGET_TABLE, '.', TARGET_COLUMN
        ) AS JOIN_SYNTAX,
        RELATIONSHIP_DESCRIPTION
    FROM TABLE_RELATIONSHIPS
    WHERE UPPER(SOURCE_TABLE) = UPPER(table_name_param)
    OR UPPER(TARGET_TABLE) = UPPER(table_name_param)
    ORDER BY SOURCE_TABLE, TARGET_TABLE
$$;

-- ============================================================================
-- STEP 3: GET BUSINESS RULES FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION GET_BUSINESS_RULES(rule_type_param VARCHAR)
RETURNS TABLE (
    RULE_TYPE VARCHAR,
    RULE_NAME VARCHAR,
    RULE_DESCRIPTION VARCHAR,
    THRESHOLD_VALUE NUMBER,
    RULE_VALUE VARCHAR
)
LANGUAGE SQL
AS $$
    SELECT 
        RULE_TYPE,
        RULE_NAME,
        RULE_DESCRIPTION,
        THRESHOLD_VALUE,
        RULE_VALUE
    FROM BUSINESS_CONTEXT
    WHERE RULE_TYPE = rule_type_param
    ORDER BY THRESHOLD_VALUE DESC
$$;

-- ============================================================================
-- STEP 4: GET ALL AVAILABLE TABLES FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION GET_ALL_TABLES()
RETURNS TABLE (
    TABLE_NAME VARCHAR,
    TABLE_DESCRIPTION VARCHAR,
    COLUMN_COUNT NUMBER
)
LANGUAGE SQL
AS $$
    SELECT 
        TABLE_NAME,
        TABLE_DESCRIPTION,
        COUNT(DISTINCT COLUMN_NAME) AS COLUMN_COUNT
    FROM DATA_DICTIONARY
    GROUP BY TABLE_NAME, TABLE_DESCRIPTION
    ORDER BY TABLE_NAME
$$;

-- ============================================================================
-- STEP 5: CREATE SAMPLE QUERIES REFERENCE TABLE
-- ============================================================================

CREATE OR REPLACE TABLE AGENT_SAMPLE_QUERIES (
    QUERY_ID VARCHAR DEFAULT UUID_STRING(),
    QUESTION_CATEGORY VARCHAR,
    SAMPLE_QUESTION VARCHAR,
    TABLES_INVOLVED VARCHAR,
    BUSINESS_RULES_APPLIED VARCHAR,
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

INSERT INTO AGENT_SAMPLE_QUERIES (QUESTION_CATEGORY, SAMPLE_QUESTION, TABLES_INVOLVED, BUSINESS_RULES_APPLIED)
VALUES
('CUSTOMER_ANALYSIS', 'Show me top 10 customers by revenue', 'CUSTOMERS, ORDERS, ORDER_ITEMS', 'NONE'),
('CUSTOMER_ANALYSIS', 'Which customers have high churn risk?', 'CUSTOMERS, CUSTOMER_LIFETIME_VALUE', 'CHURN_RISK'),
('CUSTOMER_ANALYSIS', 'Show me customer lifetime value breakdown', 'CUSTOMERS, CUSTOMER_LIFETIME_VALUE', 'LTV_METRICS'),
('CUSTOMER_ANALYSIS', 'Which customers purchased in the last 30 days?', 'CUSTOMERS, ORDERS', 'DATE_FILTER'),

('SALES_PERFORMANCE', 'Which sales reps are underperforming?', 'SALES_REPS, SALES_PERFORMANCE', 'QUOTA_ATTAINMENT'),
('SALES_PERFORMANCE', 'Show me sales rep performance comparison', 'SALES_REPS, SALES_PERFORMANCE', 'QUOTA_ATTAINMENT'),
('SALES_PERFORMANCE', 'Who is the top performing sales rep this month?', 'SALES_REPS, SALES_PERFORMANCE', 'TOP_PERFORMERS'),
('SALES_PERFORMANCE', 'What is the pipeline value by sales rep?', 'SALES_REPS, SALES_PERFORMANCE', 'PIPELINE_ANALYSIS'),

('PRODUCT_ANALYSIS', 'What products are trending?', 'PRODUCTS, PRODUCT_DEMAND_FREQUENCY', 'PRODUCT_GROWTH'),
('PRODUCT_ANALYSIS', 'Top 5 products by revenue', 'PRODUCTS, PRODUCT_DEMAND_FREQUENCY, ORDER_ITEMS', 'REVENUE_ANALYSIS'),
('PRODUCT_ANALYSIS', 'Show products by category and growth', 'PRODUCTS, PRODUCT_DEMAND_FREQUENCY', 'CATEGORIZATION'),
('PRODUCT_ANALYSIS', 'Which products have declining demand?', 'PRODUCTS, PRODUCT_DEMAND_FREQUENCY', 'GROWTH_ANALYSIS'),

('INVENTORY', 'Show inventory alerts', 'PRODUCTS, PRODUCT_INVENTORY, PRODUCT_DEMAND_FREQUENCY', 'INVENTORY_STATUS'),
('INVENTORY', 'Which products need reordering?', 'PRODUCTS, PRODUCT_INVENTORY, PRODUCT_DEMAND_FREQUENCY', 'REORDER_LEVEL'),
('INVENTORY', 'Current inventory status by product', 'PRODUCTS, PRODUCT_INVENTORY', 'STOCK_STATUS'),
('INVENTORY', 'Products with critical stock levels', 'PRODUCTS, PRODUCT_INVENTORY, PRODUCT_DEMAND_FREQUENCY', 'CRITICAL_INVENTORY'),

('FORECASTING', 'Show demand forecast for next month', 'PRODUCTS, DEMAND_FORECAST, PRODUCT_INVENTORY', 'FORECAST_ANALYSIS'),
('FORECASTING', 'Which products need urgent manufacturing?', 'PRODUCTS, DEMAND_FORECAST, PRODUCT_INVENTORY', 'MANUFACTURING_URGENCY'),
('FORECASTING', 'Manufacturing deadlines and risks', 'PRODUCTS, DEMAND_FORECAST', 'RISK_ASSESSMENT'),
('FORECASTING', 'Show me production schedule with inventory gaps', 'PRODUCTS, DEMAND_FORECAST, PRODUCT_INVENTORY', 'PRODUCTION_PLANNING');

-- ============================================================================
-- STEP 6: CREATE COMMON METRICS CALCULATION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION CALCULATE_KEY_METRICS()
RETURNS TABLE (
    METRIC_NAME VARCHAR,
    METRIC_VALUE VARCHAR,
    METRIC_DESCRIPTION VARCHAR
)
LANGUAGE SQL
AS $$
    SELECT 
        'Total Customers' AS METRIC_NAME,
        COUNT(DISTINCT CUSTOMER_ID)::VARCHAR AS METRIC_VALUE,
        'Total unique customers in database' AS METRIC_DESCRIPTION
    FROM CUSTOMERS
    UNION ALL
    SELECT 
        'Total Orders',
        COUNT(DISTINCT ORDER_ID)::VARCHAR,
        'Total sales orders processed'
    FROM ORDERS
    UNION ALL
    SELECT 
        'Total Products',
        COUNT(DISTINCT PRODUCT_ID)::VARCHAR,
        'Total products in catalog'
    FROM PRODUCTS
    UNION ALL
    SELECT 
        'Active Sales Reps',
        COUNT(DISTINCT REP_ID)::VARCHAR,
        'Sales representatives on team'
    FROM SALES_REPS
    UNION ALL
    SELECT 
        'Total Revenue',
        ROUND(SUM(FINAL_VALUE), 2)::VARCHAR,
        'Total revenue from all orders'
    FROM ORDERS
$$;

-- ============================================================================
-- STEP 7: VERIFY KNOWLEDGE BASE CREATION
-- ============================================================================

SELECT 'Knowledge Base Status' AS COMPONENT, COUNT(*) AS OBJECT_COUNT
FROM (
    SELECT 1 FROM GET_ALL_TABLES() LIMIT 1
    UNION ALL
    SELECT 1 FROM AGENT_SAMPLE_QUERIES LIMIT 1
)
GROUP BY COMPONENT;

-- ============================================================================
-- END OF KNOWLEDGE BASE CREATION
-- ============================================================================