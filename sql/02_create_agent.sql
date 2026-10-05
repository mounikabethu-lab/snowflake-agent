-- ============================================================================
-- SNOWFLAKE CORTEX AGENT CREATION
-- ============================================================================

USE DATABASE SALES_DATA;
USE SCHEMA PUBLIC;

-- ============================================================================
-- STEP 1: CREATE AGENT WITH PROPER SYNTAX
-- ============================================================================

CREATE AGENT SNOWFLAKE_DATA_AGENT
COMMENT = 'Cortex Agent for Sales Data Analysis'
SYSTEM_PROMPT = $$You are an expert sales data analyst helping users analyze sales data.

Available Data:
- CUSTOMERS: Customer information and profiles
- ORDERS: Sales transactions and values
- SALES_REPS: Sales team and performance
- PRODUCTS: Product catalog
- SALES_PERFORMANCE: Monthly metrics and quotas
- CUSTOMER_LIFETIME_VALUE: Customer value and churn risk

Instructions:
1. Answer questions about sales data
2. Use only SELECT queries
3. Apply business rules:
   - Churn Risk: HIGH (>25%), MEDIUM (15-25%), LOW (<15%)
   - Quota: EXCEEDING (>110%), ON_TRACK (85-110%), UNDERPERFORMING (<85%)
   - Growth: HIGH (>15%), MODERATE (5-15%), DECLINING (<5%)
4. Provide clear insights and summaries
5. Always explain findings$$;

-- ============================================================================
-- STEP 2: GRANT PERMISSIONS
-- ============================================================================

GRANT USAGE ON DATABASE SALES_DATA TO ROLE ACCOUNTADMIN;
GRANT USAGE ON SCHEMA PUBLIC TO ROLE ACCOUNTADMIN;
GRANT SELECT ON ALL TABLES IN SCHEMA PUBLIC TO ROLE ACCOUNTADMIN;
GRANT OPERATE ON AGENT SNOWFLAKE_DATA_AGENT TO ROLE ACCOUNTADMIN;

-- ============================================================================
-- STEP 3: VERIFY AGENT CREATION
-- ============================================================================

SELECT AGENT_NAME, AGENT_STATUS, CREATED_AT
FROM INFORMATION_SCHEMA.AGENTS
WHERE AGENT_NAME = 'SNOWFLAKE_DATA_AGENT';