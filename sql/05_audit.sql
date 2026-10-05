-- ============================================================================
-- AUTOMATIC AUDIT LOGGING FOR ANALYST UI QUERIES - FIXED
-- ============================================================================
-- Purpose: Automatically capture all Analyst questions asked in Snowflake UI
-- Database: SALES_DATA
-- Schema: PUBLIC
-- ============================================================================

USE DATABASE SALES_DATA;
USE SCHEMA PUBLIC;



-- ============================================================================
-- CREATE PROCEDURE TO AUTO-CAPTURE FROM QUERY HISTORY
-- ============================================================================

CREATE OR REPLACE PROCEDURE CAPTURE_ANALYST_QUERIES_FROM_HISTORY()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
BEGIN
    INSERT INTO ANALYST_QUERY_LOG (QUERY_TIMESTAMP, USER_NAME, QUERY_TEXT, RESPONSE, EXECUTION_TIME_SECONDS)
    SELECT
        qh.START_TIME,
        qh.USER_NAME,
        qh.QUERY_TEXT,
        'Auto-captured from Cortex Analyst query history',
        ROUND(qh.EXECUTION_TIME / 1000000000.0, 2)
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY qh
    WHERE qh.START_TIME >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
      AND qh.QUERY_TEXT ILIKE '%SALES_SEMANTIC_MODEL%'
      AND qh.EXECUTION_STATUS = 'SUCCESS'
      AND qh.QUERY_TEXT NOT ILIKE '%CAPTURE_ANALYST_QUERIES_FROM_HISTORY%'
      AND qh.QUERY_TEXT NOT ILIKE '%CAPTURE_ANALYST_QUERIES_TASK%'
      AND NOT EXISTS (
          SELECT 1 FROM ANALYST_QUERY_LOG aql
          WHERE aql.USER_NAME = qh.USER_NAME
          AND ABS(DATEDIFF(second, aql.QUERY_TIMESTAMP, qh.START_TIME)) < 60
      )
    ORDER BY qh.START_TIME
    LIMIT 100;
    
    RETURN 'Capture procedure executed successfully';
END;
 
-- ============================================================================
-- STEP 3: CREATE TASK TO RUN EVERY MINUTE
-- ============================================================================
 
CREATE OR REPLACE TASK CAPTURE_ANALYST_QUERIES_TASK
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = '1 MINUTE'
    AS
    CALL CAPTURE_ANALYST_QUERIES_FROM_HISTORY();
 
-- ============================================================================
-- ENABLE THE TASK
-- ============================================================================

--ALTER TASK CAPTURE_ANALYST_QUERIES_TASK RESUME;
