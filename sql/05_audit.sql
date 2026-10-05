-- ============================================================================
-- AUTOMATIC AUDIT LOGGING FOR ANALYST UI QUERIES
-- ============================================================================

USE DATABASE SALES_DATA;

USE SCHEMA PUBLIC;


-- ============================================================================
-- CREATE PROCEDURE
-- ============================================================================

CREATE OR REPLACE PROCEDURE CAPTURE_ANALYST_QUERIES_FROM_HISTORY()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
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
      AND qh.QUERY_TEXT ILIKE '%SALES_SEMANTIC_MODEL%'
      AND qh.EXECUTION_STATUS = 'SUCCESS'
      AND qh.QUERY_TEXT NOT ILIKE '%CAPTURE_ANALYST_QUERIES_FROM_HISTORY%'
      AND qh.QUERY_TEXT NOT ILIKE '%CAPTURE_ANALYST_QUERIES_TASK%'
      AND NOT EXISTS
      (
          SELECT 1
          FROM ANALYST_QUERY_LOG aql
          WHERE aql.QUERY_ID = qh.QUERY_ID
      )
    ORDER BY qh.START_TIME
    LIMIT 100;

    RETURN 'Capture procedure executed successfully';

END;
$$;


-- ============================================================================
-- CREATE TASK
-- ============================================================================

CREATE OR REPLACE TASK CAPTURE_ANALYST_QUERIES_TASK
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = '1 MINUTE'
AS
    CALL CAPTURE_ANALYST_QUERIES_FROM_HISTORY();


-- ============================================================================
-- ENABLE TASK
-- ============================================================================

-- ALTER TASK CAPTURE_ANALYST_QUERIES_TASK RESUME;