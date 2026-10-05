-- ============================================================================
-- AUTOMATIC AUDIT LOGGING FOR ANALYST UI QUERIES
-- ============================================================================
-- Purpose: Automatically capture all Analyst questions asked in Snowflake UI
-- How: Background task scans query history every minute
--      Finds all Analyst queries
--      Auto-inserts them into ANALYST_QUERY_LOG
-- Database: SALES_DATA
-- Schema: PUBLIC
-- ============================================================================

USE DATABASE SALES_DATA;
USE SCHEMA PUBLIC;


-- ============================================================================
-- STEP 1: CREATE PROCEDURE TO AUTO-CAPTURE FROM QUERY HISTORY
-- ============================================================================

CREATE OR REPLACE PROCEDURE CAPTURE_ANALYST_QUERIES_FROM_HISTORY()
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
DECLARE
    v_captured_count INTEGER DEFAULT 0;
BEGIN

    INSERT INTO ANALYST_QUERY_LOG
    (
        QUERY_ID,
        QUERY_TIMESTAMP,
        USER_NAME,
        QUERY_TEXT,
        RESPONSE,
        EXECUTION_TIME_SECONDS
    )
    SELECT
        qh.QUERY_ID,
        qh.START_TIME,
        qh.USER_NAME,
        qh.QUERY_TEXT,
        'Auto-captured from Cortex Analyst query history',
        ROUND(qh.EXECUTION_TIME / 1000.0, 2)
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY qh
    WHERE qh.START_TIME >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'

      -- Cortex Analyst-related queries
      AND qh.QUERY_TEXT ILIKE '%SALES_SEMANTIC_MODEL%'

      -- Don't capture the logging procedure itself
      AND qh.QUERY_TEXT NOT ILIKE '%CAPTURE_ANALYST_QUERIES_FROM_HISTORY%'

      -- Don't capture the task itself
      AND qh.QUERY_TEXT NOT ILIKE '%CAPTURE_ANALYST_QUERIES_TASK%'

      -- Prevent duplicates using Snowflake's unique query ID
      AND NOT EXISTS
      (
          SELECT 1
          FROM ANALYST_QUERY_LOG aql
          WHERE aql.QUERY_ID = qh.QUERY_ID
      )

    ORDER BY qh.START_TIME
    LIMIT 100;

    SELECT COUNT(*)
    INTO :v_captured_count
    FROM ANALYST_QUERY_LOG
    WHERE QUERY_ID IN
    (
        SELECT QUERY_ID
        FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
        WHERE START_TIME >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
          AND QUERY_TEXT ILIKE '%SALES_SEMANTIC_MODEL%'
    );

    RETURN 'Captured Analyst queries. Total matching records processed: '
           || v_captured_count;

END;
$$;
-- ============================================================================
-- STEP 1.1: CREATE TASK TO RUN EVERY MINUTE
-- ============================================================================

CREATE OR REPLACE TASK CAPTURE_ANALYST_QUERIES_TASK
WAREHOUSE = COMPUTE_WH
SCHEDULE = '1 minute'
AS
CALL CAPTURE_ANALYST_QUERIES_FROM_HISTORY();

-- ============================================================================
-- STEP 1.2: ENABLE THE TASK
-- ============================================================================

--ALTER TASK CAPTURE_ANALYST_QUERIES_TASK RESUME;

