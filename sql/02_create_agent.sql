-- ============================================================================
-- SNOWFLAKE NATIVE AGENT CREATION
-- Purpose: Create Cortex-powered agent for natural language queries
-- Environment: DEV/TEST/PROD (environment-agnostic)
-- ============================================================================

USE DATABASE SALES_DATA;
USE SCHEMA PUBLIC;

-- ============================================================================
-- STEP 1: CREATE QUERY EXECUTION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION EXECUTE_AGENT_QUERY(query_text VARCHAR)
RETURNS TABLE (RESULT VARIANT)
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
AS $$
def execute_agent_query(query_text):
    try:
        result = _snowflake.execute_string(query_text)
        rows = []
        while result.next():
            rows.append(dict(result.get_values()))
        return rows if rows else [{"INFO": "Query executed successfully with no results"}]
    except Exception as e:
        return [{"ERROR": str(e)}]
$$;

-- ============================================================================
-- STEP 2: CREATE SCHEMA CONTEXT FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION GET_SCHEMA_CONTEXT()
RETURNS VARCHAR
LANGUAGE SQL
AS $$
    SELECT STRING_AGG(
        'TABLE: ' || TABLE_NAME || 
        ' - ' || TABLE_DESCRIPTION || 
        ' (Columns: ' || STRING_AGG(COLUMN_NAME || ' (' || COLUMN_TYPE || ')', ', ') || ')',
        ' | '
    ) 
    FROM DATA_DICTIONARY
    GROUP BY TABLE_NAME
$$;

-- ============================================================================
-- STEP 3: CREATE AGENT
-- ============================================================================

CREATE OR REPLACE AGENT SNOWFLAKE_DATA_AGENT
    USER_CREATED_TOOL = TRUE
    COMMENT = 'Cortex-powered agent for natural language Snowflake queries'
AS $$
You are an expert Snowflake analyst and SQL specialist. Your role is to help users query a sales database.

IMPORTANT RULES:
1. ONLY generate SELECT queries - read-only access
2. ALWAYS reference the semantic layer tables to understand schema:
   - DATA_DICTIONARY: Contains table and column information
   - TABLE_RELATIONSHIPS: Contains join information
   - BUSINESS_CONTEXT: Contains business rules and thresholds
3. Use correct JOINs based on foreign key relationships
4. Return ALL results (no row limits unless requested)
5. Format results clearly and explain what data is shown
6. Apply business context thresholds when relevant:
   - Churn Risk: HIGH_RISK > 25%, MEDIUM_RISK > 15%
   - Quota: EXCEEDING > 110%, ON_TRACK 85-110%, UNDERPERFORMING < 85%
   - Inventory: CRITICAL < safety_stock, WARNING < safety_stock * 1.5
   - Growth: HIGH_GROWTH > 15%, MODERATE > 5%, DECLINING ≤ 5%

WORKFLOW:
1. Understand the user question
2. Query DATA_DICTIONARY to find relevant tables
3. Query TABLE_RELATIONSHIPS to find correct JOINs
4. Query BUSINESS_CONTEXT for applicable thresholds
5. Generate the SQL query
6. Execute and return results

EXAMPLE QUESTIONS YOU SHOULD HANDLE:
- "Show me top 10 customers by revenue"
- "Which sales reps are underperforming?"
- "What products are trending?"
- "Which customers have high churn risk?"
- "Show me inventory alerts"
- "What's our demand forecast for next month?"
- "Customer lifetime value analysis"
- "Top performing products by category"
- "Sales performance comparison between reps"
- "Manufacturing deadlines and risks"

If a question is ambiguous, ask for clarification before generating SQL.
$$;

-- ============================================================================
-- STEP 4: GRANT PERMISSIONS TO AGENTS
-- ============================================================================

GRANT USAGE ON DATABASE SALES_DATA TO ROLE ACCOUNTADMIN;
GRANT USAGE ON SCHEMA PUBLIC TO ROLE ACCOUNTADMIN;
GRANT SELECT ON ALL TABLES IN SCHEMA PUBLIC TO ROLE ACCOUNTADMIN;
GRANT EXECUTE ON FUNCTION EXECUTE_AGENT_QUERY(VARCHAR) TO ROLE ACCOUNTADMIN;
GRANT EXECUTE ON FUNCTION GET_SCHEMA_CONTEXT() TO ROLE ACCOUNTADMIN;

-- ============================================================================
-- STEP 5: VERIFY AGENT CREATION
-- ============================================================================

SELECT AGENT_NAME, AGENT_STATUS, CREATED_AT
FROM INFORMATION_SCHEMA.AGENTS
WHERE AGENT_NAME = 'SNOWFLAKE_DATA_AGENT';

-- ============================================================================
-- END OF AGENT CREATION
-- ============================================================================