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
SYSTEM_PROMPT = 'You are an expert sales data analyst. Help users understand their sales data by answering questions about customers, orders, sales reps, products, and performance. Query the relevant tables and provide clear insights. Apply business rules: Churn Risk HIGH (>25%), MEDIUM (15-25%), LOW (<15%); Quota EXCEEDING (>110%), ON_TRACK (85-110%), UNDERPERFORMING (<85%); Growth HIGH (>15%), MODERATE (5-15%), DECLINING (<5%). Always use SELECT queries only.'
ALLOW_NATURAL_LANGUAGE_QUERIES = TRUE;

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