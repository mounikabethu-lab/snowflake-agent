-- ============================================================================
-- AUTOMATIC AUDIT LOGGING FOR ANALYST UI QUERIES
-- ============================================================================
-- Purpose:
--   Automatically capture Analyst-related queries from Snowflake query history.
--
-- How:
--   Background task scans query history every minute.
--   New queries referencing SALES_SEMANTIC_MODEL are inserted into
--   ANALYST_QUERY_LOG.
--
-- Database: SALES_DATA
-- Schema  : PUBLIC
-- ============================================================================

USE DATABASE SALES_DATA;
USE SCHEMA PUBLIC;


-- ============================================================================
-- STEP 1: CREATE AUDIT LOG TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS ANALYST_QUERY_LOG
(
    QUERY_ID                 VARCHAR,
    QUERY_TIMESTAMP          TIMESTAMP_LTZ,
    USER_NAME                VARCHAR,
    QUERY_TEXT               VARCHAR,
    RESPONSE                 VARCHAR,
    EXECUTION_TIME_SECONDS   NUMBER(12,2)
);


-- ============================================================================
-- STEP 2: CREATE PROCEDURE
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

      -- Cortex Analyst / semantic-view related queries
      AND qh.QUERY_TEXT ILIKE '%SALES_SEMANTIC_MODEL%'

      -- Do not capture this procedure itself
      AND qh.QUERY_TEXT NOT ILIKE '%CAPTURE_ANALYST_QUERIES_FROM_HISTORY%'

      -- Do not capture the task definition/execution
      AND qh.QUERY_TEXT NOT ILIKE '%CAPTURE_ANALYST_QUERIES_TASK%'

      -- Prevent duplicates
      AND NOT EXISTS
      (
          SELECT 1
          FROM ANALYST_QUERY_LOG aql
          WHERE aql.QUERY_ID = qh.QUERY_ID
      )

    ORDER BY qh.START_TIME
    LIMIT 100;

    -- Number of rows inserted by the INSERT above
    v_captured_count := SQLROWCOUNT;

    RETURN
        'Captured ' || v_captured_count ||
        ' new Analyst query record(s).';

END;
$$;


-- ============================================================================
-- STEP 3: CREATE TASK
-- ============================================================================

CREATE OR REPLACE TASK CAPTURE_ANALYST_QUERIES_TASK
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = '1 MINUTE'
AS
    CALL CAPTURE_ANALYST_QUERIES_FROM_HISTORY();


-- ============================================================================
-- STEP 4: ENABLE TASK
-- ============================================================================
-- New tasks are created suspended.
-- Uncomment this after successful deployment/testing.

-- ALTER TASK CAPTURE_ANALYST_QUERIES_TASK RESUME;