import streamlit as st
import pandas as pd
import json
import time
import re
import html

import _snowflake
from snowflake.snowpark.context import get_active_session


# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================

APPLICATION_NAME = "Sales AI"

SEMANTIC_VIEW = "SALES_DATA.PUBLIC.SALES_SEMANTIC_MODEL"

SEMANTIC_MODEL_NAME = "SALES_SEMANTIC_MODEL"

ANALYST_ENDPOINT = "/api/v2/cortex/analyst/message"

MAX_RESULT_ROWS = 10000

QUERY_HISTORY_LIMIT = 100

AUDIT_TABLE = "SALES_DATA.PUBLIC.ANALYST_QUERY_AUDIT_LOG"

FEEDBACK_TABLE = "SALES_DATA.PUBLIC.ANALYST_QUERY_FEEDBACK"

LEGACY_LOG_TABLE = "SALES_DATA.PUBLIC.ANALYST_QUERY_LOG"


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Sales AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 34px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .sub-title {
        font-size: 16px;
        color: #666666;
        margin-bottom: 25px;
    }

    .answer-box {
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #dddddd;
        margin-top: 10px;
        margin-bottom: 20px;
    }

    .info-card {
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #dddddd;
        min-height: 120px;
    }

    .info-title {
        font-size: 14px;
        color: #666666;
        margin-bottom: 8px;
    }

    .info-value {
        font-size: 25px;
        font-weight: 700;
    }

    .filter-summary {
        padding: 10px 14px;
        border-radius: 8px;
        border: 1px solid #dddddd;
        margin-bottom: 15px;
        font-size: 13px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =============================================================================
# SESSION
# =============================================================================

session = get_active_session()


# =============================================================================
# SESSION STATE INITIALIZATION
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
    st.session_state.last_question = ""

if "last_analyst_question" not in st.session_state:
    st.session_state.last_analyst_question = ""

if "last_sql" not in st.session_state:
    st.session_state.last_sql = ""

if "last_response" not in st.session_state:
    st.session_state.last_response = ""

if "last_dataframe" not in st.session_state:
    st.session_state.last_dataframe = None

if "last_status" not in st.session_state:
    st.session_state.last_status = ""

if "last_error" not in st.session_state:
    st.session_state.last_error = ""

if "question_input" not in st.session_state:
    st.session_state.question_input = ""


# =============================================================================
# HELPER - CURRENT USER
# =============================================================================

@st.cache_data(ttl=300)
def get_current_user():
    try:
        result = session.sql(
            "SELECT CURRENT_USER() AS USER_NAME"
        ).collect()

        if result:
            return result[0]["USER_NAME"]

    except Exception:
        pass

    return "UNKNOWN_USER"


CURRENT_USER = get_current_user()


# =============================================================================
# DATE RANGE HELPER
# =============================================================================

def get_date_range(date_filter):
    """
    Returns a human-readable date filter description.
    The actual filtering is passed to Cortex Analyst as business context.
    """

    today = pd.Timestamp.today().normalize()

    if date_filter == "Today":
        return (
            f"{today.strftime('%Y-%m-%d')} to "
            f"{today.strftime('%Y-%m-%d')}"
        )

    if date_filter == "Yesterday":
        yesterday = today - pd.Timedelta(days=1)

        return (
            f"{yesterday.strftime('%Y-%m-%d')} to "
            f"{yesterday.strftime('%Y-%m-%d')}"
        )

    if date_filter == "Last 7 Days":
        start = today - pd.Timedelta(days=6)

        return (
            f"{start.strftime('%Y-%m-%d')} to "
            f"{today.strftime('%Y-%m-%d')}"
        )

    if date_filter == "Last 30 Days":
        start = today - pd.Timedelta(days=29)

        return (
            f"{start.strftime('%Y-%m-%d')} to "
            f"{today.strftime('%Y-%m-%d')}"
        )

    if date_filter == "Last 90 Days":
        start = today - pd.Timedelta(days=89)

        return (
            f"{start.strftime('%Y-%m-%d')} to "
            f"{today.strftime('%Y-%m-%d')}"
        )

    if date_filter == "Month to Date":
        start = today.replace(day=1)

        return (
            f"{start.strftime('%Y-%m-%d')} to "
            f"{today.strftime('%Y-%m-%d')}"
        )

    if date_filter == "Quarter to Date":

        quarter_month = ((today.month - 1) // 3) * 3 + 1

        start = today.replace(
            month=quarter_month,
            day=1
        )

        return (
            f"{start.strftime('%Y-%m-%d')} to "
            f"{today.strftime('%Y-%m-%d')}"
        )

    if date_filter == "Year to Date":

        start = today.replace(
            month=1,
            day=1
        )

        return (
            f"{start.strftime('%Y-%m-%d')} to "
            f"{today.strftime('%Y-%m-%d')}"
        )

    if date_filter == "Last Month":

        first_this_month = today.replace(day=1)

        last_month_end = first_this_month - pd.Timedelta(days=1)

        last_month_start = last_month_end.replace(day=1)

        return (
            f"{last_month_start.strftime('%Y-%m-%d')} to "
            f"{last_month_end.strftime('%Y-%m-%d')}"
        )

    if date_filter == "Last Quarter":

        current_quarter = (today.month - 1) // 3

        if current_quarter == 0:

            year = today.year - 1
            start_month = 10

        else:

            year = today.year
            start_month = (current_quarter - 1) * 3 + 1

        start = pd.Timestamp(
            year=year,
            month=start_month,
            day=1
        )

        end = start + pd.offsets.QuarterEnd(1)

        return (
            f"{start.strftime('%Y-%m-%d')} to "
            f"{end.strftime('%Y-%m-%d')}"
        )

    if date_filter == "Last Year":

        start = pd.Timestamp(
            year=today.year - 1,
            month=1,
            day=1
        )

        end = pd.Timestamp(
            year=today.year - 1,
            month=12,
            day=31
        )

        return (
            f"{start.strftime('%Y-%m-%d')} to "
            f"{end.strftime('%Y-%m-%d')}"
        )

    return "No date filter"


# =============================================================================
# BUSINESS CONTEXT
# =============================================================================

def build_business_context():

    role = st.session_state.get(
        "business_role",
        "Sales Executive"
    )

    answer_style = st.session_state.get(
        "answer_style",
        "Executive summary"
    )

    date_filter = st.session_state.get(
        "date_filter",
        "Last 30 Days"
    )

    comparison = st.session_state.get(
        "comparison",
        "No comparison"
    )

    region = st.session_state.get(
        "filter_region",
        ""
    )

    territory = st.session_state.get(
        "filter_territory",
        ""
    )

    sales_rep = st.session_state.get(
        "filter_sales_rep",
        ""
    )

    customer = st.session_state.get(
        "filter_customer",
        ""
    )

    industry = st.session_state.get(
        "filter_industry",
        ""
    )

    product = st.session_state.get(
        "filter_product",
        ""
    )

    product_category = st.session_state.get(
        "filter_product_category",
        ""
    )

    channel = st.session_state.get(
        "filter_channel",
        ""
    )

    context = []

    context.append(
        f"Business role: {role}"
    )

    context.append(
        f"Preferred answer style: {answer_style}"
    )

    context.append(
        f"Date filter: {date_filter}"
    )

    context.append(
        f"Date range: {get_date_range(date_filter)}"
    )

    context.append(
        f"Comparison requested: {comparison}"
    )

    if region:
        context.append(
            f"Region filter: {region}"
        )

    if territory:
        context.append(
            f"Territory filter: {territory}"
        )

    if sales_rep:
        context.append(
            f"Sales Rep filter: {sales_rep}"
        )

    if customer:
        context.append(
            f"Customer filter: {customer}"
        )

    if industry:
        context.append(
            f"Industry filter: {industry}"
        )

    if product:
        context.append(
            f"Product filter: {product}"
        )

    if product_category:
        context.append(
            f"Product Category filter: {product_category}"
        )

    if channel:
        context.append(
            f"Channel filter: {channel}"
        )

    return "\n".join(context)


# =============================================================================
# BUILD CORTEX ANALYST QUESTION
# =============================================================================

def build_analyst_question(question):

    business_context = build_business_context()

    analyst_question = f"""
You are Sales AI, an enterprise sales analytics assistant.

Answer the user's business question using the semantic view:

{SEMANTIC_VIEW}

Business context:
{business_context}

User question:
{question}

Instructions:

1. Use the semantic model as the source of truth.
2. Answer using the available business metrics and dimensions.
3. Do not invent columns, metrics, customers, products, sales representatives,
   regions, or other business data.
4. If the question asks for rankings such as top 10, return the requested
   number of records.
5. Prefer revenue, sales, quantity, margin, customer, product, sales rep,
   region, territory, and channel metrics when they are available in the
   semantic model.
6. Apply the date filter when the question does not explicitly specify
   another date range.
7. Apply the selected business filters when relevant.
8. If a comparison is requested, clearly explain the comparison.
9. Provide a concise business explanation along with the SQL when appropriate.
10. Generate read-only SQL only.
11. Do not generate INSERT, UPDATE, DELETE, MERGE, CREATE, ALTER, DROP,
    TRUNCATE, CALL, GRANT, REVOKE, USE, or other administrative statements.
12. Never expose credentials, secrets, tokens, or system information.
13. Format the answer for business users.
14. If the requested information is unavailable from the semantic model,
    clearly state that instead of guessing.
"""

    return analyst_question.strip()


# =============================================================================
# CORTEX ANALYST API CALL
# =============================================================================

def ask_cortex_analyst(question):
    """
    Sends a request to Cortex Analyst.

    IMPORTANT:
    Snowflake's _snowflake.send_snow_api_request() in some Streamlit
    runtimes does not accept keyword arguments.

    Therefore positional arguments are intentionally used.
    """

    analyst_question = build_analyst_question(question)

    # -------------------------------------------------------------------------
    # Preserve previous Analyst messages for multi-turn conversations.
    # -------------------------------------------------------------------------

    messages = list(
        st.session_state.get(
            "analyst_messages",
            []
        )
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

    request_json = json.dumps(
        request_body
    )

    try:

        # ---------------------------------------------------------------------
        # IMPORTANT:
        # Positional arguments.
        # ---------------------------------------------------------------------

        response = _snowflake.send_snow_api_request(
            "POST",
            ANALYST_ENDPOINT,
            {},
            {},
            request_json
        )

    except Exception as e:

        raise RuntimeError(
            f"Cortex Analyst request failed: {str(e)}"
        )

    # -------------------------------------------------------------------------
    # Determine HTTP status.
    # -------------------------------------------------------------------------

    status_code = None

    try:

        if hasattr(response, "status"):
            status_code = response.status

        elif hasattr(response, "status_code"):
            status_code = response.status_code

        elif isinstance(response, dict):

            status_code = (
                response.get("status")
                or response.get("status_code")
                or response.get("http_status")
            )

    except Exception:
        status_code = None

    # -------------------------------------------------------------------------
    # Retrieve response body.
    # -------------------------------------------------------------------------

    raw_content = None

    try:

        if hasattr(response, "content"):
            raw_content = response.content

        elif hasattr(response, "body"):
            raw_content = response.body

        elif isinstance(response, dict):

            raw_content = (
                response.get("content")
                or response.get("body")
                or response.get("response")
            )

    except Exception:
        raw_content = None

    # -------------------------------------------------------------------------
    # Convert bytes to string if necessary.
    # -------------------------------------------------------------------------

    if isinstance(raw_content, bytes):

        try:
            raw_content = raw_content.decode(
                "utf-8"
            )

        except Exception:
            raw_content = str(
                raw_content
            )

    # -------------------------------------------------------------------------
    # Sometimes Snowflake response objects expose JSON through json().
    # -------------------------------------------------------------------------

    parsed_response = None

    try:

        if hasattr(response, "json"):

            parsed_response = response.json()

    except Exception:

        parsed_response = None

    # -------------------------------------------------------------------------
    # If json() did not work, parse content.
    # -------------------------------------------------------------------------

    if parsed_response is None:

        if isinstance(raw_content, dict):

            parsed_response = raw_content

        elif isinstance(raw_content, str):

            try:

                parsed_response = json.loads(
                    raw_content
                )

            except Exception:

                parsed_response = None

    # -------------------------------------------------------------------------
    # Handle HTTP errors.
    # -------------------------------------------------------------------------

    if status_code is not None:

        try:

            numeric_status = int(
                status_code
            )

        except Exception:

            numeric_status = None

        if (
            numeric_status is not None
            and numeric_status >= 400
        ):

            error_detail = raw_content

            if isinstance(
                parsed_response,
                dict
            ):

                error_detail = (
                    parsed_response.get("message")
                    or parsed_response.get("error")
                    or parsed_response.get("detail")
                    or parsed_response
                )

            raise RuntimeError(
                f"Cortex Analyst request failed "
                f"(HTTP {numeric_status}): "
                f"{error_detail}"
            )

    # -------------------------------------------------------------------------
    # Validate parsed response.
    # -------------------------------------------------------------------------

    if not isinstance(
        parsed_response,
        dict
    ):

        raise RuntimeError(
            "Invalid Cortex Analyst response.\n\n"
            f"HTTP status: {status_code}\n\n"
            f"Response type: {type(response).__name__}\n\n"
            f"Raw response:\n{raw_content}"
        )

    # -------------------------------------------------------------------------
    # Store the complete assistant response in the conversation.
    #
    # Cortex Analyst expects structured assistant content for future turns.
    # -------------------------------------------------------------------------

    message_object = parsed_response.get(
        "message",
        {}
    )

    if isinstance(
        message_object,
        dict
    ):

        assistant_content = message_object.get(
            "content",
            []
        )

    else:

        assistant_content = []

    if not isinstance(
        assistant_content,
        list
    ):

        assistant_content = []

    messages.append(
        {
            "role": "assistant",
            "content": assistant_content
        }
    )

    st.session_state.analyst_messages = messages

    return (
        parsed_response,
        analyst_question
    )


# =============================================================================
# PARSE CORTEX ANALYST RESPONSE
# =============================================================================

def parse_analyst_response(response):

    if not isinstance(
        response,
        dict
    ):

        return {
            "text": "",
            "sql": "",
            "suggestions": [],
            "request_id": None
        }

    # -------------------------------------------------------------------------
    # Request ID
    # -------------------------------------------------------------------------

    request_id = (
        response.get("request_id")
        or response.get("requestId")
        or response.get("id")
    )

    # -------------------------------------------------------------------------
    # Message
    # -------------------------------------------------------------------------

    message = response.get(
        "message",
        {}
    )

    if not isinstance(
        message,
        dict
    ):

        message = {}

    content = message.get(
        "content",
        []
    )

    if not isinstance(
        content,
        list
    ):

        content = []

    text_parts = []

    sql_parts = []

    suggestions = []

    # -------------------------------------------------------------------------
    # Parse content blocks.
    # -------------------------------------------------------------------------

    for item in content:

        if not isinstance(
            item,
            dict
        ):
            continue

        item_type = item.get(
            "type"
        )

        # ---------------------------------------------------------------------
        # Text
        # ---------------------------------------------------------------------

        if item_type == "text":

            text_value = item.get(
                "text",
                ""
            )

            if text_value:

                text_parts.append(
                    str(text_value)
                )

        # ---------------------------------------------------------------------
        # SQL
        # ---------------------------------------------------------------------

        elif item_type == "sql":

            sql_value = (
                item.get("statement")
                or item.get("sql")
                or item.get("query")
                or ""
            )

            if sql_value:

                sql_parts.append(
                    str(sql_value)
                )

        # ---------------------------------------------------------------------
        # Suggestions
        # ---------------------------------------------------------------------

        elif item_type == "suggestions":

            suggestion_values = item.get(
                "suggestions",
                []
            )

            if isinstance(
                suggestion_values,
                list
            ):

                for suggestion in suggestion_values:

                    if suggestion:

                        suggestions.append(
                            str(suggestion)
                        )

        # ---------------------------------------------------------------------
        # Generic fallback.
        # ---------------------------------------------------------------------

        else:

            if "statement" in item:

                statement = item.get(
                    "statement"
                )

                if statement:

                    sql_parts.append(
                        str(statement)
                    )

            if "text" in item:

                text_value = item.get(
                    "text"
                )

                if text_value:

                    text_parts.append(
                        str(text_value)
                    )

    # -------------------------------------------------------------------------
    # Additional fallback for SQL.
    # -------------------------------------------------------------------------

    if not sql_parts:

        for item in content:

            if not isinstance(
                item,
                dict
            ):
                continue

            statement = item.get(
                "statement"
            )

            if statement:

                sql_parts.append(
                    str(statement)
                )

    return {
        "text": "\n\n".join(
            text_parts
        ).strip(),

        "sql": "\n\n".join(
            sql_parts
        ).strip(),

        "suggestions": suggestions,

        "request_id": request_id
    }


# =============================================================================
# SQL SAFETY VALIDATION
# =============================================================================

def strip_sql_comments_and_literals(sql):

    if not sql:
        return ""

    # Remove single-line comments.
    sql = re.sub(
        r"--[^\n]*",
        "",
        sql
    )

    # Remove block comments.
    sql = re.sub(
        r"/\*.*?\*/",
        "",
        sql,
        flags=re.DOTALL
    )

    # Replace string literals with placeholders.
    sql = re.sub(
        r"'(?:''|[^'])*'",
        "''",
        sql
    )

    return sql


def validate_generated_sql(sql):

    if not sql:
        return False, "No SQL was generated."

    cleaned_sql = strip_sql_comments_and_literals(
        sql
    ).strip()

    # -------------------------------------------------------------------------
    # Remove trailing semicolon.
    # -------------------------------------------------------------------------

    cleaned_sql = cleaned_sql.rstrip(";").strip()

    if ";" in cleaned_sql:

        return (
            False,
            "Multiple SQL statements are not allowed."
        )

    # -------------------------------------------------------------------------
    # Must start with SELECT or WITH.
    # -------------------------------------------------------------------------

    if not re.match(
        r"^(SELECT|WITH)\b",
        cleaned_sql,
        flags=re.IGNORECASE
    ):

        return (
            False,
            "Only SELECT/WITH queries are allowed."
        )

    # -------------------------------------------------------------------------
    # Block dangerous SQL operations.
    # -------------------------------------------------------------------------

    blocked_patterns = [
        r"\bINSERT\b",
        r"\bUPDATE\b",
        r"\bDELETE\b",
        r"\bMERGE\b",
        r"\bCREATE\b",
        r"\bALTER\b",
        r"\bDROP\b",
        r"\bTRUNCATE\b",
        r"\bCALL\b",
        r"\bGRANT\b",
        r"\bREVOKE\b",
        r"\bUSE\b",
        r"\bPUT\b",
        r"\bGET\b",
        r"\bCOPY\b",
        r"\bREMOVE\b",
        r"\bEXECUTE\b",
        r"\bEXEC\b",
        r"\bSYSTEM\$",
        r"\bALTER\s+SESSION\b",
        r"\bALTER\s+USER\b",
        r"\bALTER\s+ROLE\b",
    ]

    for pattern in blocked_patterns:

        if re.search(
            pattern,
            cleaned_sql,
            flags=re.IGNORECASE
        ):

            return (
                False,
                f"Potentially unsafe SQL detected: {pattern}"
            )

    return True, ""


# =============================================================================
# EXECUTE GENERATED SQL
# =============================================================================

def execute_generated_sql(sql):

    valid, error_message = validate_generated_sql(
        sql
    )

    if not valid:

        raise RuntimeError(
            error_message
        )

    cleaned_sql = sql.strip()

    # -------------------------------------------------------------------------
    # Remove trailing semicolon.
    # -------------------------------------------------------------------------

    cleaned_sql = cleaned_sql.rstrip(";").strip()

    # -------------------------------------------------------------------------
    # Limit result size.
    # -------------------------------------------------------------------------

    protected_sql = f"""
SELECT *
FROM (
    {cleaned_sql}
) AS ANALYST_RESULT
LIMIT {MAX_RESULT_ROWS}
"""

    result = session.sql(
        protected_sql
    )

    dataframe = result.to_pandas()

    return dataframe


# =============================================================================
# LOG QUERY
# =============================================================================

def log_query(
    user_question,
    analyst_question,
    response,
    generated_sql,
    execution_status,
    analyst_seconds,
    execution_seconds,
    rows_returned,
    error_message,
    request_id
):

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
        SELECT
            UUID_STRING(),
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
        """

        session.sql(
            insert_sql,
            params=[
                CURRENT_USER,
                request_id,
                user_question,
                analyst_question,
                response,
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

        return

    except Exception:
        pass

    # -------------------------------------------------------------------------
    # Legacy table fallback.
    # -------------------------------------------------------------------------

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
        SELECT
            CURRENT_TIMESTAMP(),
            ?,
            ?,
            ?,
            ?
        """

        session.sql(
            legacy_sql,
            params=[
                CURRENT_USER,
                user_question,
                response,
                SEMANTIC_MODEL_NAME
            ]
        ).collect()

    except Exception:
        pass


# =============================================================================
# LOG FEEDBACK
# =============================================================================

def log_feedback(
    query_id,
    feedback
):

    if not query_id:
        return

    try:

        sql = f"""
        INSERT INTO {FEEDBACK_TABLE}
        (
            QUERY_ID,
            FEEDBACK_TIMESTAMP,
            USER_NAME,
            FEEDBACK
        )
        SELECT
            ?,
            CURRENT_TIMESTAMP(),
            ?,
            ?
        """

        session.sql(
            sql,
            params=[
                query_id,
                CURRENT_USER,
                feedback
            ]
        ).collect()

    except Exception:
        pass


# =============================================================================
# GET QUERY HISTORY
# =============================================================================

def get_query_history():

    try:

        sql = f"""
        SELECT
            QUERY_ID,
            QUERY_TIMESTAMP,
            USER_NAME,
            USER_QUESTION,
            RESPONSE,
            GENERATED_SQL,
            EXECUTION_STATUS,
            ANALYST_SECONDS,
            EXECUTION_SECONDS,
            ROWS_RETURNED,
            ERROR_MESSAGE,
            REQUEST_ID
        FROM {AUDIT_TABLE}
        WHERE USER_NAME = ?
        ORDER BY QUERY_TIMESTAMP DESC
        LIMIT {QUERY_HISTORY_LIMIT}
        """

        dataframe = session.sql(
            sql,
            params=[CURRENT_USER]
        ).to_pandas()

        return dataframe

    except Exception:
        pass

    # -------------------------------------------------------------------------
    # Legacy fallback.
    # -------------------------------------------------------------------------

    try:

        sql = f"""
        SELECT
            QUERY_TIMESTAMP,
            USER_NAME,
            USER_QUESTION,
            RESPONSE,
            SEMANTIC_MODEL_NAME
        FROM {LEGACY_LOG_TABLE}
        WHERE USER_NAME = ?
        ORDER BY QUERY_TIMESTAMP DESC
        LIMIT {QUERY_HISTORY_LIMIT}
        """

        dataframe = session.sql(
            sql,
            params=[CURRENT_USER]
        ).to_pandas()

        return dataframe

    except Exception:

        return pd.DataFrame()


# =============================================================================
# PROCESS QUESTION
# =============================================================================

def process_question(question):

    question = (
        question or ""
    ).strip()

    if not question:

        st.warning(
            "Please enter a business question."
        )

        return

    start_time = time.time()

    try:

        # =====================================================================
        # CALL CORTEX ANALYST
        # =====================================================================

        analyst_response, analyst_question = (
            ask_cortex_analyst(
                question
            )
        )

        analyst_seconds = (
            time.time() - start_time
        )

        # =====================================================================
        # PARSE RESPONSE
        # =====================================================================

        parsed = parse_analyst_response(
            analyst_response
        )

        response_text = parsed[
            "text"
        ]

        generated_sql = parsed[
            "sql"
        ]

        suggestions = parsed[
            "suggestions"
        ]

        request_id = parsed[
            "request_id"
        ]

        st.session_state.last_request_id = (
            request_id
        )

        st.session_state.last_question = (
            question
        )

        st.session_state.last_analyst_question = (
            analyst_question
        )

        st.session_state.last_sql = (
            generated_sql
        )

        st.session_state.last_response = (
            response_text
        )

        # =====================================================================
        # EXECUTE SQL
        # =====================================================================

        dataframe = None

        execution_seconds = 0

        execution_status = "NO_SQL"

        error_message = None

        if generated_sql:

            sql_start = time.time()

            try:

                dataframe = execute_generated_sql(
                    generated_sql
                )

                execution_seconds = (
                    time.time() - sql_start
                )

                execution_status = "SUCCESS"

                st.session_state.last_dataframe = (
                    dataframe
                )

            except Exception as e:

                execution_seconds = (
                    time.time() - sql_start
                )

                execution_status = "FAILED"

                error_message = str(e)

                st.session_state.last_dataframe = (
                    None
                )

        else:

            st.session_state.last_dataframe = None

        # =====================================================================
        # SAVE STATUS
        # =====================================================================

        if execution_status == "FAILED":

            st.session_state.last_status = (
                "FAILED"
            )

        elif generated_sql:

            st.session_state.last_status = (
                "SUCCESS"
            )

        else:

            st.session_state.last_status = (
                "ANSWER_ONLY"
            )

        st.session_state.last_error = (
            error_message or ""
        )

        # =====================================================================
        # SAVE CONVERSATION DISPLAY DATA
        # =====================================================================

        st.session_state.conversation_history.append(
            {
                "question": question,
                "response": response_text,
                "sql": generated_sql,
                "dataframe": dataframe,
                "status": execution_status,
                "request_id": request_id,
                "suggestions": suggestions
            }
        )

        # =====================================================================
        # LOG QUERY
        # =====================================================================

        log_query(
            user_question=question,
            analyst_question=analyst_question,
            response=response_text,
            generated_sql=generated_sql,
            execution_status=execution_status,
            analyst_seconds=analyst_seconds,
            execution_seconds=execution_seconds,
            rows_returned=(
                len(dataframe)
                if dataframe is not None
                else 0
            ),
            error_message=error_message,
            request_id=request_id
        )

        # =====================================================================
        # DISPLAY ANSWER
        # =====================================================================

        st.markdown(
            "### Sales AI"
        )

        if response_text:

            st.markdown(
                response_text
            )

        else:

            st.info(
                "Cortex Analyst returned no text explanation."
            )

        # =====================================================================
        # DISPLAY RESULTS
        # =====================================================================

        if dataframe is not None:

            st.markdown(
                "### Results"
            )

            st.dataframe(
                dataframe,
                use_container_width=True
            )

            st.caption(
                f"{len(dataframe):,} rows returned"
            )

            # -----------------------------------------------------------------
            # CSV DOWNLOAD
            # -----------------------------------------------------------------

            try:

                csv_data = dataframe.to_csv(
                    index=False
                )

                st.download_button(
                    label="Download Results as CSV",
                    data=csv_data,
                    file_name="sales_ai_results.csv",
                    mime="text/csv"
                )

            except Exception:
                pass

        # =====================================================================
        # SQL
        # =====================================================================

        if generated_sql:

            with st.expander(
                "View generated SQL"
            ):

                st.code(
                    generated_sql,
                    language="sql"
                )

        # =====================================================================
        # REQUEST ID
        # =====================================================================

        if request_id:

            st.caption(
                f"Request ID: {request_id}"
            )

        # =====================================================================
        # SUGGESTIONS
        # =====================================================================

        if suggestions:

            st.markdown(
                "### Suggested follow-ups"
            )

            for suggestion in suggestions[:5]:

                if st.button(
                    suggestion
                ):

                    st.session_state.question_input = (
                        suggestion
                    )

        # =====================================================================
        # SQL EXECUTION ERROR
        # =====================================================================

        if execution_status == "FAILED":

            st.error(
                "Cortex Analyst understood the question, "
                "but the generated SQL could not be executed."
            )

            with st.expander(
                "Technical Details"
            ):

                st.code(
                    error_message or "Unknown SQL error."
                )

    except Exception as e:

        st.session_state.last_status = (
            "FAILED"
        )

        st.session_state.last_error = (
            str(e)
        )

        st.error(
            "Sales AI could not process your question."
        )

        with st.expander(
            "Technical Details"
        ):

            st.code(
                str(e)
            )


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:

    st.markdown(
        "## Sales AI"
    )

    st.caption(
        f"Signed in as: {CURRENT_USER}"
    )

    st.divider()

    # =========================================================================
    # BUSINESS ROLE
    # =========================================================================

    st.selectbox(
        "Business Role",
        [
            "Sales Executive",
            "Sales Manager",
            "Sales Analyst",
            "Business User",
            "Data / AI Developer"
        ],
        key="business_role"
    )

    # =========================================================================
    # ANSWER STYLE
    # =========================================================================

    st.selectbox(
        "Answer Style",
        [
            "Executive summary",
            "Detailed analysis",
            "Data focused",
            "Technical"
        ],
        key="answer_style"
    )

    st.divider()

    # =========================================================================
    # DATE FILTER
    # =========================================================================

    st.markdown(
        "### Date Filter"
    )

    st.selectbox(
        "Period",
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
            "Last Year"
        ],
        key="date_filter"
    )

    # =========================================================================
    # COMPARISON
    # =========================================================================

    st.selectbox(
        "Comparison",
        [
            "No comparison",
            "Previous period",
            "Previous year",
            "Year over year",
            "Month over month"
        ],
        key="comparison"
    )

    st.divider()

    # =========================================================================
    # BUSINESS FILTERS
    # =========================================================================

    st.markdown(
        "### Business Filters"
    )

    st.text_input(
        "Region",
        key="filter_region"
    )

    st.text_input(
        "Territory",
        key="filter_territory"
    )

    st.text_input(
        "Sales Rep",
        key="filter_sales_rep"
    )

    st.text_input(
        "Customer",
        key="filter_customer"
    )

    st.text_input(
        "Industry",
        key="filter_industry"
    )

    st.text_input(
        "Product",
        key="filter_product"
    )

    st.text_input(
        "Product Category",
        key="filter_product_category"
    )

    st.text_input(
        "Channel",
        key="filter_channel"
    )

    st.divider()

    # =========================================================================
    # NEW CONVERSATION
    # =========================================================================

    if st.button(
        "Start New Conversation",
        use_container_width=True
    ):

        st.session_state.analyst_messages = []

        st.session_state.conversation_history = []

        st.session_state.last_question = ""

        st.session_state.last_analyst_question = ""

        st.session_state.last_sql = ""

        st.session_state.last_response = ""

        st.session_state.last_dataframe = None

        st.session_state.last_request_id = None

        st.session_state.last_status = ""

        st.session_state.last_error = ""

        st.session_state.question_input = ""

        st.success(
            "New conversation started."
        )


# =============================================================================
# APPLICATION HEADER
# =============================================================================

st.markdown(
    '<div class="main-title">Sales AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    'Ask business questions using natural language and get '
    'trusted answers from your Snowflake sales data.'
    '</div>',
    unsafe_allow_html=True
)


# =============================================================================
# TABS
# =============================================================================

tab_overview, tab_ai, tab_history, tab_questions, tab_about = st.tabs(
    [
        "Executive Overview",
        "Sales AI",
        "Query History",
        "Sample Questions",
        "About"
    ]
)


# =============================================================================
# EXECUTIVE OVERVIEW
# =============================================================================

with tab_overview:

    st.markdown(
        "## Executive Overview"
    )

    st.caption(
        "Use Sales AI to analyze revenue, sales performance, "
        "customers, products, representatives and business trends."
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">AI Analytics</div>
                <div class="info-value">Natural Language</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">Data Source</div>
                <div class="info-value">Snowflake</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:

        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">Semantic Layer</div>
                <div class="info-value">Cortex Analyst</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:

        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">Access</div>
                <div class="info-value">Read Only</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        ""
    )

    st.markdown(
        "### Recommended Analyses"
    )

    overview_col1, overview_col2 = st.columns(2)

    with overview_col1:

        st.markdown(
            """
            **Sales Performance**
            
            - Revenue by sales representative
            - Revenue by region
            - Revenue by territory
            - Monthly sales trends
            - Top and bottom performers
            """
        )

    with overview_col2:

        st.markdown(
            """
            **Customer & Product Intelligence**
            
            - Top customers by revenue
            - Product performance
            - Product category trends
            - Channel performance
            - Customer concentration
            """
        )

    st.markdown(
        "### Current Filters"
    )

    date_filter = st.session_state.get(
        "date_filter",
        "Last 30 Days"
    )

    comparison = st.session_state.get(
        "comparison",
        "No comparison"
    )

    st.write(
        f"**Period:** {date_filter}"
    )

    st.write(
        f"**Date range:** {get_date_range(date_filter)}"
    )

    st.write(
        f"**Comparison:** {comparison}"
    )


# =============================================================================
# SALES AI TAB
# =============================================================================

with tab_ai:

    st.markdown(
        "## Ask a Business Question"
    )

    st.caption(
        "Examples: "
        "Show the top 10 sales reps by revenue. "
        "Compare this month's revenue with last month. "
        "Which customers generated the most revenue?"
    )

    # -------------------------------------------------------------------------
    # Current filters summary
    # -------------------------------------------------------------------------

    active_filters = []

    date_filter = st.session_state.get(
        "date_filter",
        "Last 30 Days"
    )

    active_filters.append(
        f"Period: {date_filter}"
    )

    comparison = st.session_state.get(
        "comparison",
        "No comparison"
    )

    if comparison != "No comparison":

        active_filters.append(
            f"Comparison: {comparison}"
        )

    filter_mapping = [
        ("Region", "filter_region"),
        ("Territory", "filter_territory"),
        ("Sales Rep", "filter_sales_rep"),
        ("Customer", "filter_customer"),
        ("Industry", "filter_industry"),
        ("Product", "filter_product"),
        ("Product Category", "filter_product_category"),
        ("Channel", "filter_channel")
    ]

    for label, key in filter_mapping:

        value = st.session_state.get(
            key,
            ""
        )

        if value:

            active_filters.append(
                f"{label}: {value}"
            )

    safe_filter_summary = html.escape(
        " | ".join(active_filters)
    )

    st.markdown(
        f"""
        <div class="filter-summary">
            <strong>Active context:</strong>
            {safe_filter_summary}
        </div>
        """,
        unsafe_allow_html=True
    )

    # -------------------------------------------------------------------------
    # Question input
    # -------------------------------------------------------------------------

    st.text_area(
        "Business Question",
        key="question_input",
        height=110,
        placeholder=(
            "Example: Show the top 10 sales reps by revenue."
        )
    )

    ask_col, clear_col = st.columns(
        [3, 1]
    )

    with ask_col:

        ask_clicked = st.button(
            "Ask Sales AI",
            use_container_width=True
        )

    with clear_col:

        clear_clicked = st.button(
            "Clear",
            use_container_width=True
        )

    if clear_clicked:

        st.session_state.question_input = ""

        st.info(
            "Question cleared. Enter a new question."
        )

    if ask_clicked:

        process_question(
            st.session_state.question_input
        )

    # -------------------------------------------------------------------------
    # Display last successful result on normal reruns.
    # -------------------------------------------------------------------------

    if (
        not ask_clicked
        and st.session_state.last_question
        and st.session_state.last_status
    ):

        st.markdown(
            "---"
        )

        st.markdown(
            "### Last Question"
        )

        st.write(
            st.session_state.last_question
        )

        if st.session_state.last_response:

            st.markdown(
                "### Sales AI"
            )

            st.markdown(
                st.session_state.last_response
            )

        if (
            st.session_state.last_dataframe
            is not None
        ):

            st.markdown(
                "### Results"
            )

            st.dataframe(
                st.session_state.last_dataframe,
                use_container_width=True
            )

            try:

                csv_data = (
                    st.session_state
                    .last_dataframe
                    .to_csv(index=False)
                )

                st.download_button(
                    "Download Results as CSV",
                    csv_data,
                    "sales_ai_results.csv",
                    "text/csv"
                )

            except Exception:
                pass

        if st.session_state.last_sql:

            with st.expander(
                "View generated SQL"
            ):

                st.code(
                    st.session_state.last_sql,
                    language="sql"
                )

        if st.session_state.last_request_id:

            st.caption(
                "Request ID: "
                + str(
                    st.session_state.last_request_id
                )
            )

        # ---------------------------------------------------------------------
        # Feedback
        # ---------------------------------------------------------------------

        st.markdown(
            "### Was this answer useful?"
        )

        feedback_col1, feedback_col2 = st.columns(2)

        with feedback_col1:

            if st.button(
                "Helpful"
            ):

                log_feedback(
                    st.session_state.last_query_id,
                    "HELPFUL"
                )

                st.success(
                    "Thanks for the feedback."
                )

        with feedback_col2:

            if st.button(
                "Not Helpful"
            ):

                log_feedback(
                    st.session_state.last_query_id,
                    "NOT_HELPFUL"
                )

                st.success(
                    "Thanks for the feedback."
                )


# =============================================================================
# QUERY HISTORY TAB
# =============================================================================

with tab_history:

    st.markdown(
        "## Query History"
    )

    history = get_query_history()

    if history.empty:

        st.info(
            "No query history is available yet."
        )

    else:

        st.dataframe(
            history,
            use_container_width=True
        )

        st.caption(
            f"{len(history):,} historical queries displayed."
        )


# =============================================================================
# SAMPLE QUESTIONS TAB
# =============================================================================

with tab_questions:

    st.markdown(
        "## Sample Business Questions"
    )

    st.caption(
        "Use these questions as starting points for Sales AI."
    )

    sample_questions = [
        "Show the top 10 sales reps by revenue.",
        "Show the top 10 customers by revenue.",
        "What are our total sales?",
        "What is our revenue by region?",
        "Show revenue by territory.",
        "Which products generate the most revenue?",
        "Show monthly revenue for the last 12 months.",
        "Compare revenue this month with last month.",
        "Compare this year's revenue with last year.",
        "Which sales reps are underperforming?",
        "Which customers have declining revenue?",
        "What are our highest revenue product categories?",
        "Show sales performance by channel.",
        "Who are the top 5 sales representatives?",
        "Which region generates the most revenue?"
    ]

    for question in sample_questions:

        if st.button(
            question,
            use_container_width=True
        ):

            st.session_state.question_input = (
                question
            )

            st.info(
                "Question loaded into the Sales AI tab. "
                "Open the Sales AI tab and click "
                "'Ask Sales AI'."
            )


# =============================================================================
# ABOUT TAB
# =============================================================================

with tab_about:

    st.markdown(
        "## About Sales AI"
    )

    st.markdown(
        """
        **Sales AI** is a Snowflake-native business analytics application
        powered by Cortex Analyst.

        ### How it works

        1. A business user enters a natural-language question.
        2. Sales AI adds the selected business context and filters.
        3. Cortex Analyst interprets the question using the governed
           semantic model.
        4. Cortex Analyst generates read-only SQL.
        5. Sales AI validates the generated SQL.
        6. The SQL is executed inside Snowflake.
        7. Results are displayed in the application.
        8. The request and execution information can be captured in the
           audit log.

        ### Governance

        The application is designed around:

        - Snowflake-native execution
        - Cortex Analyst semantic modeling
        - Read-only SQL validation
        - Result-size protection
        - Query auditing
        - Request tracking
        - User feedback
        - Business filters
        - Multi-turn conversation context

        ### Semantic Model

        The current semantic model is:

        `SALES_DATA.PUBLIC.SALES_SEMANTIC_MODEL`

        ### Security

        Sales AI does not intentionally execute DML or administrative SQL
        generated by Cortex Analyst. Snowflake role-based access controls
        remain the primary security boundary.
        """
    )


# =============================================================================
# END OF APPLICATION
# =============================================================================