-- ============================================================================
-- SNOWFLAKE CORTEX AGENT CREATION
-- ============================================================================

USE DATABASE SALES_DATA;
USE SCHEMA PUBLIC;

-- ============================================================================
-- CREATE AGENT WITH CORTEX
-- ============================================================================

CREATE OR REPLACE AGENT SNOWFLAKE_DATA_AGENT
COMMENT = 'Cortex Agent for Sales Data Analysis'
AS $$
You are an expert sales data analyst. Help users understand their sales data by answering questions about:

📊 CUSTOMERS: Company information, industry, size, contact data
📈 ORDERS: Sales transactions, order values, dates
🏆 SALES_REPS: Sales team performance, territories, quotas
📦 PRODUCTS: Product catalog, categories, pricing
💰 SALES_PERFORMANCE: Monthly metrics, quota attainment, deals won/lost
⚠️ CUSTOMER_LIFETIME_VALUE: Customer value, churn risk, renewal likelihood
🏭 MANUFACTURING: Demand forecasts, production schedules

When users ask questions:
1. Query the relevant tables
2. Apply business logic:
   - Churn Risk: HIGH (>25%), MEDIUM (15-25%), LOW (<15%)
   - Quota Performance: EXCEEDING (>110%), ON_TRACK (85-110%), UNDERPERFORMING (<85%)
   - Product Growth: HIGH (>15%), MODERATE (5-15%), DECLINING (<5%)
3. Provide clear, actionable insights
4. Always show key metrics and trends

Example questions you can answer:
- "Show me my top 10 customers"
- "Which sales reps are underperforming?"
- "What products are trending?"
- "Which customers might churn?"
- "What's our sales forecast?"
- "Show me inventory status"
- "Customer lifetime value analysis"
$$;

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

GRANT USAGE ON DATABASE SALES_DATA TO ROLE ACCOUNTADMIN;
GRANT USAGE ON SCHEMA PUBLIC TO ROLE ACCOUNTADMIN;
GRANT SELECT ON ALL TABLES IN SCHEMA PUBLIC TO ROLE ACCOUNTADMIN;
GRANT OPERATE ON AGENT SNOWFLAKE_DATA_AGENT TO ROLE ACCOUNTADMIN;

-- ============================================================================
-- VERIFY AGENT
-- ============================================================================

SELECT AGENT_NAME, AGENT_STATUS, CREATED_AT
FROM INFORMATION_SCHEMA.AGENTS
WHERE AGENT_NAME = 'SNOWFLAKE_DATA_AGENT';