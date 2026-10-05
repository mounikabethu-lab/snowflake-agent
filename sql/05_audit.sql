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
        REQUEST_ID,
        QUERY_TIMESTAMP,
        USER_NAME,
        USER_QUESTION,
        GENERATED_SQL,
        RESPONSE,
        EXECUTION_TIME_SECONDS,
        SEMANTIC_MODEL_NAME,
        RESPONSE_STATUS_CODE,
        AGENT_REQUEST_ID
    )
    SELECT
        ca.REQUEST_ID,
        ca.TIMESTAMP,
        ca.USER_ID,
        ca.LATEST_QUESTION,
        ca.GENERATED_SQL,
        ca.RESPONSE_BODY::VARCHAR,
        NULL,
        ca.SEMANTIC_MODEL_NAME,
        ca.RESPONSE_STATUS_CODE,
        ca.SOURCE:agent_request_id::VARCHAR
    FROM SNOWFLAKE.LOCAL.CORTEX_ANALYST_REQUESTS_V ca
    WHERE ca.TIMESTAMP >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
      AND ca.REQUEST_ID IS NOT NULL
      AND NOT EXISTS
      (
          SELECT 1
          FROM ANALYST_QUERY_LOG aql
          WHERE aql.REQUEST_ID = ca.REQUEST_ID
      )
    ORDER BY ca.TIMESTAMP
    LIMIT 100;

    RETURN 'Cortex Analyst requests captured successfully';

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