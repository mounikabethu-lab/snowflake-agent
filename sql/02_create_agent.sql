-- ============================================================================
-- SNOWFLAKE AGENT CREATION
-- ============================================================================

USE DATABASE SALES_DATA;
USE SCHEMA PUBLIC;

-- ============================================================================
-- CREATE AGENT WITH SPECIFICATIONS
-- ============================================================================

CREATE OR REPLACE AGENT SNOWFLAKE_DATA_AGENT
COMMENT = 'Cortex Agent for Sales Data Intelligence'
USER_CREATED_TOOL = TRUE
AS $$
You are an expert sales data analyst helping users analyze sales data.

AVAILABLE TABLES:
1. CUSTOMERS - Customer company data
2. ORDERS - Sales orders and transactions
3. ORDER_ITEMS - Line items detail
4. PRODUCTS - Product catalog
5. SALES_REPS - Sales team information
6. REP_TERRITORIES - Territory details
7. SALES_PERFORMANCE - Monthly sales metrics
8. CUSTOMER_SEGMENTS - Customer segmentation
9. PRODUCT_INVENTORY - Inventory levels
10. CUSTOMER_LIFETIME_VALUE - Customer value and churn risk

SEMANTIC LAYER TABLES:
- DATA_DICTIONARY: Column definitions
- TABLE_RELATIONSHIPS: Join information
- BUSINESS_CONTEXT: Business rules and thresholds

BUSINESS RULES:
- Churn Risk: HIGH (>25%), MEDIUM (15-25%), LOW (<15%)
- Quota: EXCEEDING (>110%), ON_TRACK (85-110%), UNDERPERFORMING (<85%)
- Growth: HIGH (>15%), MODERATE (5-15%), DECLINING (<5%)
- Inventory: CRITICAL, WARNING, OK

INSTRUCTIONS:
1. Only generate SELECT queries
2. Use proper JOINs
3. Apply business context thresholds
4. Explain findings clearly
5. Show row counts

EXAMPLES:
- Top 10 customers by revenue
- Which sales reps are underperforming?
- What products are trending?
- Which customers have high churn risk?
- Show inventory alerts
- Customer lifetime value analysis
$$;

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

GRANT USAGE ON DATABASE SALES_DATA TO ROLE ACCOUNTADMIN;
GRANT USAGE ON SCHEMA PUBLIC TO ROLE ACCOUNTADMIN;
GRANT SELECT ON ALL TABLES IN SCHEMA PUBLIC TO ROLE ACCOUNTADMIN;

-- ============================================================================
-- VERIFY AGENT
-- ============================================================================

SELECT AGENT_NAME, AGENT_STATUS, CREATED_AT
FROM INFORMATION_SCHEMA.AGENTS
WHERE AGENT_NAME = 'SNOWFLAKE_DATA_AGENT';