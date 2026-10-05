-- ============================================================================
-- DEPLOYMENT VERIFICATION
-- ============================================================================

USE DATABASE SALES_DATA;
USE SCHEMA PUBLIC;

SELECT '====== DEPLOYMENT VERIFICATION ======' AS STATUS;

-- ============================================================================
-- VERIFY TABLES
-- ============================================================================

SELECT 'SEMANTIC TABLES' AS COMPONENT, COUNT(*) AS COUNT
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'PUBLIC'
AND TABLE_NAME IN ('DATA_DICTIONARY', 'TABLE_RELATIONSHIPS', 'BUSINESS_CONTEXT', 'AGENT_QUERY_LOG', 'AGENT_SAMPLE_QUERIES', 'AGENT_INSTRUCTIONS', 'KNOWLEDGE_BASE');

-- ============================================================================
-- VERIFY AGENT
-- ============================================================================

SELECT 'AGENT' AS COMPONENT, COUNT(*) AS COUNT
FROM INFORMATION_SCHEMA.AGENTS
WHERE AGENT_NAME = 'SNOWFLAKE_DATA_AGENT';

-- ============================================================================
-- VERIFY FUNCTIONS
-- ============================================================================

SELECT 'FUNCTIONS' AS COMPONENT, COUNT(*) AS COUNT
FROM INFORMATION_SCHEMA.FUNCTIONS
WHERE FUNCTION_SCHEMA = 'PUBLIC';

-- ============================================================================
-- DATA SUMMARY
-- ============================================================================

SELECT 'DATA_DICTIONARY' AS TABLE_NAME, COUNT(*) AS ROWS FROM DATA_DICTIONARY
UNION ALL
SELECT 'TABLE_RELATIONSHIPS', COUNT(*) FROM TABLE_RELATIONSHIPS
UNION ALL
SELECT 'BUSINESS_CONTEXT', COUNT(*) FROM BUSINESS_CONTEXT
UNION ALL
SELECT 'AGENT_SAMPLE_QUERIES', COUNT(*) FROM AGENT_SAMPLE_QUERIES
UNION ALL
SELECT 'AGENT_INSTRUCTIONS', COUNT(*) FROM AGENT_INSTRUCTIONS
UNION ALL
SELECT 'KNOWLEDGE_BASE', COUNT(*) FROM KNOWLEDGE_BASE;

-- ============================================================================
-- FINAL STATUS
-- ============================================================================

SELECT '✅ DEPLOYMENT COMPLETE - AGENT READY' AS FINAL_STATUS;