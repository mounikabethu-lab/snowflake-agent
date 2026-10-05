-- ============================================================================
-- AGENT CONFIGURATION
-- ============================================================================

USE DATABASE SALES_DATA;
USE SCHEMA PUBLIC;

-- ============================================================================
-- CREATE AGENT INSTRUCTION TABLE
-- ============================================================================

CREATE OR REPLACE TABLE AGENT_INSTRUCTIONS (
    INSTRUCTION_ID VARCHAR DEFAULT UUID_STRING(),
    INSTRUCTION_TEXT VARCHAR,
    CATEGORY VARCHAR,
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

INSERT INTO AGENT_INSTRUCTIONS (INSTRUCTION_TEXT, CATEGORY)
VALUES
('You are an expert Snowflake analyst helping users query sales data', 'PRIMARY'),
('ONLY generate SELECT queries - read-only access', 'SECURITY'),
('Reference DATA_DICTIONARY for table and column information', 'SEMANTIC'),
('Use TABLE_RELATIONSHIPS to find correct JOIN paths', 'SEMANTIC'),
('Apply BUSINESS_CONTEXT thresholds for analysis', 'BUSINESS'),
('Churn Risk: HIGH > 25%, MEDIUM 15-25%, LOW < 15%', 'THRESHOLD'),
('Quota Attainment: EXCEEDING > 110%, ON_TRACK 85-110%, UNDERPERFORMING < 85%', 'THRESHOLD'),
('Inventory Status: CRITICAL < safety_stock, WARNING < 1.5x, OK >= 1.5x', 'THRESHOLD'),
('Product Growth: HIGH > 15%, MODERATE 5-15%, DECLINING < 5%', 'THRESHOLD'),
('Ask for clarification if question is ambiguous', 'BEHAVIOR');

-- ============================================================================
-- CREATE QUERY LOGGING PROCEDURE
-- ============================================================================

CREATE OR REPLACE PROCEDURE LOG_AGENT_QUERY(
    question VARCHAR,
    sql_generated VARCHAR,
    status VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
    INSERT INTO AGENT_QUERY_LOG (QUESTION, GENERATED_SQL, EXECUTION_STATUS)
    VALUES (question, sql_generated, status);
    SELECT 'Query logged successfully' AS RESULT;
$$;

-- ============================================================================
-- VERIFY SETUP
-- ============================================================================

