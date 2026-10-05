-- ============================================================================
-- MASTER DEPLOYMENT VERIFICATION
-- ============================================================================

USE DATABASE SALES_DATA;
USE SCHEMA PUBLIC;

-- ============================================================================
-- STEP 1: VERIFY ALL OBJECTS CREATED
-- ============================================================================

SELECT '=== DEPLOYMENT VERIFICATION ===' AS STATUS;

SELECT 'TABLES' AS OBJECT_TYPE, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'PUBLIC'
AND TABLE_NAME IN ('DATA_DICTIONARY', 'TABLE_RELATIONSHIPS', 'BUSINESS_CONTEXT', 'AGENT_QUERY_LOG', 'AGENT_SAMPLE_QUERIES', 'AGENT_INSTRUCTIONS', 'KNOWLEDGE_BASE')
ORDER BY TABLE_NAME;

-- ============================================================================
-- STEP 2: VERIFY FUNCTIONS CREATED
-- ============================================================================

SELECT 'FUNCTIONS' AS OBJECT_TYPE, FUNCTION_NAME
FROM INFORMATION_SCHEMA.FUNCTIONS
WHERE FUNCTION_SCHEMA = 'PUBLIC'
AND FUNCTION_NAME IN ('GET_TABLE_INFO', 'GET_TABLE_JOINS', 'GET_BUSINESS_RULES', 'GET_ALL_TABLES')
ORDER BY FUNCTION_NAME;

-- ============================================================================
-- STEP 3: VERIFY VIEWS CREATED
-- ============================================================================

SELECT 'VIEWS' AS OBJECT_TYPE, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'PUBLIC'
AND TABLE_TYPE = 'VIEW'
AND TABLE_NAME = 'KEY_METRICS';

-- ============================================================================
-- STEP 4: DATA SUMMARY
-- ============================================================================

SELECT '=== DATA SUMMARY ===' AS STATUS;

SELECT 
    'DATA_DICTIONARY' AS TABLE_NAME,
    COUNT(*) AS ROW_COUNT
FROM DATA_DICTIONARY

UNION ALL

SELECT 
    'TABLE_RELATIONSHIPS',
    COUNT(*)
FROM TABLE_RELATIONSHIPS

UNION ALL

SELECT 
    'BUSINESS_CONTEXT',
    COUNT(*)
FROM BUSINESS_CONTEXT

UNION ALL

SELECT 
    'AGENT_INSTRUCTIONS',
    COUNT(*)
FROM AGENT_INSTRUCTIONS

UNION ALL

SELECT 
    'KNOWLEDGE_BASE',
    COUNT(*)
FROM KNOWLEDGE_BASE;

