# =============================================================================
# SALES AI - SNOWFLAKE STREAMLIT PRODUCTION APPLICATION
# =============================================================================
#
# Compatible with older Snowflake Streamlit runtimes.
#
# DOES NOT USE:
#   st.chat_input()
#   st.chat_message()
#   st.rerun()
#
# Uses:
#   Snowflake Active Session
#   Cortex Analyst REST API
#   Snowflake SQL
#   Streamlit
#
# =============================================================================


# =============================================================================
# 1. IMPORTS
# =============================================================================

import streamlit as st
import pandas as pd
import json
import re
import time
import uuid

from datetime import date, timedelta

import _snowflake

from snowflake.snowpark.context import get_active_session


# =============================================================================
# 2. PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Sales AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# 3. APPLICATION CONFIGURATION
# =============================================================================

APPLICATION_NAME = "Sales AI"

SEMANTIC_VIEW = (
    "SALES_DATA.PUBLIC.SALES_SEMANTIC_MODEL"
)

SEMANTIC_MODEL_NAME = (
    "SALES_SEMANTIC_MODEL"
)

ANALYST_ENDPOINT = (
    "/api/v2/cortex/analyst/message"
)

MAX_RESULT_ROWS = 10000

QUERY_HISTORY_LIMIT = 100

AUDIT_TABLE = (
    "SALES_DATA.PUBLIC.ANALYST_QUERY_AUDIT_LOG"
)

FEEDBACK_TABLE = (
    "SALES_DATA.PUBLIC.ANALYST_QUERY_FEEDBACK"
)

LEGACY_LOG_TABLE = (
    "SALES_DATA.PUBLIC.ANALYST_QUERY_LOG"
)


# =============================================================================
# 4. CSS
# =============================================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .sub-title {
        color: #666666;
        font-size: 1rem;
        margin-bottom: 1rem;
    }

    .answer-box {
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dddddd;
        background-color: #fafafa;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }

    .filter-box {
        padding: 0.75rem;
        border-radius: 8px;
        border: 1px solid #dddddd;
        background-color: #fafafa;
        margin-bottom: 1rem;
    }

    .metric-box {
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dddddd;
        background-color: #fafafa;
        min-height: 100px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =============================================================================
# 5. SNOWFLAKE SESSION
# =============================================================================

session = get_active_session()


# =============================================================================
# 6. SESSION STATE
# =============================================================================

if "analyst_messages" not in st.session_state:
    st.session_state.analyst_messages = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "last_query_id" not in st.session_state:
    st.session_state.last_query_id = None

if "last_request_id" not in st.session_state:
    st.session_state.last_request_id = None

if "last_question" not in st.session_state:
    st.session_state.last_question = None

if "last_sql" not in st.session_state:
    st.session_state.last_sql = None

if "last_response" not in st.session_state:
    st.session_state.last_response = None

if "last_dataframe" not in st.session_state:
    st.session_state.last_dataframe = None

if "last_status" not in st.session_state:
    st.session_state.last_status = None


# =============================================================================
# 7. CURRENT USER
# =============================================================================

def get_current_user():

    if "current_user" in st.session_state:
        return st.session_state.current_user

    try:

        user_df = session.sql(
            "SELECT CURRENT_USER() AS USER_NAME"
        ).to_pandas()

        if not user_df.empty:

            user_name = str(
                user_df.iloc[0]["USER_NAME"]
            )

        else:

            user_name = "UNKNOWN"

    except Exception:

        user_name = "UNKNOWN"

    st.session_state.current_user = user_name

    return user_name


# =============================================================================
# 8. DATE RANGE
# =============================================================================

def get_date_range(filter_name):

    today = date.today()

    if filter_name == "Today":

        return today, today

    if filter_name == "Yesterday":

        yesterday = (
            today - timedelta(days=1)
        )

        return yesterday, yesterday

    if filter_name == "Last 7 Days":

        return (
            today - timedelta(days=6),
            today
        )

    if filter_name == "Last 30 Days":

        return (
            today - timedelta(days=29),
            today
        )

    if filter_name == "Last 90 Days":

        return (
            today - timedelta(days=89),
            today
        )

    if filter_name == "Month to Date":

        return (
            today.replace(day=1),
            today
        )

    if filter_name == "Quarter to Date":

        quarter_start_month = (
            ((today.month - 1) // 3) * 3 + 1
        )

        return (
            today.replace(
                month=quarter_start_month,
                day=1
            ),
            today
        )

    if filter_name == "Year to Date":

        return (
            today.replace(
                month=1,
                day=1
            ),
            today
        )

    if filter_name == "Last Month":

        first_current_month = (
            today.replace(day=1)
        )

        last_previous_month = (
            first_current_month
            - timedelta(days=1)
        )

        first_previous_month = (
            last_previous_month.replace(day=1)
        )

        return (
            first_previous_month,
            last_previous_month
        )

    if filter_name == "Last Quarter":

        current_quarter = (
            (today.month - 1) // 3
        )

        if current_quarter == 0:

            previous_year = (
                today.year - 1
            )

            previous_quarter = 3

        else:

            previous_year = today.year

            previous_quarter = (
                current_quarter - 1
            )

        start_month = (
            previous_quarter * 3 + 1
        )

        start_date = date(
            previous_year,
            start_month,
            1
        )

        if start_month == 10:

            end_date = date(
                previous_year,
                12,
                31
            )

        else:

            next_quarter_start = date(
                previous_year,
                start_month + 3,
                1
            )

            end_date = (
                next_quarter_start
                - timedelta(days=1)
            )

        return start_date, end_date

    if filter_name == "Last Year":

        return (
            date(
                today.year - 1,
                1,
                1
            ),
            date(
                today.year - 1,
                12,
                31
            )
        )

    return None, None


# =============================================================================
# 9. BUSINESS CONTEXT
# =============================================================================

def build_business_context():

    role = st.session_state.get(
        "business_role",
        "Sales Executive"
    )

    answer_style = st.session_state.get(
        "answer_style",
        "Executive Summary"
    )

    date_filter = st.session_state.get(
        "date_filter",
        "Last 30 Days"
    )

    comparison = st.session_state.get(
        "comparison_period",
        "No Comparison"
    )

    context = []

    context.append(
        "Business role: "
        + role
    )

    context.append(
        "Preferred answer style: "
        + answer_style
    )

    if date_filter == "Custom":

        start_date = st.session_state.get(
            "custom_start_date"
        )

        end_date = st.session_state.get(
            "custom_end_date"
        )

        if start_date and end_date:

            context.append(
                "Date filter: Custom, from "
                + start_date.isoformat()
                + " through "
                + end_date.isoformat()
            )

    else:

        start_date, end_date = (
            get_date_range(date_filter)
        )

        if start_date and end_date:

            context.append(
                "Date filter: "
                + date_filter
                + ", from "
                + start_date.isoformat()
                + " through "
                + end_date.isoformat()
            )

    if comparison != "No Comparison":

        context.append(
            "Comparison period: "
            + comparison
        )

    filters = [
        (
            "Region",
            st.session_state.get(
                "filter_region",
                ""
            )
        ),
        (
            "Territory",
            st.session_state.get(
                "filter_territory",
                ""
            )
        ),
        (
            "Sales Rep",
            st.session_state.get(
                "filter_sales_rep",
                ""
            )
        ),
        (
            "Customer",
            st.session_state.get(
                "filter_customer",
                ""
            )
        ),
        (
            "Industry",
            st.session_state.get(
                "filter_industry",
                ""
            )
        ),
        (
            "Product",
            st.session_state.get(
                "filter_product",
                ""
            )
        ),
        (
            "Product Category",
            st.session_state.get(
                "filter_product_category",
                ""
            )
        ),
        (
            "Channel",
            st.session_state.get(
                "filter_channel",
                ""
            )
        )
    ]

    for label, value in filters:

        value = str(value).strip()

        if value and value.lower() not in (
            "all",
            "any"
        ):

            context.append(
                label
                + " filter: "
                + value
            )

    context.append(
        "Apply these application filters unless "
        "the user explicitly requests a different "
        "filter or date period."
    )

    return "\n".join(context)


# =============================================================================
# 10. ANALYST QUESTION
# =============================================================================

def build_analyst_question(question):

    context = build_business_context()

    return f"""
User's sales question:
{question}

Application business context:
{context}

Instructions:
- Use the configured semantic model.
- Answer the user's actual question.
- Respect the application filters unless explicitly overridden.
- Do not invent metrics, dimensions, customers, products or values.
- Provide a concise business explanation.
- If the user requests a comparison, clearly explain both periods.
""".strip()


# =============================================================================
# 11. SQL COMMENT REMOVAL
# =============================================================================

def remove_sql_comments(sql_text):

    sql_text = re.sub(
        r"/\*.*?\*/",
        " ",
        sql_text,
        flags=re.DOTALL
    )

    sql_text = re.sub(
        r"--[^\n\r]*",
        " ",
        sql_text
    )

    return sql_text


# =============================================================================
# 12. SQL STRING REMOVAL
# =============================================================================

def remove_sql_string_literals(sql_text):

    return re.sub(
        r"'(?:''|[^'])*'",
        " ",
        sql_text
    )


# =============================================================================
# 13. SQL VALIDATION
# =============================================================================

def validate_generated_sql(sql_text):

    if not sql_text:

        return False, "No SQL was generated."

    sql_text = str(
        sql_text
    ).strip()

    sql_text = sql_text.rstrip(";").strip()

    if len(sql_text) > 100000:

        return (
            False,
            "Generated SQL exceeds the allowed size."
        )

    validation_sql = remove_sql_comments(
        sql_text
    )

    validation_sql = remove_sql_string_literals(
        validation_sql
    )

    if ";" in validation_sql:

        return (
            False,
            "Multiple SQL statements are not allowed."
        )

    normalized = validation_sql.strip().upper()

    if not (
        normalized.startswith("SELECT ")
        or normalized.startswith("SELECT\n")
        or normalized == "SELECT"
        or normalized.startswith("WITH ")
        or normalized.startswith("WITH\n")
    ):

        return (
            False,
            "Only read-only SELECT/WITH queries are allowed."
        )

    blocked_keywords = [
        "INSERT ",
        "UPDATE ",
        "DELETE ",
        "MERGE ",
        "TRUNCATE ",
        "DROP ",
        "ALTER ",
        "CREATE ",
        "REPLACE ",
        "GRANT ",
        "REVOKE ",
        "COPY ",
        "PUT ",
        "GET ",
        "REMOVE ",
        "CALL ",
        "EXECUTE ",
        "EXEC ",
        "BEGIN ",
        "COMMIT ",
        "ROLLBACK ",
        "USE "
    ]

    upper_sql = validation_sql.upper()

    for keyword in blocked_keywords:

        if keyword in upper_sql:

            return (
                False,
                "Generated SQL contains a non-read-only operation: "
                + keyword.strip()
            )

    return True, ""


# =============================================================================
# 14. CORTEX ANALYST REQUEST
# =============================================================================

def ask_cortex_analyst(question):

    analyst_question = (
        build_analyst_question(question)
    )

    messages = list(
        st.session_state.analyst_messages
    )

    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": analyst_question
                }
            ]
        }
    )

    request_body = {
        "messages": messages,
        "semantic_view": SEMANTIC_VIEW
    }

    start_time = time.perf_counter()

    try:

        response = (
            _snowflake.send_snow_api_request(
                method="POST",
                endpoint=ANALYST_ENDPOINT,
                headers={
                    "Content-Type": "application/json"
                },
                body=request_body
            )
        )

        elapsed = (
            time.perf_counter()
            - start_time
        )

        return response, elapsed

    except Exception as exc:

        elapsed = (
            time.perf_counter()
            - start_time
        )

        return {
            "status": 500,
            "content": {
                "error": str(exc)
            }
        }, elapsed


# =============================================================================
# 15. PARSE CORTEX ANALYST RESPONSE
# =============================================================================

def parse_analyst_response(api_response):

    result = {
        "success": False,
        "text": "",
        "sql": None,
        "suggestions": [],
        "assistant_message": None,
        "request_id": None,
        "error": None
    }

    if not isinstance(
        api_response,
        dict
    ):

        result["error"] = (
            "Invalid Cortex Analyst response."
        )

        return result

    status = api_response.get(
        "status"
    )

    result["request_id"] = (
        api_response.get(
            "request_id"
        )
        or api_response.get(
            "requestId"
        )
    )

    headers = api_response.get(
        "headers"
    )

    if isinstance(
        headers,
        dict
    ):

        result["request_id"] = (
            result["request_id"]
            or headers.get(
                "X-Snowflake-Request-ID"
            )
            or headers.get(
                "x-snowflake-request-id"
            )
            or headers.get(
                "X-Request-ID"
            )
            or headers.get(
                "x-request-id"
            )
        )

    content = api_response.get(
        "content"
    )

    if status != 200:

        if isinstance(
            content,
            dict
        ):

            error_value = (
                content.get(
                    "message"
                )
                or content.get(
                    "error"
                )
                or content.get(
                    "detail"
                )
            )

            if isinstance(
                error_value,
                dict
            ):

                error_value = json.dumps(
                    error_value
                )

        else:

            error_value = str(
                content
            )

        result["error"] = (
            "Cortex Analyst request failed "
            f"(HTTP {status}): "
            f"{error_value}"
        )

        return result

    if isinstance(
        content,
        str
    ):

        try:

            content = json.loads(
                content
            )

        except Exception:

            result["error"] = (
                "Cortex Analyst returned invalid JSON."
            )

            return result

    if not isinstance(
        content,
        dict
    ):

        result["error"] = (
            "Unexpected Cortex Analyst response."
        )

        return result

    result["request_id"] = (
        result["request_id"]
        or content.get(
            "request_id"
        )
        or content.get(
            "requestId"
        )
    )

    message = content.get(
        "message"
    )

    if not isinstance(
        message,
        dict
    ):

        result["error"] = (
            "Cortex Analyst response did not "
            "contain a message."
        )

        return result

    message_content = message.get(
        "content",
        []
    )

    if not isinstance(
        message_content,
        list
    ):

        result["error"] = (
            "Cortex Analyst message content is invalid."
        )

        return result

    result["assistant_message"] = {
        "role": "assistant",
        "content": message_content
    }

    text_parts = []

    suggestions = []

    for item in message_content:

        if not isinstance(
            item,
            dict
        ):

            continue

        item_type = item.get(
            "type"
        )

        if item_type == "text":

            text_value = item.get(
                "text",
                ""
            )

            if text_value:

                text_parts.append(
                    str(text_value)
                )

        elif item_type == "sql":

            sql_value = (
                item.get(
                    "statement"
                )
                or item.get(
                    "sql"
                )
                or item.get(
                    "query"
                )
            )

            if sql_value:

                result["sql"] = str(
                    sql_value
                )

        elif item_type == "suggestions":

            values = (
                item.get(
                    "suggestions"
                )
                or item.get(
                    "items"
                )
                or []
            )

            if isinstance(
                values,
                list
            ):

                for value in values:

                    if isinstance(
                        value,
                        str
                    ):

                        suggestions.append(
                            value
                        )

                    elif isinstance(
                        value,
                        dict
                    ):

                        suggestion_text = (
                            value.get(
                                "text"
                            )
                            or value.get(
                                "question"
                            )
                            or value.get(
                                "suggestion"
                            )
                        )

                        if suggestion_text:

                            suggestions.append(
                                str(
                                    suggestion_text
                                )
                            )

    result["text"] = (
        "\n\n".join(
            text_parts
        ).strip()
    )

    result["suggestions"] = (
        suggestions[:5]
    )

    result["success"] = True

    return result


# =============================================================================
# 16. EXECUTE GENERATED SQL
# =============================================================================

def execute_generated_sql(generated_sql):

    generated_sql = str(
        generated_sql
    ).strip()

    generated_sql = (
        generated_sql.rstrip(";")
        .strip()
    )

    valid, validation_error = (
        validate_generated_sql(
            generated_sql
        )
    )

    if not valid:

        return {
            "success": False,
            "dataframe": None,
            "seconds": 0,
            "rows": 0,
            "error": validation_error
        }

    wrapped_sql = f"""
SELECT *
FROM (
    {generated_sql}
) AS ANALYST_RESULT
LIMIT {MAX_RESULT_ROWS}
""".strip()

    start_time = time.perf_counter()

    try:

        dataframe = (
            session.sql(
                wrapped_sql
            ).to_pandas()
        )

        elapsed = (
            time.perf_counter()
            - start_time
        )

        return {
            "success": True,
            "dataframe": dataframe,
            "seconds": elapsed,
            "rows": len(dataframe),
            "error": None
        }

    except Exception as exc:

        elapsed = (
            time.perf_counter()
            - start_time
        )

        return {
            "success": False,
            "dataframe": None,
            "seconds": elapsed,
            "rows": 0,
            "error": str(exc)
        }


# =============================================================================
# 17. AUDIT LOGGING
# =============================================================================

def log_query(
    query_id,
    user_question,
    analyst_question,
    response_text,
    generated_sql,
    request_id,
    execution_status,
    analyst_seconds,
    execution_seconds,
    rows_returned,
    error_message
):

    current_user = get_current_user()

    try:

        sql = f"""
INSERT INTO {AUDIT_TABLE}
(
    QUERY_ID,
    QUERY_TIMESTAMP,
    USER_NAME,
    REQUEST_ID,
    USER_QUESTION,
    ANALYST_QUESTION,
    RESPONSE,
    GENERATED_SQL,
    EXECUTION_STATUS,
    ANALYST_SECONDS,
    EXECUTION_SECONDS,
    ROWS_RETURNED,
    ERROR_MESSAGE,
    SEMANTIC_MODEL_NAME,
    APPLICATION_NAME
)
VALUES
(
    ?,
    CURRENT_TIMESTAMP(),
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?
)
"""

        session.sql(
            sql,
            params=[
                query_id,
                current_user,
                request_id,
                user_question,
                analyst_question,
                response_text,
                generated_sql,
                execution_status,
                analyst_seconds,
                execution_seconds,
                rows_returned,
                error_message,
                SEMANTIC_MODEL_NAME,
                APPLICATION_NAME
            ]
        ).collect()

        return True

    except Exception:

        # Fallback to existing table.
        try:

            legacy_sql = f"""
INSERT INTO {LEGACY_LOG_TABLE}
(
    QUERY_TIMESTAMP,
    USER_NAME,
    USER_QUESTION,
    RESPONSE,
    SEMANTIC_MODEL_NAME
)
VALUES
(
    CURRENT_TIMESTAMP(),
    ?,
    ?,
    ?,
    ?
)
"""

            legacy_response = (
                response_text or ""
            )

            if error_message:

                legacy_response += (
                    "\n\nExecution Error: "
                    + str(error_message)
                )

            session.sql(
                legacy_sql,
                params=[
                    current_user,
                    user_question,
                    legacy_response,
                    SEMANTIC_MODEL_NAME
                ]
            ).collect()

            return True

        except Exception:

            return False


# =============================================================================
# 18. FEEDBACK
# =============================================================================

def log_feedback(
    query_id,
    feedback
):

    try:

        sql = f"""
INSERT INTO {FEEDBACK_TABLE}
(
    QUERY_ID,
    FEEDBACK_TIMESTAMP,
    USER_NAME,
    FEEDBACK
)
VALUES
(
    ?,
    CURRENT_TIMESTAMP(),
    ?,
    ?
)
"""

        session.sql(
            sql,
            params=[
                query_id,
                get_current_user(),
                feedback
            ]
        ).collect()

        return True

    except Exception:

        return False


# =============================================================================
# 19. FILTER SUMMARY
# =============================================================================

def display_filter_summary():

    date_filter = st.session_state.get(
        "date_filter",
        "Last 30 Days"
    )

    summary = [
        "Date: " + date_filter
    ]

    filter_list = [
        (
            "Region",
            "filter_region"
        ),
        (
            "Territory",
            "filter_territory"
        ),
        (
            "Sales Rep",
            "filter_sales_rep"
        ),
        (
            "Customer",
            "filter_customer"
        ),
        (
            "Industry",
            "filter_industry"
        ),
        (
            "Product",
            "filter_product"
        ),
        (
            "Product Category",
            "filter_product_category"
        ),
        (
            "Channel",
            "filter_channel"
        )
    ]

    for label, key in filter_list:

        value = st.session_state.get(
            key,
            ""
        )

        if value:

            summary.append(
                label + ": " + value
            )

    st.markdown(
        '<div class="filter-box">'
        "<strong>Active Business Context</strong><br>"
        + " | ".join(summary)
        + "</div>",
        unsafe_allow_html=True
    )


# =============================================================================
# 20. PROCESS QUESTION
# =============================================================================

def process_question(
    question,
    display_result=True
):

    question = str(
        question
    ).strip()

    if not question:

        st.warning(
            "Please enter a question."
        )

        return

    query_id = str(
        uuid.uuid4()
    )

    analyst_question = (
        build_analyst_question(
            question
        )
    )

    st.session_state.last_query_id = (
        query_id
    )

    st.session_state.last_question = (
        question
    )

    st.session_state.last_sql = None

    st.session_state.last_response = None

    st.session_state.last_dataframe = None

    # -------------------------------------------------------------------------
    # USER QUESTION
    # -------------------------------------------------------------------------

    st.markdown(
        "### You"
    )

    st.markdown(
        question
    )

    # -------------------------------------------------------------------------
    # CORTEX ANALYST
    # -------------------------------------------------------------------------

    with st.spinner(
        "Sales AI is analyzing your question..."
    ):

        api_response, analyst_seconds = (
            ask_cortex_analyst(
                question
            )
        )

    parsed = (
        parse_analyst_response(
            api_response
        )
    )

    request_id = parsed.get(
        "request_id"
    )

    st.session_state.last_request_id = (
        request_id
    )

    # -------------------------------------------------------------------------
    # ANALYST ERROR
    # -------------------------------------------------------------------------

    if not parsed["success"]:

        error_message = parsed.get(
            "error",
            "Cortex Analyst failed."
        )

        st.session_state.last_status = (
            "ANALYST_ERROR"
        )

        st.error(
            "Sales AI could not process your question."
        )

        with st.expander(
            "Technical Details"
        ):

            st.code(
                error_message
            )

        log_query(
            query_id=query_id,
            user_question=question,
            analyst_question=analyst_question,
            response_text="",
            generated_sql=None,
            request_id=request_id,
            execution_status="ANALYST_ERROR",
            analyst_seconds=analyst_seconds,
            execution_seconds=0,
            rows_returned=0,
            error_message=error_message
        )

        return

    # -------------------------------------------------------------------------
    # RESPONSE
    # -------------------------------------------------------------------------

    response_text = parsed.get(
        "text",
        ""
    )

    generated_sql = parsed.get(
        "sql"
    )

    suggestions = parsed.get(
        "suggestions",
        []
    )

    assistant_message = parsed.get(
        "assistant_message"
    )

    # -------------------------------------------------------------------------
    # PRESERVE ACTUAL ANALYST CONVERSATION
    # -------------------------------------------------------------------------

    st.session_state.analyst_messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": analyst_question
                }
            ]
        }
    )

    if assistant_message:

        st.session_state.analyst_messages.append(
            assistant_message
        )

    st.session_state.last_response = (
        response_text
    )

    st.session_state.last_sql = (
        generated_sql
    )

    # -------------------------------------------------------------------------
    # ANSWER
    # -------------------------------------------------------------------------

    st.markdown(
        "### Sales AI"
    )

    if response_text:

        st.markdown(
            '<div class="answer-box">'
            + response_text
            + "</div>",
            unsafe_allow_html=True
        )

    # -------------------------------------------------------------------------
    # EXECUTE SQL
    # -------------------------------------------------------------------------

    execution_result = {
        "success": False,
        "dataframe": None,
        "seconds": 0,
        "rows": 0,
        "error": None
    }

    execution_status = (
        "ANSWER_ONLY"
    )

    if generated_sql:

        with st.spinner(
            "Running analysis in Snowflake..."
        ):

            execution_result = (
                execute_generated_sql(
                    generated_sql
                )
            )

        if execution_result["success"]:

            execution_status = (
                "SUCCESS"
            )

        else:

            execution_status = (
                "SQL_ERROR"
            )

    st.session_state.last_status = (
        execution_status
    )

    # -------------------------------------------------------------------------
    # RESULTS
    # -------------------------------------------------------------------------

    result_dataframe = None

    if execution_result["success"]:

        result_dataframe = (
            execution_result["dataframe"]
        )

        st.session_state.last_dataframe = (
            result_dataframe
        )

        if result_dataframe is not None:

            st.markdown(
                "### Results"
            )

            st.dataframe(
                result_dataframe,
                use_container_width=True,
                height=420
            )

            csv_data = (
                result_dataframe
                .to_csv(
                    index=False
                )
                .encode("utf-8")
            )

            st.download_button(
                "Download Results as CSV",
                data=csv_data,
                file_name=(
                    "sales_ai_"
                    + query_id[:8]
                    + ".csv"
                ),
                mime="text/csv",
                key=(
                    "download_"
                    + query_id
                )
            )

    elif generated_sql:

        st.error(
            "The generated SQL could not be executed "
            "in Snowflake."
        )

        with st.expander(
            "Technical Details"
        ):

            st.code(
                execution_result["error"]
            )

    # -------------------------------------------------------------------------
    # TECHNICAL DETAILS
    # -------------------------------------------------------------------------

    with st.expander(
        "Technical Details"
    ):

        col1, col2, col3, col4 = (
            st.columns(4)
        )

        with col1:

            st.metric(
                "Analyst Time",
                f"{analyst_seconds:.2f}s"
            )

        with col2:

            st.metric(
                "SQL Time",
                f"{execution_result['seconds']:.2f}s"
            )

        with col3:

            st.metric(
                "Rows",
                f"{execution_result['rows']:,}"
            )

        with col4:

            st.metric(
                "Status",
                execution_status
            )

        if request_id:

            st.caption(
                "Request ID: "
                + str(request_id)
            )

        if generated_sql:

            st.markdown(
                "#### Generated SQL"
            )

            st.code(
                generated_sql,
                language="sql"
            )

    # -------------------------------------------------------------------------
    # LOG
    # -------------------------------------------------------------------------

    log_query(
        query_id=query_id,
        user_question=question,
        analyst_question=analyst_question,
        response_text=response_text,
        generated_sql=generated_sql,
        request_id=request_id,
        execution_status=execution_status,
        analyst_seconds=analyst_seconds,
        execution_seconds=(
            execution_result["seconds"]
        ),
        rows_returned=(
            execution_result["rows"]
        ),
        error_message=(
            execution_result["error"]
        )
    )

    # -------------------------------------------------------------------------
    # FEEDBACK
    # -------------------------------------------------------------------------

    st.markdown(
        "### Feedback"
    )

    feedback_col1, feedback_col2 = (
        st.columns(2)
    )

    with feedback_col1:

        if st.button(
            "👍 Helpful",
            key=(
                "helpful_"
                + query_id
            )
        ):

            if log_feedback(
                query_id,
                "HELPFUL"
            ):

                st.success(
                    "Thanks for your feedback."
                )

    with feedback_col2:

        if st.button(
            "👎 Not Helpful",
            key=(
                "not_helpful_"
                + query_id
            )
        ):

            if log_feedback(
                query_id,
                "NOT_HELPFUL"
            ):

                st.success(
                    "Thanks for your feedback."
                )

    # -------------------------------------------------------------------------
    # SUGGESTED FOLLOW-UPS
    #
    # IMPORTANT:
    #
    # No st.rerun().
    #
    # A button stores the question in session state.
    # The user can then click "Ask Sales AI".
    # -------------------------------------------------------------------------

    if suggestions:

        st.markdown(
            "### Suggested Follow-ups"
        )

        for index, suggestion in enumerate(
            suggestions
        ):

            if st.button(
                suggestion,
                key=(
                    "suggestion_"
                    + query_id
                    + "_"
                    + str(index)
                ),
                use_container_width=True
            ):

                st.session_state[
                    "question_input"
                ] = suggestion

                st.info(
                    "The suggested question has been "
                    "placed in the question box. "
                    "Click **Ask Sales AI** to run it."
                )


# =============================================================================
# 21. APPLICATION HEADER
# =============================================================================

st.markdown(
    '<div class="main-title">'
    "📊 Sales AI"
    "</div>",
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    "Natural-language sales analytics powered by "
    "Snowflake and Cortex Analyst"
    "</div>",
    unsafe_allow_html=True
)


# =============================================================================
# 22. SIDEBAR
# =============================================================================

with st.sidebar:

    st.markdown(
        "## Business Controls"
    )

    st.caption(
        "User: "
        + get_current_user()
    )

    st.markdown(
        "---"
    )

    # -------------------------------------------------------------------------
    # ROLE
    # -------------------------------------------------------------------------

    st.selectbox(
        "Business Role",
        [
            "Sales Executive",
            "Sales Manager",
            "Sales Representative",
            "Sales Leadership",
            "Sales Analyst",
            "Data / AI Developer"
        ],
        index=0,
        key="business_role"
    )

    # -------------------------------------------------------------------------
    # ANSWER STYLE
    # -------------------------------------------------------------------------

    st.selectbox(
        "Answer Style",
        [
            "Executive Summary",
            "Detailed Analysis",
            "Data Focused",
            "Trend Analysis",
            "Action Oriented"
        ],
        index=0,
        key="answer_style"
    )

    st.markdown(
        "---"
    )

    # -------------------------------------------------------------------------
    # DATE
    # -------------------------------------------------------------------------

    st.selectbox(
        "Date Range",
        [
            "Today",
            "Yesterday",
            "Last 7 Days",
            "Last 30 Days",
            "Last 90 Days",
            "Month to Date",
            "Quarter to Date",
            "Year to Date",
            "Last Month",
            "Last Quarter",
            "Last Year",
            "Custom"
        ],
        index=3,
        key="date_filter"
    )

    if st.session_state.date_filter == "Custom":

        st.date_input(
            "Start Date",
            value=(
                date.today()
                - timedelta(days=29)
            ),
            key="custom_start_date"
        )

        st.date_input(
            "End Date",
            value=date.today(),
            key="custom_end_date"
        )

        if (
            st.session_state.custom_start_date
            > st.session_state.custom_end_date
        ):

            st.error(
                "Start Date cannot be after End Date."
            )

    # -------------------------------------------------------------------------
    # COMPARISON
    # -------------------------------------------------------------------------

    st.selectbox(
        "Comparison",
        [
            "No Comparison",
            "Previous Period",
            "Previous Month",
            "Previous Quarter",
            "Previous Year"
        ],
        index=0,
        key="comparison_period"
    )

    st.markdown(
        "---"
    )

    # -------------------------------------------------------------------------
    # SALES FILTERS
    # -------------------------------------------------------------------------

    st.markdown(
        "### Sales Filters"
    )

    st.text_input(
        "Region",
        placeholder="All regions",
        key="filter_region"
    )

    st.text_input(
        "Territory",
        placeholder="All territories",
        key="filter_territory"
    )

    st.text_input(
        "Sales Rep",
        placeholder="All sales reps",
        key="filter_sales_rep"
    )

    st.text_input(
        "Customer",
        placeholder="All customers",
        key="filter_customer"
    )

    st.text_input(
        "Industry",
        placeholder="All industries",
        key="filter_industry"
    )

    st.text_input(
        "Product",
        placeholder="All products",
        key="filter_product"
    )

    st.text_input(
        "Product Category",
        placeholder="All product categories",
        key="filter_product_category"
    )

    st.text_input(
        "Channel",
        placeholder="All channels",
        key="filter_channel"
    )

    st.markdown(
        "---"
    )

    # -------------------------------------------------------------------------
    # NEW CONVERSATION
    # -------------------------------------------------------------------------

    if st.button(
        "Start New Conversation",
        use_container_width=True
    ):

        st.session_state.analyst_messages = []

        st.session_state.conversation_history = []

        st.session_state.last_question = None

        st.session_state.last_response = None

        st.session_state.last_sql = None

        st.session_state.last_dataframe = None

        st.session_state.last_query_id = None

        st.session_state.last_request_id = None

        st.session_state.last_status = None

        st.success(
            "Conversation cleared."
        )

    # -------------------------------------------------------------------------
    # RESET FILTERS
    # -------------------------------------------------------------------------

    if st.button(
        "Reset Filters",
        use_container_width=True
    ):

        st.session_state.business_role = (
            "Sales Executive"
        )

        st.session_state.answer_style = (
            "Executive Summary"
        )

        st.session_state.date_filter = (
            "Last 30 Days"
        )

        st.session_state.comparison_period = (
            "No Comparison"
        )

        st.session_state.filter_region = ""

        st.session_state.filter_territory = ""

        st.session_state.filter_sales_rep = ""

        st.session_state.filter_customer = ""

        st.session_state.filter_industry = ""

        st.session_state.filter_product = ""

        st.session_state.filter_product_category = ""

        st.session_state.filter_channel = ""

        st.success(
            "Filters reset."
        )


# =============================================================================
# 23. TABS
# =============================================================================

tab_overview, tab_ai, tab_history, tab_samples, tab_about = (
    st.tabs(
        [
            "Executive Overview",
            "Sales AI",
            "Query History",
            "Sample Questions",
            "About"
        ]
    )
)


# =============================================================================
# 24. EXECUTIVE OVERVIEW
# =============================================================================

with tab_overview:

    st.markdown(
        "## Executive Overview"
    )

    display_filter_summary()

    st.info(
        "Ask Sales AI questions using natural language. "
        "The application uses the governed sales semantic "
        "model to generate the analysis."
    )

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.markdown(
            """
            <div class="metric-box">
            <strong>Revenue</strong><br>
            Analyze revenue, growth and trends.
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            """
            <div class="metric-box">
            <strong>Sales Team</strong><br>
            Analyze reps and territories.
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:

        st.markdown(
            """
            <div class="metric-box">
            <strong>Customers</strong><br>
            Analyze customer contribution and trends.
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:

        st.markdown(
            """
            <div class="metric-box">
            <strong>Products</strong><br>
            Analyze products and categories.
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        "### Recommended Analyses"
    )

    overview_questions = [
        "What was total revenue during the selected period?",
        "Which regions are performing best?",
        "Which sales reps have the highest revenue?",
        "Which customers contributed the most revenue?",
        "Which products are growing fastest?",
        "How does this period compare with the previous period?",
        "What are the biggest sales performance risks?",
        "Where should the sales team focus next?"
    ]

    for question in overview_questions:

        st.markdown(
            "- " + question
        )

    st.markdown(
        "### Recommended Workflow"
    )

    st.markdown(
        """
        **1. Select filters**

        Choose the relevant date range, region, territory,
        sales rep, customer, product or channel.

        **2. Ask a business question**

        Open the **Sales AI** tab and enter a natural-language question.

        **3. Review the answer**

        Cortex Analyst interprets the question using the governed
        semantic model.

        **4. Review the data**

        The generated SQL is executed in Snowflake and the results
        are displayed.

        **5. Continue analysis**

        Use follow-up questions to investigate the result further.
        """
    )


# =============================================================================
# 25. SALES AI TAB
# =============================================================================

with tab_ai:

    st.markdown(
        "## Sales AI"
    )

    display_filter_summary()

    # -------------------------------------------------------------------------
    # QUICK QUESTIONS
    # -------------------------------------------------------------------------

    st.markdown(
        "### Quick Questions"
    )

    quick_questions = [
        "What was revenue during the selected period?",
        "Show the top 10 sales reps by revenue.",
        "Show the top 10 customers by revenue.",
        "Which regions are performing best?",
        "What are the biggest sales trends?"
    ]

    quick_columns = st.columns(
        len(quick_questions)
    )

    for index, quick_question in enumerate(
        quick_questions
    ):

        with quick_columns[index]:

            if st.button(
                quick_question,
                key=(
                    "quick_"
                    + str(index)
                ),
                use_container_width=True
            ):

                st.session_state.question_input = (
                    quick_question
                )

                st.info(
                    "Question selected. "
                    "Click **Ask Sales AI** below."
                )

    st.markdown(
        "---"
    )

    # -------------------------------------------------------------------------
    # QUESTION INPUT
    # -------------------------------------------------------------------------

    st.markdown(
        "### Ask a Business Question"
    )

    st.text_area(
        "Sales question",
        placeholder=(
            "Examples:\n"
            "What was revenue last month by region?\n"
            "Which sales reps are below target?\n"
            "Show top 10 customers by revenue.\n"
            "Compare this quarter with last quarter.\n"
            "Which products are declining?"
        ),
        height=120,
        key="question_input"
    )

    input_col1, input_col2 = (
        st.columns(
            [1, 5]
        )
    )

    with input_col1:

        ask_clicked = st.button(
            "Ask Sales AI",
            type="primary",
            use_container_width=True
        )

    with input_col2:

        clear_clicked = st.button(
            "Clear",
            use_container_width=True
        )

    if clear_clicked:

        st.session_state.question_input = ""

        st.info(
            "Question cleared."
        )

    if ask_clicked:

        current_question = (
            st.session_state.get(
                "question_input",
                ""
            )
        )

        if current_question.strip():

            process_question(
                current_question.strip()
            )

        else:

            st.warning(
                "Please enter a sales question."
            )

    # -------------------------------------------------------------------------
    # LAST QUESTION / ANSWER
    #
    # Because this application intentionally does not use st.rerun(),
    # the current result is displayed during the button click execution.
    # -------------------------------------------------------------------------

    if (
        st.session_state.last_question
        and not ask_clicked
    ):

        st.markdown(
            "---"
        )

        st.markdown(
            "### Last Question"
        )

        st.markdown(
            st.session_state.last_question
        )

        if st.session_state.last_response:

            st.markdown(
                "### Last Answer"
            )

            st.markdown(
                '<div class="answer-box">'
                + st.session_state.last_response
                + "</div>",
                unsafe_allow_html=True
            )

        if (
            st.session_state.last_dataframe
            is not None
        ):

            st.markdown(
                "### Last Results"
            )

            st.dataframe(
                st.session_state.last_dataframe,
                use_container_width=True,
                height=400
            )

        if st.session_state.last_sql:

            with st.expander(
                "Last Generated SQL"
            ):

                st.code(
                    st.session_state.last_sql,
                    language="sql"
                )


# =============================================================================
# 26. QUERY HISTORY
# =============================================================================

with tab_history:

    st.markdown(
        "## Query History"
    )

    st.caption(
        "Recent Sales AI questions executed through Snowflake."
    )

    history_search = st.text_input(
        "Search History",
        placeholder=(
            "Search question, user or response..."
        ),
        key="history_search"
    )

    history_df = None

    # -------------------------------------------------------------------------
    # Try production audit table first.
    # -------------------------------------------------------------------------

    try:

        history_sql = f"""
SELECT
    QUERY_TIMESTAMP,
    USER_NAME,
    USER_QUESTION,
    RESPONSE,
    SEMANTIC_MODEL_NAME,
    EXECUTION_STATUS,
    ANALYST_SECONDS,
    EXECUTION_SECONDS,
    ROWS_RETURNED
FROM {AUDIT_TABLE}
ORDER BY QUERY_TIMESTAMP DESC
LIMIT {QUERY_HISTORY_LIMIT}
"""

        history_df = (
            session.sql(
                history_sql
            ).to_pandas()
        )

    except Exception:

        # ---------------------------------------------------------------------
        # Fall back to original table.
        # ---------------------------------------------------------------------

        try:

            history_sql = f"""
SELECT
    QUERY_TIMESTAMP,
    USER_NAME,
    USER_QUESTION,
    RESPONSE,
    SEMANTIC_MODEL_NAME
FROM {LEGACY_LOG_TABLE}
ORDER BY QUERY_TIMESTAMP DESC
LIMIT {QUERY_HISTORY_LIMIT}
"""

            history_df = (
                session.sql(
                    history_sql
                ).to_pandas()
            )

        except Exception as exc:

            st.error(
                "Unable to load query history."
            )

            with st.expander(
                "Technical Details"
            ):

                st.code(
                    str(exc)
                )

    # -------------------------------------------------------------------------
    # FILTER HISTORY
    # -------------------------------------------------------------------------

    if history_df is not None:

        if history_search.strip():

            search_value = (
                history_search
                .strip()
                .lower()
            )

            search_mask = (
                history_df
                .astype(str)
                .apply(
                    lambda column:
                    column.str.lower()
                    .str.contains(
                        search_value,
                        na=False
                    )
                )
                .any(
                    axis=1
                )
            )

            history_df = (
                history_df[
                    search_mask
                ]
            )

        if history_df.empty:

            st.info(
                "No matching query history found."
            )

        else:

            st.dataframe(
                history_df,
                use_container_width=True,
                height=500
            )

            history_csv = (
                history_df
                .to_csv(
                    index=False
                )
                .encode("utf-8")
            )

            st.download_button(
                "Download History CSV",
                data=history_csv,
                file_name=(
                    "sales_ai_query_history.csv"
                ),
                mime="text/csv"
            )


# =============================================================================
# 27. SAMPLE QUESTIONS
# =============================================================================

with tab_samples:

    st.markdown(
        "## Sample Questions"
    )

    sample_groups = {

        "Revenue & Performance": [

            "What was total revenue last month?",

            "Show revenue by region for the last 30 days.",

            "What is the revenue trend this quarter?",

            "Which regions grew the most compared with "
            "the previous period?"
        ],

        "Sales Team": [

            "Who are the top 10 sales reps by revenue?",

            "Which sales reps are below target?",

            "Show sales rep performance by territory.",

            "Which territories have declining performance?"
        ],

        "Customers": [

            "Who are our top 10 customers by revenue?",

            "Which customers have declining revenue?",

            "Which customers generated the most growth?",

            "Show customer revenue by region."
        ],

        "Products": [

            "Which products generate the most revenue?",

            "Which products are declining?",

            "Show revenue by product category.",

            "Which products are growing fastest?"
        ],

        "Regions": [

            "Compare revenue across regions.",

            "Which region has the strongest growth?",

            "Show territory performance by region.",

            "Which regions need management attention?"
        ],

        "Management": [

            "What are the biggest sales risks?",

            "Where should the sales team focus next?",

            "What are the top drivers of revenue growth?",

            "Give me an executive summary of sales performance."
        ]
    }

    for group_name, questions in (
        sample_groups.items()
    ):

        st.markdown(
            "### " + group_name
        )

        for question in questions:

            st.markdown(
                "- " + question
            )


# =============================================================================
# 28. ABOUT
# =============================================================================

with tab_about:

    st.markdown(
        "## About Sales AI"
    )

    st.markdown(
        """
        Sales AI provides a business-friendly interface for
        asking natural-language questions against a governed
        Snowflake sales semantic model.

        The application is designed for:

        - Sales executives
        - Sales managers
        - Sales representatives
        - Sales leadership
        - Sales analysts
        - Data and AI developers
        """
    )

    st.markdown(
        "### Semantic Model"
    )

    st.code(
        SEMANTIC_VIEW
    )

    st.markdown(
        "### Production Controls"
    )

    st.markdown(
        """
        **Read-only SQL validation**

        Analyst-generated SQL is checked before execution.

        **Result protection**

        Results are limited to the configured maximum row count.

        **Audit logging**

        Questions, responses, generated SQL, execution status,
        timing and request information can be logged.

        **Conversation context**

        Previous Cortex Analyst messages are preserved so that
        follow-up questions can reference previous analysis.

        **Business filters**

        Filters are supplied as business context to Cortex Analyst.
        The application does not construct physical sales SQL itself.

        **Technical details**

        Generated SQL and request information are hidden inside
        Technical Details sections so normal business users see
        a cleaner interface.
        """
    )

    st.markdown(
        "### Configuration"
    )

    config_col1, config_col2, config_col3 = (
        st.columns(3)
    )

    with config_col1:

        st.metric(
            "Application",
            APPLICATION_NAME
        )

    with config_col2:

        st.metric(
            "Semantic Model",
            SEMANTIC_MODEL_NAME
        )

    with config_col3:

        st.metric(
            "Max Result Rows",
            f"{MAX_RESULT_ROWS:,}"
        )