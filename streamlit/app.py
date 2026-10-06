# =============================================================================
# SALES AI - PRODUCTION STREAMLIT APPLICATION
# =============================================================================
#
# Snowflake-native Streamlit + Cortex Analyst
#
# Compatible with Snowflake Streamlit runtimes that do NOT support:
#   - st.chat_input()
#   - st.chat_message()
#
# Main capabilities:
#   - Cortex Analyst REST API
#   - Multi-turn conversations
#   - Business filters
#   - Date presets
#   - Sales role / answer style
#   - Read-only SQL validation
#   - Query execution
#   - Result limiting
#   - Query history
#   - Feedback
#   - CSV export
#   - Follow-up analysis
#   - Explain / Compare / Top Drivers
#   - Execution metrics
#
# Semantic model:
#   SALES_DATA.PUBLIC.SALES_SEMANTIC_MODEL
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
from datetime import date, datetime, timedelta

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
# 3. APPLICATION CONSTANTS
# =============================================================================

APPLICATION_NAME = "Sales AI"

SEMANTIC_VIEW = "SALES_DATA.PUBLIC.SALES_SEMANTIC_MODEL"

SEMANTIC_MODEL_NAME = "SALES_SEMANTIC_MODEL"

ANALYST_ENDPOINT = "/api/v2/cortex/analyst/message"

MAX_RESULT_ROWS = 10000

QUERY_HISTORY_LIMIT = 100

AUDIT_TABLE = "SALES_DATA.PUBLIC.ANALYST_QUERY_AUDIT_LOG"

FEEDBACK_TABLE = "SALES_DATA.PUBLIC.ANALYST_QUERY_FEEDBACK"

# Existing table from the original application.
# Used as a fallback if the new audit table has not yet been created.
LEGACY_LOG_TABLE = "SALES_DATA.PUBLIC.ANALYST_QUERY_LOG"


# =============================================================================
# 4. CUSTOM CSS
# =============================================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2.0rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .sub-title {
        color: #666666;
        font-size: 1rem;
        margin-bottom: 1rem;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 650;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }

    .answer-box {
        padding: 1rem 1.2rem;
        border-radius: 8px;
        border: 1px solid #dddddd;
        background-color: #fafafa;
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
        min-height: 110px;
    }

    .small-text {
        color: #666666;
        font-size: 0.85rem;
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
# 6. SESSION STATE INITIALIZATION
# =============================================================================

if "analyst_messages" not in st.session_state:
    st.session_state.analyst_messages = []

if "chat_turns" not in st.session_state:
    st.session_state.chat_turns = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

if "last_query_id" not in st.session_state:
    st.session_state.last_query_id = None

if "last_request_id" not in st.session_state:
    st.session_state.last_request_id = None

if "last_sql" not in st.session_state:
    st.session_state.last_sql = None

if "last_dataframe" not in st.session_state:
    st.session_state.last_dataframe = None

if "last_question" not in st.session_state:
    st.session_state.last_question = None

if "last_response" not in st.session_state:
    st.session_state.last_response = None

if "last_execution_status" not in st.session_state:
    st.session_state.last_execution_status = None

if "last_execution_seconds" not in st.session_state:
    st.session_state.last_execution_seconds = None

if "last_error" not in st.session_state:
    st.session_state.last_error = None

if "last_suggestions" not in st.session_state:
    st.session_state.last_suggestions = []

if "current_user" not in st.session_state:
    try:
        current_user_df = session.sql(
            "SELECT CURRENT_USER() AS USER_NAME"
        ).to_pandas()

        if not current_user_df.empty:
            st.session_state.current_user = str(
                current_user_df.iloc[0]["USER_NAME"]
            )
        else:
            st.session_state.current_user = "UNKNOWN"

    except Exception:
        st.session_state.current_user = "UNKNOWN"


# =============================================================================
# 7. HELPER FUNCTIONS
# =============================================================================

def get_current_user():
    """Return current Snowflake user."""
    return st.session_state.get("current_user", "UNKNOWN")


def clean_sql(sql_text):
    """Clean generated SQL before execution."""

    if sql_text is None:
        return ""

    sql_text = str(sql_text).strip()

    # Remove trailing semicolons.
    sql_text = sql_text.rstrip(";").strip()

    return sql_text


def remove_sql_comments(sql_text):
    """Remove SQL comments for safer validation."""

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


def remove_sql_string_literals(sql_text):
    """
    Replace SQL string literals before keyword validation.

    This reduces false positives such as:
        SELECT 'DELETE'
    """

    return re.sub(
        r"'(?:''|[^'])*'",
        " ",
        sql_text
    )


def validate_generated_sql(sql_text):
    """
    Conservative read-only SQL validation.

    Cortex Analyst should generate SELECT queries, but we still
    validate the result before execution.
    """

    sql_text = clean_sql(sql_text)

    if not sql_text:
        return False, "No SQL was generated."

    if len(sql_text) > 100000:
        return False, "Generated SQL is larger than the allowed limit."

    # Only allow one statement.
    # A semicolon inside a string has already been removed below.
    validation_sql = remove_sql_comments(sql_text)
    validation_sql = remove_sql_string_literals(validation_sql)

    if ";" in validation_sql:
        return False, "Multiple SQL statements are not allowed."

    normalized = validation_sql.strip().upper()

    if not (
        normalized.startswith("SELECT ")
        or normalized.startswith("SELECT\n")
        or normalized == "SELECT"
        or normalized.startswith("WITH ")
        or normalized.startswith("WITH\n")
    ):
        return False, "Only SELECT/WITH queries are allowed."

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
        "USE ",
    ]

    for keyword in blocked_keywords:
        if keyword in validation_sql.upper():
            return False, (
                "Generated SQL contains a non-read-only operation: "
                + keyword.strip()
            )

    return True, ""


def build_date_range(filter_name):
    """Return start/end dates for selected date filter."""

    today = date.today()

    if filter_name == "Today":
        return today, today

    if filter_name == "Yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday

    if filter_name == "Last 7 Days":
        return today - timedelta(days=6), today

    if filter_name == "Last 30 Days":
        return today - timedelta(days=29), today

    if filter_name == "Last 90 Days":
        return today - timedelta(days=89), today

    if filter_name == "Month to Date":
        return today.replace(day=1), today

    if filter_name == "Quarter to Date":
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1

        return (
            today.replace(
                month=quarter_start_month,
                day=1
            ),
            today
        )

    if filter_name == "Year to Date":
        return today.replace(month=1, day=1), today

    if filter_name == "Last Month":

        first_day_current_month = today.replace(day=1)

        last_day_previous_month = (
            first_day_current_month - timedelta(days=1)
        )

        first_day_previous_month = (
            last_day_previous_month.replace(day=1)
        )

        return (
            first_day_previous_month,
            last_day_previous_month
        )

    if filter_name == "Last Quarter":

        current_quarter = (today.month - 1) // 3

        if current_quarter == 0:
            previous_quarter_year = today.year - 1
            previous_quarter = 3
        else:
            previous_quarter_year = today.year
            previous_quarter = current_quarter - 1

        start_month = previous_quarter * 3 + 1

        start_date = date(
            previous_quarter_year,
            start_month,
            1
        )

        if start_month == 10:
            end_date = date(
                previous_quarter_year,
                12,
                31
            )
        else:
            next_quarter_start = date(
                previous_quarter_year,
                start_month + 3,
                1
            )

            end_date = next_quarter_start - timedelta(days=1)

        return start_date, end_date

    if filter_name == "Last Year":
        return (
            date(today.year - 1, 1, 1),
            date(today.year - 1, 12, 31)
        )

    return None, None


def build_business_context():
    """
    Convert UI filters into natural-language context for Cortex Analyst.

    We intentionally do NOT construct SQL here.

    The semantic model remains responsible for selecting the
    correct physical dimensions/measures.
    """

    context_lines = []

    business_role = st.session_state.get(
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

    region = st.session_state.get("filter_region", "").strip()
    territory = st.session_state.get("filter_territory", "").strip()
    sales_rep = st.session_state.get("filter_sales_rep", "").strip()
    customer = st.session_state.get("filter_customer", "").strip()
    industry = st.session_state.get("filter_industry", "").strip()
    product = st.session_state.get("filter_product", "").strip()
    product_category = st.session_state.get(
        "filter_product_category",
        ""
    ).strip()
    channel = st.session_state.get("filter_channel", "").strip()

    comparison = st.session_state.get(
        "comparison_period",
        "No Comparison"
    )

    context_lines.append(
        f"Answer from the perspective of a {business_role}."
    )

    context_lines.append(
        f"Preferred answer style: {answer_style}."
    )

    if date_filter != "Custom":

        start_date, end_date = build_date_range(date_filter)

        if start_date and end_date:
            context_lines.append(
                f"Primary date filter: {date_filter} "
                f"({start_date.isoformat()} through "
                f"{end_date.isoformat()})."
            )

    else:

        custom_start = st.session_state.get(
            "custom_start_date"
        )

        custom_end = st.session_state.get(
            "custom_end_date"
        )

        if custom_start and custom_end:
            context_lines.append(
                "Primary date filter: Custom "
                f"({custom_start.isoformat()} through "
                f"{custom_end.isoformat()})."
            )

    if comparison != "No Comparison":
        context_lines.append(
            f"Comparison requested by application filter: {comparison}."
        )

    filters = [
        ("Region", region),
        ("Territory", territory),
        ("Sales Rep", sales_rep),
        ("Customer", customer),
        ("Industry", industry),
        ("Product", product),
        ("Product Category", product_category),
        ("Channel", channel),
    ]

    for label, value in filters:
        if value and value.lower() not in ("all", "any"):
            context_lines.append(
                f"{label} filter: {value}."
            )

    context_lines.append(
        "Apply these application filters unless the user's "
        "question explicitly asks for a different value or period."
    )

    return "\n".join(context_lines)


def build_analyst_question(user_question):
    """Combine user question and application context."""

    business_context = build_business_context()

    return f"""
User's sales question:
{user_question}

Application business context:
{business_context}

Instructions:
- Use the configured semantic model.
- Answer the user's actual business question.
- Respect the application filters unless explicitly overridden by the user.
- Do not invent metrics, dimensions, customers, products, or values.
- Prefer concise business explanations.
- If the user asks for a comparison, clearly identify the comparison periods.
""".strip()


# =============================================================================
# 8. CORTEX ANALYST API
# =============================================================================

def ask_cortex_analyst(user_question):
    """
    Send question to Cortex Analyst using Snowflake's native REST API.

    This avoids calling:
        SNOWFLAKE.CORTEX.ANALYST(...)
    """

    analyst_question = build_analyst_question(user_question)

    # Start with previous Analyst conversation.
    messages = list(st.session_state.analyst_messages)

    # Add current user message using Cortex Analyst API format.
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

    api_start = time.perf_counter()

    try:

        response = _snowflake.send_snow_api_request(
            method="POST",
            endpoint=ANALYST_ENDPOINT,
            headers={
                "Content-Type": "application/json"
            },
            body=request_body
        )

        api_seconds = time.perf_counter() - api_start

        return response, api_seconds

    except Exception as exc:

        api_seconds = time.perf_counter() - api_start

        return {
            "status": 500,
            "content": {
                "error": str(exc)
            }
        }, api_seconds


# =============================================================================
# 9. ANALYST RESPONSE PARSER
# =============================================================================

def extract_analyst_response(api_response):
    """
    Extract text, SQL, suggestions and raw assistant message
    from Cortex Analyst response.
    """

    result = {
        "success": False,
        "text": "",
        "sql": None,
        "suggestions": [],
        "assistant_message": None,
        "request_id": None,
        "error": None,
    }

    if not isinstance(api_response, dict):
        result["error"] = "Invalid response returned by Cortex Analyst."
        return result

    status = api_response.get("status")

    # Try several possible request ID locations.
    result["request_id"] = (
        api_response.get("request_id")
        or api_response.get("requestId")
    )

    headers = api_response.get("headers")

    if isinstance(headers, dict):

        result["request_id"] = (
            result["request_id"]
            or headers.get("X-Snowflake-Request-ID")
            or headers.get("x-snowflake-request-id")
            or headers.get("X-Request-ID")
            or headers.get("x-request-id")
        )

    content = api_response.get("content")

    if status != 200:

        if isinstance(content, dict):

            error_value = (
                content.get("message")
                or content.get("error")
                or content.get("detail")
            )

            if isinstance(error_value, dict):
                error_value = json.dumps(error_value)

        else:
            error_value = str(content)

        result["error"] = (
            f"Cortex Analyst request failed "
            f"(HTTP {status}): {error_value}"
        )

        return result

    # API content may already be a dictionary.
    if isinstance(content, str):

        try:
            content = json.loads(content)

        except Exception:

            result["error"] = (
                "Cortex Analyst returned an unreadable response."
            )

            return result

    if not isinstance(content, dict):

        result["error"] = (
            "Cortex Analyst returned an unexpected response format."
        )

        return result

    # Sometimes request ID is present in the parsed body.
    result["request_id"] = (
        result["request_id"]
        or content.get("request_id")
        or content.get("requestId")
    )

    response_message = content.get("message")

    if not isinstance(response_message, dict):

        result["error"] = (
            "Cortex Analyst response did not contain a message."
        )

        return result

    message_content = response_message.get("content", [])

    if not isinstance(message_content, list):

        result["error"] = (
            "Cortex Analyst response content was invalid."
        )

        return result

    result["assistant_message"] = {
        "role": "assistant",
        "content": message_content
    }

    text_parts = []
    suggestions = []

    for item in message_content:

        if not isinstance(item, dict):
            continue

        item_type = item.get("type")

        if item_type == "text":

            text_value = item.get("text", "")

            if text_value:
                text_parts.append(str(text_value))

        elif item_type == "sql":

            sql_value = (
                item.get("statement")
                or item.get("sql")
                or item.get("query")
            )

            if sql_value:
                result["sql"] = str(sql_value)

        elif item_type == "suggestions":

            suggestion_values = (
                item.get("suggestions")
                or item.get("items")
                or []
            )

            if isinstance(suggestion_values, list):

                for suggestion in suggestion_values:

                    if isinstance(suggestion, str):
                        suggestions.append(suggestion)

                    elif isinstance(suggestion, dict):

                        text_value = (
                            suggestion.get("text")
                            or suggestion.get("question")
                            or suggestion.get("suggestion")
                        )

                        if text_value:
                            suggestions.append(
                                str(text_value)
                            )

    result["text"] = "\n\n".join(text_parts).strip()

    result["suggestions"] = suggestions[:5]

    result["success"] = True

    return result


# =============================================================================
# 10. SQL EXECUTION
# =============================================================================

def execute_generated_sql(generated_sql):
    """
    Execute Analyst-generated SQL safely.

    We wrap the generated query and apply a maximum result-row limit.

    Example:

        SELECT *
        FROM (
            <Cortex Analyst SQL>
        ) AS ANALYST_RESULT
        LIMIT 10000
    """

    generated_sql = clean_sql(generated_sql)

    valid, validation_error = validate_generated_sql(
        generated_sql
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

        dataframe = session.sql(
            wrapped_sql
        ).to_pandas()

        execution_seconds = (
            time.perf_counter() - start_time
        )

        return {
            "success": True,
            "dataframe": dataframe,
            "seconds": execution_seconds,
            "rows": len(dataframe),
            "error": None
        }

    except Exception as exc:

        execution_seconds = (
            time.perf_counter() - start_time
        )

        return {
            "success": False,
            "dataframe": None,
            "seconds": execution_seconds,
            "rows": 0,
            "error": str(exc)
        }


# =============================================================================
# 11. QUERY AUDIT LOGGING
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
    error_message=None
):
    """
    Write production audit record.

    Preferred table:
        ANALYST_QUERY_AUDIT_LOG

    If it does not exist, fall back to the original:
        ANALYST_QUERY_LOG
    """

    current_user = get_current_user()

    try:

        insert_sql = f"""
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
    ?, CURRENT_TIMESTAMP(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
)
"""

        session.sql(
            insert_sql,
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

        # Backward compatibility with original logging table.
        try:

            legacy_insert = f"""
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

            legacy_response = response_text or ""

            if error_message:
                legacy_response += (
                    "\n\nExecution Error: "
                    + str(error_message)
                )

            session.sql(
                legacy_insert,
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
# 12. FEEDBACK LOGGING
# =============================================================================

def log_feedback(
    query_id,
    feedback
):
    """Store user feedback."""

    current_user = get_current_user()

    try:

        feedback_sql = f"""
INSERT INTO {FEEDBACK_TABLE}
(
    QUERY_ID,
    FEEDBACK_TIMESTAMP,
    USER_NAME,
    FEEDBACK
)
VALUES
(
    ?, CURRENT_TIMESTAMP(), ?, ?
)
"""

        session.sql(
            feedback_sql,
            params=[
                query_id,
                current_user,
                feedback
            ]
        ).collect()

        return True

    except Exception:

        # Do not break the application if feedback table
        # has not yet been created.
        return False


# =============================================================================
# 13. RESULT VISUALIZATION
# =============================================================================

def display_result_visualization(dataframe):
    """
    Provide a lightweight automatic visualization when the result
    contains a suitable date/category column and numeric measure.
    """

    if dataframe is None or dataframe.empty:
        return

    if len(dataframe.columns) < 2:
        return

    numeric_columns = list(
        dataframe.select_dtypes(
            include=["number"]
        ).columns
    )

    if not numeric_columns:
        return

    date_columns = []

    for column in dataframe.columns:

        column_name = str(column).upper()

        if (
            "DATE" in column_name
            or "DAY" in column_name
            or "MONTH" in column_name
            or "YEAR" in column_name
            or "WEEK" in column_name
            or "TIME" in column_name
        ):
            date_columns.append(column)

    if not date_columns:
        return

    x_column = date_columns[0]
    y_column = numeric_columns[0]

    st.markdown("#### Quick Visualization")

    try:

        chart_df = dataframe[
            [x_column, y_column]
        ].copy()

        chart_df[x_column] = pd.to_datetime(
            chart_df[x_column],
            errors="coerce"
        )

        chart_df = chart_df.dropna(
            subset=[x_column]
        )

        if chart_df.empty:
            return

        chart_df = chart_df.sort_values(
            by=x_column
        )

        chart_df = chart_df.set_index(
            x_column
        )

        st.line_chart(
            chart_df[[y_column]]
        )

    except Exception:
        pass


# =============================================================================
# 14. DISPLAY FILTER SUMMARY
# =============================================================================

def display_filter_summary():

    date_filter = st.session_state.get(
        "date_filter",
        "Last 30 Days"
    )

    region = st.session_state.get(
        "filter_region",
        ""
    ).strip()

    territory = st.session_state.get(
        "filter_territory",
        ""
    ).strip()

    sales_rep = st.session_state.get(
        "filter_sales_rep",
        ""
    ).strip()

    customer = st.session_state.get(
        "filter_customer",
        ""
    ).strip()

    product = st.session_state.get(
        "filter_product",
        ""
    ).strip()

    channel = st.session_state.get(
        "filter_channel",
        ""
    ).strip()

    summary = [
        f"Date: {date_filter}"
    ]

    if region:
        summary.append(f"Region: {region}")

    if territory:
        summary.append(f"Territory: {territory}")

    if sales_rep:
        summary.append(f"Sales Rep: {sales_rep}")

    if customer:
        summary.append(f"Customer: {customer}")

    if product:
        summary.append(f"Product: {product}")

    if channel:
        summary.append(f"Channel: {channel}")

    st.markdown(
        '<div class="filter-box">'
        "<strong>Active Business Context</strong><br>"
        + " | ".join(summary)
        + "</div>",
        unsafe_allow_html=True
    )


# =============================================================================
# 15. PROCESS A QUESTION
# =============================================================================

def process_question(user_question):
    """
    Complete question-processing pipeline:

        User Question
            ↓
        Business Context
            ↓
        Cortex Analyst
            ↓
        Generated SQL
            ↓
        SQL Validation
            ↓
        Snowflake Execution
            ↓
        Result
            ↓
        Audit Logging
    """

    user_question = str(user_question).strip()

    if not user_question:
        return

    query_id = str(uuid.uuid4())

    analyst_question = build_analyst_question(
        user_question
    )

    st.session_state.last_query_id = query_id
    st.session_state.last_question = user_question
    st.session_state.last_sql = None
    st.session_state.last_dataframe = None
    st.session_state.last_error = None
    st.session_state.last_execution_status = "RUNNING"
    st.session_state.last_suggestions = []

    # -------------------------------------------------------------------------
    # Show question immediately.
    # -------------------------------------------------------------------------

    st.markdown(
        '<div class="section-title">Your Question</div>',
        unsafe_allow_html=True
    )

    st.markdown(user_question)

    # -------------------------------------------------------------------------
    # Call Cortex Analyst.
    # -------------------------------------------------------------------------

    with st.spinner("Sales AI is analyzing your question..."):

        api_response, analyst_seconds = ask_cortex_analyst(
            user_question
        )

    parsed = extract_analyst_response(
        api_response
    )

    request_id = parsed.get(
        "request_id"
    )

    st.session_state.last_request_id = request_id

    if not parsed["success"]:

        error_message = parsed.get(
            "error",
            "Cortex Analyst request failed."
        )

        st.session_state.last_execution_status = "ANALYST_ERROR"
        st.session_state.last_error = error_message

        st.error(
            "Sales AI could not process the question."
        )

        with st.expander("Technical Details"):

            st.code(
                error_message
            )

        log_query(
            query_id=query_id,
            user_question=user_question,
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

    st.session_state.last_response = response_text
    st.session_state.last_sql = generated_sql
    st.session_state.last_suggestions = suggestions

    # -------------------------------------------------------------------------
    # IMPORTANT:
    #
    # Preserve the actual Cortex Analyst assistant message structure.
    # This allows future follow-up questions to remain valid.
    # -------------------------------------------------------------------------

    assistant_message = parsed.get(
        "assistant_message"
    )

    if assistant_message:

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

        st.session_state.analyst_messages.append(
            assistant_message
        )

    # -------------------------------------------------------------------------
    # Display Analyst answer.
    # -------------------------------------------------------------------------

    st.markdown(
        '<div class="section-title">Sales AI Answer</div>',
        unsafe_allow_html=True
    )

    if response_text:

        st.markdown(
            '<div class="answer-box">'
            + response_text
            + "</div>",
            unsafe_allow_html=True
        )

    else:

        st.info(
            "Cortex Analyst generated SQL for this question."
        )

    # -------------------------------------------------------------------------
    # Execute generated SQL.
    # -------------------------------------------------------------------------

    execution_result = {
        "success": False,
        "dataframe": None,
        "seconds": 0,
        "rows": 0,
        "error": None
    }

    if generated_sql:

        valid_sql, validation_error = validate_generated_sql(
            generated_sql
        )

        if not valid_sql:

            execution_result["error"] = validation_error

            st.warning(
                "The generated query was not executed because "
                "it did not pass the read-only safety check."
            )

            with st.expander("Technical Details"):

                st.code(
                    validation_error
                )

        else:

            with st.spinner("Running analysis in Snowflake..."):

                execution_result = execute_generated_sql(
                    generated_sql
                )

            if execution_result["success"]:

                dataframe = execution_result["dataframe"]

                st.session_state.last_dataframe = dataframe
                st.session_state.last_execution_status = "SUCCESS"
                st.session_state.last_execution_seconds = (
                    execution_result["seconds"]
                )

                if dataframe is not None:

                    st.markdown(
                        "#### Results"
                    )

                    st.dataframe(
                        dataframe,
                        use_container_width=True,
                        height=420
                    )

                    display_result_visualization(
                        dataframe
                    )

                    csv_data = dataframe.to_csv(
                        index=False
                    ).encode("utf-8")

                    st.download_button(
                        label="Download Results as CSV",
                        data=csv_data,
                        file_name=(
                            "sales_ai_result_"
                            + query_id[:8]
                            + ".csv"
                        ),
                        mime="text/csv",
                        use_container_width=False
                    )

            else:

                st.session_state.last_execution_status = (
                    "SQL_ERROR"
                )

                st.session_state.last_error = (
                    execution_result["error"]
                )

                st.error(
                    "Sales AI generated a query, but Snowflake "
                    "could not execute it."
                )

                with st.expander("Technical Details"):

                    st.code(
                        execution_result["error"]
                    )

    else:

        st.session_state.last_execution_status = (
            "ANSWER_ONLY"
        )

    # -------------------------------------------------------------------------
    # Technical details.
    # -------------------------------------------------------------------------

    with st.expander("Technical Details"):

        col1, col2, col3, col4 = st.columns(4)

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
                st.session_state.last_execution_status
            )

        if request_id:
            st.caption(
                f"Request ID: {request_id}"
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
    # Audit logging.
    # -------------------------------------------------------------------------

    log_query(
        query_id=query_id,
        user_question=user_question,
        analyst_question=analyst_question,
        response_text=response_text,
        generated_sql=generated_sql,
        request_id=request_id,
        execution_status=st.session_state.last_execution_status,
        analyst_seconds=analyst_seconds,
        execution_seconds=execution_result["seconds"],
        rows_returned=execution_result["rows"],
        error_message=execution_result["error"]
    )

    # -------------------------------------------------------------------------
    # Feedback.
    # -------------------------------------------------------------------------

    st.markdown(
        "#### Was this analysis useful?"
    )

    feedback_col1, feedback_col2 = st.columns(2)

    with feedback_col1:

        if st.button(
            "👍 Helpful",
            key=f"helpful_{query_id}",
            use_container_width=True
        ):

            if log_feedback(
                query_id,
                "HELPFUL"
            ):
                st.success(
                    "Thanks for your feedback."
                )
            else:
                st.info(
                    "Feedback could not be recorded."
                )

    with feedback_col2:

        if st.button(
            "👎 Not Helpful",
            key=f"not_helpful_{query_id}",
            use_container_width=True
        ):

            if log_feedback(
                query_id,
                "NOT_HELPFUL"
            ):
                st.success(
                    "Thanks. Your feedback was recorded."
                )
            else:
                st.info(
                    "Feedback could not be recorded."
                )

    # -------------------------------------------------------------------------
    # Suggestions.
    # -------------------------------------------------------------------------

    if suggestions:

        st.markdown(
            "#### Suggested Follow-ups"
        )

        for index, suggestion in enumerate(
            suggestions
        ):

            if st.button(
                suggestion,
                key=f"suggestion_{query_id}_{index}",
                use_container_width=True
            ):

                st.session_state.pending_question = (
                    suggestion
                )

                st.rerun()


# =============================================================================
# 16. APPLICATION HEADER
# =============================================================================

st.markdown(
    '<div class="main-title">📊 Sales AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    "Business-friendly sales analytics powered by Snowflake "
    "and Cortex Analyst"
    "</div>",
    unsafe_allow_html=True
)


# =============================================================================
# 17. SIDEBAR - BUSINESS CONTROLS
# =============================================================================

with st.sidebar:

    st.markdown(
        "## Business Controls"
    )

    st.caption(
        f"User: {get_current_user()}"
    )

    st.markdown(
        "---"
    )

    # -------------------------------------------------------------------------
    # Business Role
    # -------------------------------------------------------------------------

    business_role = st.selectbox(
        "Business Role",
        [
            "Sales Executive",
            "Sales Manager",
            "Sales Representative",
            "Sales Leadership",
            "Sales Analyst",
            "Data / AI Developer"
        ],
        key="business_role"
    )

    # -------------------------------------------------------------------------
    # Answer Style
    # -------------------------------------------------------------------------

    answer_style = st.selectbox(
        "Answer Style",
        [
            "Executive Summary",
            "Detailed Analysis",
            "Data Focused",
            "Trend Analysis",
            "Action Oriented"
        ],
        key="answer_style"
    )

    st.markdown(
        "---"
    )

    # -------------------------------------------------------------------------
    # Date Filter
    # -------------------------------------------------------------------------

    date_options = [
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
    ]

    if "date_filter" not in st.session_state:
        st.session_state.date_filter = "Last 30 Days"

    date_filter = st.selectbox(
        "Date Range",
        date_options,
        key="date_filter"
    )

    if date_filter == "Custom":

        if "custom_start_date" not in st.session_state:
            st.session_state.custom_start_date = (
                date.today() - timedelta(days=29)
            )

        if "custom_end_date" not in st.session_state:
            st.session_state.custom_end_date = date.today()

        st.date_input(
            "Start Date",
            key="custom_start_date"
        )

        st.date_input(
            "End Date",
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
    # Comparison
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
        key="comparison_period"
    )

    st.markdown(
        "---"
    )

    # -------------------------------------------------------------------------
    # Sales Filters
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
    # Reset
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

        st.session_state.custom_start_date = (
            date.today() - timedelta(days=29)
        )

        st.session_state.custom_end_date = date.today()

        for key in [
            "filter_region",
            "filter_territory",
            "filter_sales_rep",
            "filter_customer",
            "filter_industry",
            "filter_product",
            "filter_product_category",
            "filter_channel"
        ]:
            st.session_state[key] = ""

        st.rerun()

    st.markdown(
        "---"
    )

    # -------------------------------------------------------------------------
    # New Conversation
    # -------------------------------------------------------------------------

    if st.button(
        "Start New Conversation",
        use_container_width=True
    ):

        st.session_state.analyst_messages = []

        st.session_state.chat_turns = []

        st.session_state.pending_question = None

        st.session_state.last_question = None

        st.session_state.last_response = None

        st.session_state.last_sql = None

        st.session_state.last_dataframe = None

        st.session_state.last_error = None

        st.session_state.last_suggestions = []

        st.rerun()


# =============================================================================
# 18. MAIN TABS
# =============================================================================

tab_overview, tab_ai, tab_history, tab_samples, tab_about = st.tabs(
    [
        "Executive Overview",
        "Sales AI",
        "Query History",
        "Sample Questions",
        "About"
    ]
)


# =============================================================================
# 19. EXECUTIVE OVERVIEW
# =============================================================================

with tab_overview:

    st.markdown(
        "## Executive Overview"
    )

    display_filter_summary()

    st.info(
        "Use Sales AI to generate live business analysis from "
        "your governed sales semantic model."
    )

    # -------------------------------------------------------------------------
    # KPI-style capability cards
    # -------------------------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.markdown(
            """
            <div class="metric-box">
            <strong>Revenue</strong><br>
            Analyze revenue, growth, trends and performance.
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            """
            <div class="metric-box">
            <strong>Sales Team</strong><br>
            Understand rep and territory performance.
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:

        st.markdown(
            """
            <div class="metric-box">
            <strong>Customers</strong><br>
            Identify top customers, risks and opportunities.
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:

        st.markdown(
            """
            <div class="metric-box">
            <strong>Products</strong><br>
            Analyze product and category performance.
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        "### Recommended Business Analyses"
    )

    recommended_questions = [
        "What was total revenue during the selected period?",
        "Which regions are performing best?",
        "Which sales reps have the highest revenue?",
        "Which customers contributed the most revenue?",
        "Which products are growing fastest?",
        "How does the selected period compare with the previous period?",
        "What are the biggest sales performance risks?",
        "Where should the sales team focus next?"
    ]

    for question in recommended_questions:

        st.markdown(
            f"- {question}"
        )

    st.markdown(
        "### How to Use"
    )

    st.markdown(
        """
        1. Set your business filters in the left panel.
        2. Open **Sales AI**.
        3. Ask a natural-language sales question.
        4. Review the business answer.
        5. Review the data results when available.
        6. Use suggested follow-up questions for deeper analysis.
        """
    )


# =============================================================================
# 20. SALES AI
# =============================================================================

with tab_ai:

    st.markdown(
        "## Sales AI"
    )

    display_filter_summary()

    # -------------------------------------------------------------------------
    # Quick Questions
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

    for index, question in enumerate(
        quick_questions
    ):

        with quick_columns[index]:

            if st.button(
                question,
                key=f"quick_question_{index}",
                use_container_width=True
            ):

                st.session_state.pending_question = (
                    question
                )

                st.rerun()

    st.markdown(
        "---"
    )

    # -------------------------------------------------------------------------
    # Question Input
    #
    # IMPORTANT:
    # No st.chat_input()
    # No st.chat_message()
    # -------------------------------------------------------------------------

    st.markdown(
        "### Ask a Business Question"
    )

    typed_question = st.text_area(
        "Sales question",
        placeholder=(
            "Examples:\n"
            "• What was revenue last month by region?\n"
            "• Which sales reps are below target?\n"
            "• Show top 10 customers by revenue.\n"
            "• Compare this quarter with last quarter.\n"
            "• Which products are declining?"
        ),
        height=120,
        key="question_input"
    )

    input_col1, input_col2 = st.columns(
        [1, 5]
    )

    with input_col1:

        ask_button = st.button(
            "Ask Sales AI",
            type="primary",
            use_container_width=True
        )

    with input_col2:

        clear_question = st.button(
            "Clear Question",
            use_container_width=True
        )

    if clear_question:

        st.session_state.question_input = ""

        st.rerun()

    if ask_button:

        if typed_question.strip():

            st.session_state.pending_question = (
                typed_question.strip()
            )

            st.rerun()

        else:

            st.warning(
                "Please enter a sales question."
            )

    # -------------------------------------------------------------------------
    # Conversation History
    # -------------------------------------------------------------------------

    if st.session_state.chat_turns:

        st.markdown(
            "---"
        )

        st.markdown(
            "### Conversation"
        )

        for turn_index, turn in enumerate(
            st.session_state.chat_turns
        ):

            role = turn.get(
                "role"
            )

            if role == "user":

                st.markdown(
                    "#### You"
                )

                st.markdown(
                    turn.get("text", "")
                )

            else:

                st.markdown(
                    "#### Sales AI"
                )

                assistant_text = turn.get(
                    "text",
                    ""
                )

                if assistant_text:

                    st.markdown(
                        '<div class="answer-box">'
                        + assistant_text
                        + "</div>",
                        unsafe_allow_html=True
                    )

                turn_sql = turn.get(
                    "sql"
                )

                turn_df = turn.get(
                    "dataframe"
                )

                turn_status = turn.get(
                    "status"
                )

                turn_seconds = turn.get(
                    "execution_seconds"
                )

                turn_request_id = turn.get(
                    "request_id"
                )

                turn_query_id = turn.get(
                    "query_id"
                )

                if (
                    turn_df is not None
                    and isinstance(turn_df, pd.DataFrame)
                ):

                    st.markdown(
                        "##### Results"
                    )

                    st.dataframe(
                        turn_df,
                        use_container_width=True,
                        height=350
                    )

                    csv_data = turn_df.to_csv(
                        index=False
                    ).encode("utf-8")

                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=(
                            "sales_ai_"
                            + str(turn_query_id)[:8]
                            + ".csv"
                        ),
                        mime="text/csv",
                        key=f"download_{turn_query_id}",
                        use_container_width=False
                    )

                if turn_sql:

                    with st.expander(
                        "Generated SQL"
                    ):

                        st.code(
                            turn_sql,
                            language="sql"
                        )

                metadata_parts = []

                if turn_status:
                    metadata_parts.append(
                        f"Status: {turn_status}"
                    )

                if turn_seconds is not None:
                    metadata_parts.append(
                        f"SQL: {turn_seconds:.2f}s"
                    )

                if turn_request_id:
                    metadata_parts.append(
                        f"Request ID: {turn_request_id}"
                    )

                if metadata_parts:

                    st.caption(
                        " | ".join(metadata_parts)
                    )

                turn_suggestions = turn.get(
                    "suggestions",
                    []
                )

                if turn_suggestions:

                    st.markdown(
                        "##### Follow-up Questions"
                    )

                    for suggestion_index, suggestion in enumerate(
                        turn_suggestions
                    ):

                        if st.button(
                            suggestion,
                            key=(
                                f"turn_suggestion_"
                                f"{turn_query_id}_"
                                f"{suggestion_index}"
                            ),
                            use_container_width=True
                        ):

                            st.session_state.pending_question = (
                                suggestion
                            )

                            st.rerun()

            st.markdown(
                "---"
            )

    # -------------------------------------------------------------------------
    # Pending question
    # -------------------------------------------------------------------------

    pending_question = (
        st.session_state.get(
            "pending_question"
        )
    )

    if pending_question:

        st.session_state.pending_question = None

        # Add user turn.
        st.session_state.chat_turns.append(
            {
                "role": "user",
                "text": pending_question
            }
        )

        # Display processing area.
        st.markdown(
            "### Processing"
        )

        # Call Cortex Analyst.
        with st.spinner(
            "Sales AI is analyzing your question..."
        ):

            query_id = str(uuid.uuid4())

            analyst_question = build_analyst_question(
                pending_question
            )

            api_response, analyst_seconds = ask_cortex_analyst(
                pending_question
            )

        parsed = extract_analyst_response(
            api_response
        )

        request_id = parsed.get(
            "request_id"
        )

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

        execution_result = {
            "success": False,
            "dataframe": None,
            "seconds": 0,
            "rows": 0,
            "error": None
        }

        execution_status = "ANALYST_ERROR"

        if not parsed["success"]:

            error_message = parsed.get(
                "error",
                "Cortex Analyst request failed."
            )

            st.error(
                "Sales AI could not process the question."
            )

            with st.expander(
                "Technical Details"
            ):

                st.code(
                    error_message
                )

            log_query(
                query_id=query_id,
                user_question=pending_question,
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

            st.session_state.chat_turns.append(
                {
                    "role": "assistant",
                    "text": (
                        "I could not process that question. "
                        "Please try again."
                    ),
                    "sql": None,
                    "dataframe": None,
                    "status": "ANALYST_ERROR",
                    "execution_seconds": 0,
                    "request_id": request_id,
                    "query_id": query_id,
                    "suggestions": []
                }
            )

        else:

            # Preserve Analyst conversation.
            assistant_message = parsed.get(
                "assistant_message"
            )

            if assistant_message:

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

                st.session_state.analyst_messages.append(
                    assistant_message
                )

            # Execute SQL if Analyst generated it.
            if generated_sql:

                execution_result = execute_generated_sql(
                    generated_sql
                )

                if execution_result["success"]:

                    execution_status = "SUCCESS"

                else:

                    execution_status = "SQL_ERROR"

            else:

                execution_status = "ANSWER_ONLY"

            # ---------------------------------------------------------------
            # Display current answer
            # ---------------------------------------------------------------

            st.markdown(
                "### Sales AI Answer"
            )

            if response_text:

                st.markdown(
                    '<div class="answer-box">'
                    + response_text
                    + "</div>",
                    unsafe_allow_html=True
                )

            # ---------------------------------------------------------------
            # Display result
            # ---------------------------------------------------------------

            result_dataframe = None

            if execution_result["success"]:

                result_dataframe = (
                    execution_result["dataframe"]
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

                    csv_data = result_dataframe.to_csv(
                        index=False
                    ).encode("utf-8")

                    st.download_button(
                        label="Download Results as CSV",
                        data=csv_data,
                        file_name=(
                            "sales_ai_result_"
                            + query_id[:8]
                            + ".csv"
                        ),
                        mime="text/csv",
                        key=f"current_download_{query_id}",
                        use_container_width=False
                    )

                    display_result_visualization(
                        result_dataframe
                    )

            elif generated_sql:

                st.error(
                    "The generated query could not be executed "
                    "in Snowflake."
                )

                with st.expander(
                    "Technical Details"
                ):

                    st.code(
                        execution_result["error"]
                    )

            # ---------------------------------------------------------------
            # Technical details
            # ---------------------------------------------------------------

            with st.expander(
                "Technical Details"
            ):

                col1, col2, col3, col4 = st.columns(4)

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
                        f"Request ID: {request_id}"
                    )

                if generated_sql:

                    st.markdown(
                        "#### Generated SQL"
                    )

                    st.code(
                        generated_sql,
                        language="sql"
                    )

            # ---------------------------------------------------------------
            # Save conversation turn
            # ---------------------------------------------------------------

            st.session_state.chat_turns.append(
                {
                    "role": "assistant",
                    "text": response_text,
                    "sql": generated_sql,
                    "dataframe": result_dataframe,
                    "status": execution_status,
                    "execution_seconds": (
                        execution_result["seconds"]
                    ),
                    "request_id": request_id,
                    "query_id": query_id,
                    "suggestions": suggestions
                }
            )

            # ---------------------------------------------------------------
            # Audit log
            # ---------------------------------------------------------------

            log_query(
                query_id=query_id,
                user_question=pending_question,
                analyst_question=analyst_question,
                response_text=response_text,
                generated_sql=generated_sql,
                request_id=request_id,
                execution_status=execution_status,
                analyst_seconds=analyst_seconds,
                execution_seconds=execution_result["seconds"],
                rows_returned=execution_result["rows"],
                error_message=execution_result["error"]
            )

            # ---------------------------------------------------------------
            # Feedback
            # ---------------------------------------------------------------

            st.markdown(
                "### Was this analysis useful?"
            )

            feedback_col1, feedback_col2 = st.columns(2)

            with feedback_col1:

                if st.button(
                    "👍 Helpful",
                    key=f"current_helpful_{query_id}",
                    use_container_width=True
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
                    key=f"current_not_helpful_{query_id}",
                    use_container_width=True
                ):

                    if log_feedback(
                        query_id,
                        "NOT_HELPFUL"
                    ):

                        st.success(
                            "Thanks for your feedback."
                        )

            # ---------------------------------------------------------------
            # Suggestions
            # ---------------------------------------------------------------

            if suggestions:

                st.markdown(
                    "### Suggested Follow-ups"
                )

                suggestion_columns = st.columns(
                    min(len(suggestions), 3)
                )

                for index, suggestion in enumerate(
                    suggestions
                ):

                    with suggestion_columns[
                        index % len(suggestion_columns)
                    ]:

                        if st.button(
                            suggestion,
                            key=(
                                f"current_suggestion_"
                                f"{query_id}_"
                                f"{index}"
                            ),
                            use_container_width=True
                        ):

                            st.session_state.pending_question = (
                                suggestion
                            )

                            st.rerun()


# =============================================================================
# 21. QUERY HISTORY
# =============================================================================

with tab_history:

    st.markdown(
        "## Query History"
    )

    st.caption(
        "Recent questions asked through Sales AI."
    )

    history_search = st.text_input(
        "Search history",
        placeholder="Search questions or users...",
        key="history_search"
    )

    refresh_history = st.button(
        "Refresh History"
    )

    history_df = None

    try:

        history_sql = f"""
SELECT
    QUERY_TIMESTAMP,
    USER_NAME,
    USER_QUESTION,
    RESPONSE,
    SEMANTIC_MODEL_NAME
FROM {AUDIT_TABLE}
ORDER BY QUERY_TIMESTAMP DESC
LIMIT {QUERY_HISTORY_LIMIT}
"""

        history_df = session.sql(
            history_sql
        ).to_pandas()

    except Exception:

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

            history_df = session.sql(
                history_sql
            ).to_pandas()

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

    if history_df is not None:

        if history_search.strip():

            search_value = (
                history_search.strip().lower()
            )

            mask = (
                history_df.astype(str)
                .apply(
                    lambda column: column.str.lower().str.contains(
                        search_value,
                        na=False
                    )
                )
                .any(axis=1)
            )

            history_df = history_df[
                mask
            ]

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

            history_csv = history_df.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                label="Download History CSV",
                data=history_csv,
                file_name="sales_ai_query_history.csv",
                mime="text/csv"
            )


# =============================================================================
# 22. SAMPLE QUESTIONS
# =============================================================================

with tab_samples:

    st.markdown(
        "## Sample Business Questions"
    )

    st.markdown(
        "Use these examples as starting points."
    )

    sample_groups = {
        "Revenue & Performance": [
            "What was total revenue last month?",
            "Show revenue by region for the last 30 days.",
            "What is the revenue trend this quarter?",
            "Which regions grew the most compared with the previous period?"
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

        "Regional Analysis": [
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

    for group_name, questions in sample_groups.items():

        st.markdown(
            f"### {group_name}"
        )

        for question in questions:

            st.markdown(
                f"- {question}"
            )


# =============================================================================
# 23. ABOUT
# =============================================================================

with tab_about:

    st.markdown(
        "## About Sales AI"
    )

    st.markdown(
        """
        **Sales AI** is a Snowflake-native business analytics application
        designed to allow sales teams to ask questions using natural language.

        The application uses:

        - Snowflake Streamlit
        - Cortex Analyst
        - A governed sales semantic model
        - Snowflake SQL execution
        - Snowflake-based audit logging
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
        **Read-only SQL**

        Generated SQL is validated before execution. Only SELECT/WITH
        statements are permitted.

        **Result protection**

        Query results are limited to the configured maximum result size.

        **Auditability**

        User questions, generated SQL, execution status, timing and
        request identifiers can be recorded.

        **Conversation**

        Follow-up questions use the previous Cortex Analyst conversation
        context.

        **Business filters**

        Application filters are passed to Cortex Analyst as business
        context rather than constructing physical SQL in the application.

        **Technical transparency**

        SQL, request IDs and execution information are available under
        Technical Details rather than being shown by default to business
        users.
        """
    )

    st.markdown(
        "### Application Information"
    )

    info_col1, info_col2, info_col3 = st.columns(3)

    with info_col1:

        st.metric(
            "Application",
            APPLICATION_NAME
        )

    with info_col2:

        st.metric(
            "Semantic Model",
            SEMANTIC_MODEL_NAME
        )

    with info_col3:

        st.metric(
            "Max Result Rows",
            f"{MAX_RESULT_ROWS:,}"
        )


# =============================================================================
# 24. PROCESS A PENDING FOLLOW-UP AFTER UI RENDERING
# =============================================================================
#
# This block handles questions selected from quick-question or suggestion
# buttons. The button sets:
#
#     st.session_state.pending_question
#
# and calls st.rerun().
#
# The question is then processed here on the next run.
#
# =============================================================================

# NOTE:
# The main Sales AI tab already processes pending questions above.
# This section intentionally remains empty to avoid processing the same
# question twice.
#
# All question processing is handled inside tab_ai.
#
# =============================================================================