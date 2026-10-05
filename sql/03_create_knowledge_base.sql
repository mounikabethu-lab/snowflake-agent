-- ============================================================================
-- CREATE KNOWLEDGE BASE
-- ============================================================================

USE DATABASE SALES_DATA;
USE SCHEMA PUBLIC;

-- ============================================================================
-- CREATE AGENT INSTRUCTIONS TABLE
-- ============================================================================

CREATE OR REPLACE TABLE AGENT_INSTRUCTIONS (
    INSTRUCTION_ID VARCHAR DEFAULT UUID_STRING(),
    INSTRUCTION_TEXT VARCHAR,
    CATEGORY VARCHAR,
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

INSERT INTO AGENT_INSTRUCTIONS VALUES
('I001', 'Only generate SELECT queries for read-only access', 'SECURITY', CURRENT_TIMESTAMP()),
('I002', 'Always apply business context thresholds when analyzing data', 'BUSINESS_LOGIC', CURRENT_TIMESTAMP()),
('I003', 'Churn Risk > 25% is HIGH - flag for intervention', 'BUSINESS_RULE', CURRENT_TIMESTAMP()),
('I004', 'Quota Attainment < 85% means UNDERPERFORMING', 'BUSINESS_RULE', CURRENT_TIMESTAMP()),
('I005', 'Inventory below REORDER_LEVEL is CRITICAL', 'BUSINESS_RULE', CURRENT_TIMESTAMP()),
('I006', 'Use SUM for revenue, COUNT for transactions, AVG for metrics', 'QUERY_PATTERN', CURRENT_TIMESTAMP()),
('I007', 'JOIN tables on foreign keys - do not use cross joins', 'QUERY_PATTERN', CURRENT_TIMESTAMP()),
('I008', 'Always return row counts and totals in analysis', 'RESPONSE_FORMAT', CURRENT_TIMESTAMP()),
('I009', 'Explain findings in business terms not technical SQL', 'COMMUNICATION', CURRENT_TIMESTAMP()),
('I010', 'Suggest action items when presenting risks or opportunities', 'COMMUNICATION', CURRENT_TIMESTAMP());

-- ============================================================================
-- CREATE KNOWLEDGE BASE TABLE
-- ============================================================================

CREATE OR REPLACE TABLE KNOWLEDGE_BASE (
    KNOWLEDGE_ID VARCHAR DEFAULT UUID_STRING(),
    KNOWLEDGE_CATEGORY VARCHAR,
    KNOWLEDGE_CONTENT VARCHAR,
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

INSERT INTO KNOWLEDGE_BASE VALUES
('KB001', 'TABLE_SCHEMA', 'CUSTOMERS contains: CUSTOMER_ID (PK), CUSTOMER_NAME, INDUSTRY, COMPANY_SIZE', CURRENT_TIMESTAMP()),
('KB002', 'TABLE_SCHEMA', 'ORDERS contains: ORDER_ID (PK), CUSTOMER_ID (FK), REP_ID (FK), ORDER_DATE, FINAL_VALUE', CURRENT_TIMESTAMP()),
('KB003', 'TABLE_SCHEMA', 'SALES_PERFORMANCE contains: PERF_ID (PK), REP_ID (FK), PERFORMANCE_MONTH, QUOTA, ACTUAL_REVENUE, QUOTA_ATTAINMENT_PERCENT, DEALS_WON, DEALS_LOST, PIPELINE_VALUE', CURRENT_TIMESTAMP()),
('KB004', 'TABLE_SCHEMA', 'CUSTOMER_LIFETIME_VALUE contains: CLV_ID (PK), CUSTOMER_ID (FK), TOTAL_REVENUE, PREDICTED_LTV, CHURN_RISK_PERCENT, RENEWAL_LIKELIHOOD_PERCENT, AVERAGE_ORDER_VALUE, TOTAL_ORDERS, LAST_ORDER_DATE', CURRENT_TIMESTAMP()),
('KB005', 'ANALYSIS_PATTERN', 'Top customers by revenue: GROUP BY CUSTOMER_NAME, SUM(FINAL_VALUE), ORDER BY DESC', CURRENT_TIMESTAMP()),
('KB006', 'ANALYSIS_PATTERN', 'Sales rep performance: Filter SALES_PERFORMANCE, calculate QUOTA_ATTAINMENT_PERCENT status', CURRENT_TIMESTAMP()),
('KB007', 'ANALYSIS_PATTERN', 'High churn risk: Filter CUSTOMER_LIFETIME_VALUE where CHURN_RISK_PERCENT > 25%', CURRENT_TIMESTAMP()),
('KB008', 'ANALYSIS_PATTERN', 'Inventory alerts: Filter PRODUCT_INVENTORY where QUANTITY_AVAILABLE < REORDER_LEVEL', CURRENT_TIMESTAMP()),
('KB009', 'BUSINESS_METRIC', 'Customer Lifetime Value = TOTAL_REVENUE + PREDICTED_LTV for full customer value', CURRENT_TIMESTAMP()),
('KB010', 'BUSINESS_METRIC', 'Quota Attainment % = (ACTUAL_REVENUE / QUOTA) * 100', CURRENT_TIMESTAMP());

-- ============================================================================
-- VERIFY KNOWLEDGE BASE
-- ============================================================================

SELECT 'Knowledge Base Created' AS STATUS;