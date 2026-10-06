import streamlit as st
import pandas as pd
import json
import time
import re
import html

import _snowflake
from snowflake.snowpark.context import get_active_session


# ============================================================================
# CONFIGURATION
# ============================================================================

APPLICATION_NAME = "Sales AI"

SEMANTIC_VIEW = "SALES_DATA.PUBLIC.SALES_SEMANTIC_MODEL"

SEMANTIC_MODEL_NAME = "SALES_SEMANTIC_MODEL"

ANALYST_ENDPOINT = "/api/v2/cortex/analyst/message"

MAX_RESULT_ROWS = 10000

QUERY_HISTORY_LIMIT = 100

AUDIT_TABLE = "SALES_DATA.PUBLIC.ANALYST_QUERY_AUDIT_LOG"

FEEDBACK_TABLE = "SALES_DATA.PUBLIC.ANALYST_QUERY_FEEDBACK"

LEGACY_LOG_TABLE = "SALES_DATA.PUBLIC.ANALYST_QUERY_LOG"


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Sales AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .sub-title {
        font-size: 16px;
        color: #666666;
        margin-bottom: 20px;
    }

    .section-title {
        font-size: 22px;
        font-weight: 600;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    .success-box {
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #28a745;
        background-color: #f4fff6;
        margin-bottom: 15px;
    }

    .error-box {
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #dc3545;
        background-color: #fff5f5;
        margin-bottom: 15px;
    }

    .info-box {
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #999999;
        background-color: #f8f8f8;
        margin-bottom: 15px;
    }

    .metric-label {
        font-size: 13px;
        color: #666666;
    }

    .metric-value {
        font-size: 24px;
        font-weight: 700;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================================
# GET SNOWFLAKE SESSION
# ============================================================================

session = get_active_session()


# ============================================================================
# SESSION STATE
# ============================================================================

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

if "last_analyst_question" not in st.session_state:
    st.session_state.last_analyst_question = None

if "last_sql" not in st.session_state:
    st.session_state.last_sql = None

if "last_response" not in st.session_state:
    st.session_state.last_response = None

if "last_dataframe" not in st.session_state:
    st.session_state.last_dataframe = None

if "last_status" not in st.session_state:
    st.session_state.last_status = None

if "last_error" not in st.session_state:
    st.session_state.last_error = None

if "question_input" not in st.session_state:
    st.session_state.question_input = ""


# ============================================================================
# CURRENT USER
# ============================================================================

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

    return "UNKNOWN"


CURRENT_USER = get_current_user()


# ============================================================================
# DATE FILTER HELPER
# ============================================================================

def get_date_filter_description(date_filter):
    if date_filter == "Today":
        return "today"

    if date_filter == "Yesterday":
        return "yesterday"

    if date_filter == "Last 7 Days":
        return "the last 7 days"

    if date_filter == "Last 30 Days":
        return "the last 30 days"

    if date_filter == "Last 90 Days":
        return "the last 90 days"

    if date_filter == "Month to Date":
        return "month to date"

    if date_filter == "Quarter to Date":
        return "quarter to date"

    if date_filter == "Year to Date":
        return "year to date"

    if date_filter == "Last Month":
        return "last month"

    if date_filter == "Last Quarter":
        return "last quarter"

    if date_filter == "Last Year":
        return "last year"

    return "the available period"


# ============================================================================
# BUILD BUSINESS CONTEXT
# ============================================================================

def build_business_context():
    role = st.session_state.get(
        "business_role",
        "Sales Analyst"
    )

    answer_style = st.session_state.get(
        "answer_style",
        "Detailed analysis"
    )

    date_filter = st.session_state.get(
        "date_filter",
        "Last 30 Days"
    )

    comparison = st.session_state.get(
        "comparison",
        "No comparison"
    )

    region = st.session_state.get("region_filter", "")
    territory = st.session_state.get("territory_filter", "")
    sales_rep = st.session_state.get("sales_rep_filter", "")
    customer = st.session_state.get("customer_filter", "")
    industry = st.session_state.get("industry_filter", "")
    product = st.session_state.get("product_filter", "")
    product_category = st.session_state.get(
        "product_category_filter",
        ""
    )
    channel = st.session_state.get("channel_filter", "")

    context_lines = []

    context_lines.append(
        f"Business role: {role}"
    )

    context_lines.append(
        f"Preferred answer style: {answer_style}"
    )

    context_lines.append(
        f"Selected date filter: {date_filter} "
        f"({get_date_filter_description(date_filter)})"
    )

    context_lines.append(
        f"Comparison preference: {comparison}"
    )

    if region.strip():
        context_lines.append(
            f"Region filter: {region.strip()}"
        )

    if territory.strip():
        context_lines.append(
            f"Territory filter: {territory.strip()}"
        )

    if sales_rep.strip():
        context_lines.append(
            f"Sales representative filter: {sales_rep.strip()}"
        )

    if customer.strip():
        context_lines.append(
            f"Customer filter: {customer.strip()}"
        )

    if industry.strip():
        context_lines.append(
            f"Industry filter: {industry.strip()}"
        )

    if product.strip():
        context_lines.append(
            f"Product filter: {product.strip()}"
        )

    if product_category.strip():
        context_lines.append(
            f"Product category filter: {product_category.strip()}"
        )

    if channel.strip():
        context_lines.append(
            f"Channel filter: {channel.strip()}"
        )

    return "\n".join(context_lines)


# ============================================================================
# BUILD CORTEX ANALYST QUESTION
# ============================================================================

def build_analyst_question(question):
    business_context = build_business_context()

    analyst_question = f"""
You are a sales analytics assistant.

Use the semantic view:

{SEMANTIC_VIEW}

Answer the user's sales analytics question using the semantic view.

Important instructions:

1. Use only data and metrics available through the semantic view.
2. Generate valid Snowflake SQL.
3. Return a concise business-friendly explanation of the answer.
4. If the question requests rankings, use appropriate sorting and LIMIT.
5. If the user asks for trends, aggregate by the appropriate date grain.
6. Apply the selected date filter when it is relevant to the question.
7. Apply the selected business filters when they are relevant.
8. If a comparison is selected and relevant, compare the requested periods.
9. Do not invent columns, dimensions, measures, customers, products, sales representatives,
   regions, territories, or other values.
10. Prefer the semantic model's defined measures and dimensions.
11. For "top N" questions, return the requested number of records.
12. Keep the response focused on the user's question.

Business context:

{business_context}

User question:

{question}
"""

    return analyst_question.strip()


# ============================================================================
# ASK CORTEX ANALYST
# ============================================================================

def ask_cortex_analyst(question):
    """
    Send the current question to Cortex Analyst.

    IMPORTANT:
    The Snowflake Cortex Analyst endpoint used by this application
    does not accept role='assistant' in the messages array.

    Therefore, we intentionally send ONLY the current user message.

    This avoids errors such as:

    Unexpected value 'assistant'
    """

    analyst_question = build_analyst_question(question)

    # ------------------------------------------------------------------------
    # IMPORTANT:
    # DO NOT use previous assistant messages here.
    #
    # Do NOT do:
    #
    # messages = st.session_state.analyst_messages
    #
    # because that would send:
    #
    # role = assistant
    #
    # which is rejected by the current endpoint/runtime.
    # ------------------------------------------------------------------------

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": analyst_question
                }
            ]
        }
    ]

    request_body = {
        "messages": messages,
        "semantic_view": SEMANTIC_VIEW
    }

    start_time = time.time()

    try:
        # IMPORTANT:
        # Pass request_body directly as a Python dictionary.
        #
        # DO NOT use:
        #
        # json.dumps(request_body)
        #
        # because the Snowflake runtime expects an object,
        # not a JSON string.
        response = _snowflake.send_snow_api_request(
            "POST",
            ANALYST_ENDPOINT,
            {},
            {},
            request_body
        )

    except Exception as e:
        raise Exception(
            f"Cortex Analyst request failed: {str(e)}"
        )

    analyst_seconds = time.time() - start_time

    # ------------------------------------------------------------------------
    # GET HTTP STATUS
    # ------------------------------------------------------------------------

    status = None

    try:
        status = response.status
    except Exception:
        pass

    if status is None:
        try:
            status = response.status_code
        except Exception:
            pass

    if status is None and isinstance(response, dict):
        status = response.get("status")

    # ------------------------------------------------------------------------
    # GET RAW RESPONSE CONTENT
    # ------------------------------------------------------------------------

    raw_content = None

    try:
        raw_content = response.content
    except Exception:
        pass

    if raw_content is None:
        try:
            raw_content = response.body
        except Exception:
            pass

    if raw_content is None and isinstance(response, dict):
        raw_content = response.get("content")

    # ------------------------------------------------------------------------
    # CONVERT BYTES TO STRING
    # ------------------------------------------------------------------------

    if isinstance(raw_content, bytes):
        raw_content = raw_content.decode(
            "utf-8",
            errors="replace"
        )

    # ------------------------------------------------------------------------
    # TRY response.json()
    # ------------------------------------------------------------------------

    parsed_response = None

    try:
        if hasattr(response, "json"):
            parsed_response = response.json()
    except Exception:
        parsed_response = None

    # ------------------------------------------------------------------------
    # TRY json.loads()
    # ------------------------------------------------------------------------

    if parsed_response is None and isinstance(raw_content, str):
        try:
            parsed_response = json.loads(raw_content)
        except Exception:
            parsed_response = None

    # ------------------------------------------------------------------------
    # HANDLE HTTP ERRORS
    # ------------------------------------------------------------------------

    if status is not None:

        try:
            numeric_status = int(status)
        except Exception:
            numeric_status = None

        if numeric_status is not None and numeric_status >= 400:

            error_text = raw_content

            if parsed_response is not None:
                try:
                    error_text = json.dumps(
                        parsed_response,
                        indent=2
                    )
                except Exception:
                    error_text = str(parsed_response)

            raise Exception(
                f"Cortex Analyst request failed "
                f"(HTTP {numeric_status}): {error_text}"
            )

    # ------------------------------------------------------------------------
    # VALIDATE RESPONSE
    # ------------------------------------------------------------------------

    if parsed_response is None:

        raise Exception(
            "Invalid Cortex Analyst response.\n\n"
            f"HTTP Status: {status}\n"
            f"Response Type: {type(response)}\n"
            f"Raw Response: {raw_content}"
        )

    return parsed_response, analyst_seconds


# ============================================================================
# PARSE CORTEX ANALYST RESPONSE
# ============================================================================

def parse_analyst_response(response):
    request_id = None

    if isinstance(response, dict):

        request_id = response.get("request_id")

        if request_id is None:
            request_id = response.get("requestId")

        if request_id is None:
            request_id = response.get("id")

    text_parts = []

    sql_statement = None

    suggestions = []

    # ------------------------------------------------------------------------
    # GET MESSAGE
    # ------------------------------------------------------------------------

    message = None

    if isinstance(response, dict):
        message = response.get("message")

    if message is None:
        message = {}

    # ------------------------------------------------------------------------
    # GET MESSAGE CONTENT
    # ------------------------------------------------------------------------

    content = message.get("content", [])

    if not isinstance(content, list):
        content = []

    for item in content:

        if not isinstance(item, dict):
            continue

        item_type = item.get("type")

        # --------------------------------------------------------------------
        # TEXT
        # --------------------------------------------------------------------

        if item_type == "text":

            text_value = item.get("text")

            if text_value:
                text_parts.append(str(text_value))

        # --------------------------------------------------------------------
        # SQL
        # --------------------------------------------------------------------

        elif item_type == "sql":

            sql_statement = (
                item.get("statement")
                or item.get("sql")
                or item.get("query")
            )

        # --------------------------------------------------------------------
        # SUGGESTIONS
        # --------------------------------------------------------------------

        elif item_type == "suggestions":

            item_suggestions = item.get("suggestions", [])

            if isinstance(item_suggestions, list):
                suggestions.extend(item_suggestions)

        # --------------------------------------------------------------------
        # GENERIC FALLBACK
        # --------------------------------------------------------------------

        else:

            possible_text = (
                item.get("text")
                or item.get("statement")
                or item.get("sql")
                or item.get("query")
            )

            if possible_text:

                if (
                    isinstance(possible_text, str)
                    and (
                        possible_text.strip().upper().startswith("SELECT")
                        or possible_text.strip().upper().startswith("WITH")
                    )
                ):
                    if sql_statement is None:
                        sql_statement = possible_text

                else:
                    text_parts.append(str(possible_text))

    # ------------------------------------------------------------------------
    # TOP-LEVEL FALLBACKS
    # ------------------------------------------------------------------------

    if not text_parts and isinstance(response, dict):

        top_text = response.get("text")

        if top_text:
            text_parts.append(str(top_text))

    if sql_statement is None and isinstance(response, dict):

        sql_statement = (
            response.get("sql")
            or response.get("statement")
            or response.get("query")
        )

    response_text = "\n\n".join(text_parts).strip()

    return {
        "request_id": request_id,
        "text": response_text,
        "sql": sql_statement,
        "suggestions": suggestions
    }


# ============================================================================
# SQL VALIDATION
# ============================================================================

def clean_sql_for_validation(sql):
    if not sql:
        return ""

    cleaned = sql

    # Remove block comments
    cleaned = re.sub(
        r"/\*.*?\*/",
        " ",
        cleaned,
        flags=re.DOTALL
    )

    # Remove single-line comments
    cleaned = re.sub(
        r"--.*?$",
        " ",
        cleaned,
        flags=re.MULTILINE
    )

    # Replace string literals
    cleaned = re.sub(
        r"'(?:''|[^'])*'",
        "''",
        cleaned
    )

    return cleaned.strip()


def validate_generated_sql(sql):

    if not sql:
        raise Exception(
            "Cortex Analyst did not return SQL for this question."
        )

    cleaned_sql = clean_sql_for_validation(sql)

    # ------------------------------------------------------------------------
    # ONLY SELECT / WITH
    # ------------------------------------------------------------------------

    if not re.match(
        r"^(SELECT|WITH)\b",
        cleaned_sql,
        flags=re.IGNORECASE
    ):
        raise Exception(
            "Generated SQL is not a SELECT/WITH query."
        )

    # ------------------------------------------------------------------------
    # PREVENT MULTIPLE STATEMENTS
    # ------------------------------------------------------------------------

    sql_without_trailing_semicolon = cleaned_sql.rstrip()

    if ";" in sql_without_trailing_semicolon:
        raise Exception(
            "Multiple SQL statements are not allowed."
        )

    # ------------------------------------------------------------------------
    # BLOCK DML / DDL / ADMIN OPERATIONS
    # ------------------------------------------------------------------------

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
        r"\bSYSTEM\$\b",
        r"\bALTER\s+SESSION\b",
        r"\bALTER\s+USER\b",
        r"\bALTER\s+ROLE\b"
    ]

    for pattern in blocked_patterns:

        if re.search(
            pattern,
            cleaned_sql,
            flags=re.IGNORECASE
        ):
            raise Exception(
                f"Generated SQL contains a blocked operation: {pattern}"
            )

    return sql.strip()


# ============================================================================
# EXECUTE GENERATED SQL
# ============================================================================

def execute_generated_sql(sql):

    validated_sql = validate_generated_sql(sql)

    wrapped_sql = f"""
SELECT *
FROM (
    {validated_sql}
) AS ANALYST_RESULT
LIMIT {MAX_RESULT_ROWS}
"""

    start_time = time.time()

    dataframe = session.sql(wrapped_sql).to_pandas()

    execution_seconds = time.time() - start_time

    return dataframe, execution_seconds


# ============================================================================
# LOG QUERY
# ============================================================================

def log_query(
    user_question,
    analyst_question,
    response_text,
    generated_sql,
    execution_status,
    analyst_seconds,
    execution_seconds,
    rows_returned,
    error_message,
    request_id
):

    query_id = None

    # ------------------------------------------------------------------------
    # TRY NEW AUDIT TABLE
    # ------------------------------------------------------------------------

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

        # Retrieve the latest query ID for this user/request
        if request_id:

            try:

                id_result = session.sql(
                    f"""
                    SELECT QUERY_ID
                    FROM {AUDIT_TABLE}
                    WHERE USER_NAME = ?
                      AND REQUEST_ID = ?
                    ORDER BY QUERY_TIMESTAMP DESC
                    LIMIT 1
                    """,
                    params=[
                        CURRENT_USER,
                        request_id
                    ]
                ).collect()

                if id_result:
                    query_id = id_result[0]["QUERY_ID"]

            except Exception:
                pass

        return query_id

    except Exception:

        # --------------------------------------------------------------------
        # FALLBACK TO LEGACY LOG TABLE
        # --------------------------------------------------------------------

        try:

            session.sql(
                f"""
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
                """,
                params=[
                    CURRENT_USER,
                    user_question,
                    response_text,
                    SEMANTIC_MODEL_NAME
                ]
            ).collect()

        except Exception:
            pass

    return query_id


# ============================================================================
# LOG FEEDBACK
# ============================================================================

def log_feedback(query_id, feedback):

    if not query_id:
        return False

    try:

        session.sql(
            f"""
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
            """,
            params=[
                query_id,
                CURRENT_USER,
                feedback
            ]
        ).collect()

        return True

    except Exception:

        return False


# ============================================================================
# GET QUERY HISTORY
# ============================================================================

def get_query_history():

    # ------------------------------------------------------------------------
    # TRY NEW AUDIT TABLE
    # ------------------------------------------------------------------------

    try:

        history = session.sql(
            f"""
            SELECT
                QUERY_ID,
                QUERY_TIMESTAMP,
                USER_NAME,
                REQUEST_ID,
                USER_QUESTION,
                RESPONSE,
                GENERATED_SQL,
                EXECUTION_STATUS,
                ANALYST_SECONDS,
                EXECUTION_SECONDS,
                ROWS_RETURNED,
                ERROR_MESSAGE,
                SEMANTIC_MODEL_NAME,
                APPLICATION_NAME
            FROM {AUDIT_TABLE}
            WHERE USER_NAME = ?
            ORDER BY QUERY_TIMESTAMP DESC
            LIMIT {QUERY_HISTORY_LIMIT}
            """,
            params=[CURRENT_USER]
        ).to_pandas()

        return history

    except Exception:

        # --------------------------------------------------------------------
        # FALLBACK TO LEGACY TABLE
        # --------------------------------------------------------------------

        try:

            history = session.sql(
                f"""
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
                """,
                params=[CURRENT_USER]
            ).to_pandas()

            return history

        except Exception:

            return pd.DataFrame()


# ============================================================================
# PROCESS QUESTION
# ============================================================================

def process_question(question):

    question = question.strip()

    if not question:

        st.warning(
            "Please enter a sales question."
        )

        return

    # Reset previous status
    st.session_state.last_status = None
    st.session_state.last_error = None

    # ------------------------------------------------------------------------
    # STORE QUESTION
    # ------------------------------------------------------------------------

    st.session_state.last_question = question

    # ------------------------------------------------------------------------
    # ASK CORTEX ANALYST
    # ------------------------------------------------------------------------

    try:

        with st.spinner("Analyzing your question..."):

            analyst_response, analyst_seconds = ask_cortex_analyst(
                question
            )

        # --------------------------------------------------------------------
        # PARSE RESPONSE
        # --------------------------------------------------------------------

        parsed = parse_analyst_response(
            analyst_response
        )

        request_id = parsed.get("request_id")

        response_text = parsed.get("text", "")

        generated_sql = parsed.get("sql")

        suggestions = parsed.get(
            "suggestions",
            []
        )

        analyst_question = build_analyst_question(
            question
        )

        # --------------------------------------------------------------------
        # SAVE SESSION STATE
        # --------------------------------------------------------------------

        st.session_state.last_request_id = request_id

        st.session_state.last_analyst_question = (
            analyst_question
        )

        st.session_state.last_response = response_text

        st.session_state.last_sql = generated_sql

        # --------------------------------------------------------------------
        # EXECUTE SQL
        # --------------------------------------------------------------------

        dataframe = pd.DataFrame()

        execution_seconds = 0

        execution_error = None

        if generated_sql:

            try:

                with st.spinner(
                    "Running the generated query..."
                ):

                    dataframe, execution_seconds = (
                        execute_generated_sql(
                            generated_sql
                        )
                    )

                st.session_state.last_dataframe = dataframe

                st.session_state.last_status = "SUCCESS"

            except Exception as sql_error:

                execution_error = str(sql_error)

                st.session_state.last_status = (
                    "SQL_EXECUTION_ERROR"
                )

                st.session_state.last_error = (
                    execution_error
                )

        else:

            st.session_state.last_dataframe = (
                pd.DataFrame()
            )

            st.session_state.last_status = (
                "NO_SQL"
            )

        # --------------------------------------------------------------------
        # LOG QUERY
        # --------------------------------------------------------------------

        execution_status = st.session_state.last_status

        rows_returned = 0

        if dataframe is not None:
            rows_returned = len(dataframe)

        query_id = log_query(
            user_question=question,
            analyst_question=analyst_question,
            response_text=response_text,
            generated_sql=generated_sql,
            execution_status=execution_status,
            analyst_seconds=analyst_seconds,
            execution_seconds=execution_seconds,
            rows_returned=rows_returned,
            error_message=execution_error,
            request_id=request_id
        )

        st.session_state.last_query_id = query_id

        # --------------------------------------------------------------------
        # SAVE HISTORY IN SESSION
        # --------------------------------------------------------------------

        st.session_state.conversation_history.append(
            {
                "question": question,
                "response": response_text,
                "sql": generated_sql,
                "dataframe": dataframe,
                "request_id": request_id
            }
        )

        # --------------------------------------------------------------------
        # DISPLAY ANSWER
        # --------------------------------------------------------------------

        st.markdown(
            '<div class="section-title">Answer</div>',
            unsafe_allow_html=True
        )

        if response_text:

            st.markdown(
                response_text
            )

        else:

            st.info(
                "Cortex Analyst returned a result, "
                "but no explanation text was provided."
            )

        # --------------------------------------------------------------------
        # DISPLAY RESULTS
        # --------------------------------------------------------------------

        if (
            dataframe is not None
            and not dataframe.empty
        ):

            st.markdown(
                '<div class="section-title">Results</div>',
                unsafe_allow_html=True
            )

            st.dataframe(
                dataframe,
                use_container_width=True
            )

            # ---------------------------------------------------------------
            # CSV DOWNLOAD
            # ---------------------------------------------------------------

            csv_data = dataframe.to_csv(
                index=False
            )

            st.download_button(
                label="Download Results as CSV",
                data=csv_data,
                file_name="sales_ai_results.csv",
                mime="text/csv"
            )

        elif generated_sql and not execution_error:

            st.info(
                "The query executed successfully but returned no rows."
            )

        # --------------------------------------------------------------------
        # SQL
        # --------------------------------------------------------------------

        if generated_sql:

            with st.expander(
                "View Generated SQL"
            ):

                st.code(
                    generated_sql,
                    language="sql"
                )

        # --------------------------------------------------------------------
        # REQUEST ID
        # --------------------------------------------------------------------

        if request_id:

            with st.expander(
                "Technical Details"
            ):

                st.write(
                    f"Request ID: {request_id}"
                )

                st.write(
                    f"Analyst processing time: "
                    f"{analyst_seconds:.2f} seconds"
                )

                if execution_seconds:

                    st.write(
                        f"SQL execution time: "
                        f"{execution_seconds:.2f} seconds"
                    )

        # --------------------------------------------------------------------
        # SQL EXECUTION ERROR
        # --------------------------------------------------------------------

        if execution_error:

            st.error(
                "Cortex Analyst generated SQL, but "
                "the SQL could not be executed."
            )

            with st.expander(
                "SQL Execution Error"
            ):

                st.code(
                    execution_error
                )

        # --------------------------------------------------------------------
        # SUGGESTIONS
        # --------------------------------------------------------------------

        if suggestions:

            st.markdown(
                '<div class="section-title">Suggested Questions</div>',
                unsafe_allow_html=True
            )

            for suggestion in suggestions:

                if isinstance(
                    suggestion,
                    dict
                ):

                    suggestion_text = (
                        suggestion.get("text")
                        or suggestion.get("question")
                        or suggestion.get("value")
                    )

                else:

                    suggestion_text = str(
                        suggestion
                    )

                if suggestion_text:

                    st.write(
                        "• " + suggestion_text
                    )

    except Exception as e:

        st.session_state.last_status = "ERROR"

        st.session_state.last_error = str(e)

        st.error(
            "Sales AI could not process your question."
        )

        with st.expander(
            "Technical Details",
            expanded=True
        ):

            st.code(
                str(e)
            )


# ============================================================================
# HEADER
# ============================================================================

st.markdown(
    '<div class="main-title">📊 Sales AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    'Ask questions about sales performance, customers, products, '
    'sales representatives, regions, territories, and trends.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:

    st.markdown(
        "## Business Context"
    )

    # ------------------------------------------------------------------------
    # BUSINESS ROLE
    # ------------------------------------------------------------------------

    business_role = st.selectbox(
        "Business Role",
        [
            "Sales Executive",
            "Sales Manager",
            "Sales Analyst",
            "Business User",
            "Data / AI Developer"
        ],
        index=2,
        key="business_role"
    )

    # ------------------------------------------------------------------------
    # ANSWER STYLE
    # ------------------------------------------------------------------------

    answer_style = st.selectbox(
        "Answer Style",
        [
            "Executive summary",
            "Detailed analysis",
            "Data focused",
            "Technical"
        ],
        index=1,
        key="answer_style"
    )

    # ------------------------------------------------------------------------
    # DATE FILTER
    # ------------------------------------------------------------------------

    date_filter = st.selectbox(
        "Date Filter",
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
        index=3,
        key="date_filter"
    )

    # ------------------------------------------------------------------------
    # COMPARISON
    # ------------------------------------------------------------------------

    comparison = st.selectbox(
        "Comparison",
        [
            "No comparison",
            "Previous period",
            "Previous year",
            "Year over year",
            "Month over month"
        ],
        index=0,
        key="comparison"
    )

    st.markdown("---")

    st.markdown(
        "### Business Filters"
    )

    # ------------------------------------------------------------------------
    # REGION
    # ------------------------------------------------------------------------

    st.text_input(
        "Region",
        key="region_filter",
        placeholder="e.g. West"
    )

    # ------------------------------------------------------------------------
    # TERRITORY
    # ------------------------------------------------------------------------

    st.text_input(
        "Territory",
        key="territory_filter",
        placeholder="e.g. Texas"
    )

    # ------------------------------------------------------------------------
    # SALES REP
    # ------------------------------------------------------------------------

    st.text_input(
        "Sales Rep",
        key="sales_rep_filter",
        placeholder="e.g. John Smith"
    )

    # ------------------------------------------------------------------------
    # CUSTOMER
    # ------------------------------------------------------------------------

    st.text_input(
        "Customer",
        key="customer_filter",
        placeholder="e.g. ABC Corp"
    )

    # ------------------------------------------------------------------------
    # INDUSTRY
    # ------------------------------------------------------------------------

    st.text_input(
        "Industry",
        key="industry_filter",
        placeholder="e.g. Healthcare"
    )

    # ------------------------------------------------------------------------
    # PRODUCT
    # ------------------------------------------------------------------------

    st.text_input(
        "Product",
        key="product_filter",
        placeholder="e.g. Product A"
    )

    # ------------------------------------------------------------------------
    # PRODUCT CATEGORY
    # ------------------------------------------------------------------------

    st.text_input(
        "Product Category",
        key="product_category_filter",
        placeholder="e.g. Electronics"
    )

    # ------------------------------------------------------------------------
    # CHANNEL
    # ------------------------------------------------------------------------

    st.text_input(
        "Channel",
        key="channel_filter",
        placeholder="e.g. Online"
    )

    st.markdown("---")

    # ------------------------------------------------------------------------
    # START NEW CONVERSATION
    # ------------------------------------------------------------------------

    if st.button(
        "Start New Conversation",
        use_container_width=True
    ):

        st.session_state.analyst_messages = []

        st.session_state.conversation_history = []

        st.session_state.last_query_id = None

        st.session_state.last_request_id = None

        st.session_state.last_question = None

        st.session_state.last_analyst_question = None

        st.session_state.last_sql = None

        st.session_state.last_response = None

        st.session_state.last_dataframe = None

        st.session_state.last_status = None

        st.session_state.last_error = None

        st.session_state.question_input = ""

        st.success(
            "Conversation cleared. Enter a new question below."
        )


# ============================================================================
# TABS
# ============================================================================

overview_tab, sales_ai_tab, history_tab, samples_tab, about_tab = st.tabs(
    [
        "Executive Overview",
        "Sales AI",
        "Query History",
        "Sample Questions",
        "About"
    ]
)


# ============================================================================
# EXECUTIVE OVERVIEW
# ============================================================================

with overview_tab:

    st.markdown(
        '<div class="section-title">Executive Overview</div>',
        unsafe_allow_html=True
    )

    st.info(
        "Use the Sales AI tab to ask questions about your sales data."
    )

    # ------------------------------------------------------------------------
    # LAST RESULT SUMMARY
    # ------------------------------------------------------------------------

    if st.session_state.last_dataframe is not None:

        dataframe = st.session_state.last_dataframe

        col1, col2, col3 = st.columns(3)

        with col1:

            st.markdown(
                '<div class="metric-label">Rows Returned</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="metric-value">{len(dataframe):,}</div>',
                unsafe_allow_html=True
            )

        with col2:

            if st.session_state.last_request_id:

                st.markdown(
                    '<div class="metric-label">Analyst Request</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    '<div class="metric-value">Completed</div>',
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    '<div class="metric-label">Analyst Request</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    '<div class="metric-value">-</div>',
                    unsafe_allow_html=True
                )

        with col3:

            status = (
                st.session_state.last_status
                or "No query"
            )

            st.markdown(
                '<div class="metric-label">Status</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="metric-value">{html.escape(status)}</div>',
                unsafe_allow_html=True
            )

    else:

        st.markdown(
            """
            <div class="info-box">
                No sales question has been executed yet.
                Go to <b>Sales AI</b> to get started.
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================================
# SALES AI
# ============================================================================

with sales_ai_tab:

    st.markdown(
        '<div class="section-title">Ask Sales AI</div>',
        unsafe_allow_html=True
    )

    # ------------------------------------------------------------------------
    # ACTIVE FILTER SUMMARY
    # ------------------------------------------------------------------------

    active_filters = []

    if st.session_state.get(
        "date_filter"
    ):
        active_filters.append(
            f"Date: {st.session_state.date_filter}"
        )

    if st.session_state.get(
        "comparison"
    ) != "No comparison":

        active_filters.append(
            f"Comparison: {st.session_state.comparison}"
        )

    if st.session_state.get(
        "region_filter",
        ""
    ).strip():

        active_filters.append(
            f"Region: {st.session_state.region_filter.strip()}"
        )

    if st.session_state.get(
        "territory_filter",
        ""
    ).strip():

        active_filters.append(
            f"Territory: {st.session_state.territory_filter.strip()}"
        )

    if st.session_state.get(
        "sales_rep_filter",
        ""
    ).strip():

        active_filters.append(
            f"Sales Rep: {st.session_state.sales_rep_filter.strip()}"
        )

    if st.session_state.get(
        "customer_filter",
        ""
    ).strip():

        active_filters.append(
            f"Customer: {st.session_state.customer_filter.strip()}"
        )

    if st.session_state.get(
        "industry_filter",
        ""
    ).strip():

        active_filters.append(
            f"Industry: {st.session_state.industry_filter.strip()}"
        )

    if st.session_state.get(
        "product_filter",
        ""
    ).strip():

        active_filters.append(
            f"Product: {st.session_state.product_filter.strip()}"
        )

    if st.session_state.get(
        "product_category_filter",
        ""
    ).strip():

        active_filters.append(
            f"Product Category: "
            f"{st.session_state.product_category_filter.strip()}"
        )

    if st.session_state.get(
        "channel_filter",
        ""
    ).strip():

        active_filters.append(
            f"Channel: {st.session_state.channel_filter.strip()}"
        )

    if active_filters:

        safe_filters = [
            html.escape(str(x))
            for x in active_filters
        ]

        st.markdown(
            '<div class="info-box">'
            '<b>Active context:</b> '
            + " | ".join(safe_filters)
            + "</div>",
            unsafe_allow_html=True
        )

    # ------------------------------------------------------------------------
    # QUESTION INPUT
    # ------------------------------------------------------------------------

    question = st.text_area(
        "Enter your sales question",
        value=st.session_state.question_input,
        height=100,
        placeholder=(
            "Example: Show the top 10 sales representatives "
            "by revenue."
        ),
        key="question_text_area"
    )

    col1, col2 = st.columns([1, 5])

    with col1:

        ask_button = st.button(
            "Ask Sales AI",
            use_container_width=True
        )

    with col2:

        clear_button = st.button(
            "Clear",
            use_container_width=True
        )

    if clear_button:

        st.session_state.question_input = ""

        st.session_state.last_question = None

        st.session_state.last_response = None

        st.session_state.last_sql = None

        st.session_state.last_dataframe = None

        st.session_state.last_status = None

        st.session_state.last_error = None

    if ask_button:

        process_question(
            question
        )

    # ------------------------------------------------------------------------
    # FEEDBACK
    # ------------------------------------------------------------------------

    if st.session_state.last_query_id:

        st.markdown(
            '<div class="section-title">Was this answer helpful?</div>',
            unsafe_allow_html=True
        )

        feedback_col1, feedback_col2 = st.columns(2)

        with feedback_col1:

            if st.button(
                "👍 Helpful",
                use_container_width=True
            ):

                if log_feedback(
                    st.session_state.last_query_id,
                    "HELPFUL"
                ):

                    st.success(
                        "Thank you for your feedback."
                    )

                else:

                    st.warning(
                        "Feedback could not be saved."
                    )

        with feedback_col2:

            if st.button(
                "👎 Not Helpful",
                use_container_width=True
            ):

                if log_feedback(
                    st.session_state.last_query_id,
                    "NOT_HELPFUL"
                ):

                    st.success(
                        "Thank you for your feedback."
                    )

                else:

                    st.warning(
                        "Feedback could not be saved."
                    )


# ============================================================================
# QUERY HISTORY
# ============================================================================

with history_tab:

    st.markdown(
        '<div class="section-title">Query History</div>',
        unsafe_allow_html=True
    )

    history = get_query_history()

    if history.empty:

        st.info(
            "No query history is available."
        )

    else:

        st.dataframe(
            history,
            use_container_width=True
        )


# ============================================================================
# SAMPLE QUESTIONS
# ============================================================================

with samples_tab:

    st.markdown(
        '<div class="section-title">Sample Questions</div>',
        unsafe_allow_html=True
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

    for sample_question in sample_questions:

        st.write(
            "• " + sample_question
        )


# ============================================================================
# ABOUT
# ============================================================================

with about_tab:

    st.markdown(
        '<div class="section-title">About Sales AI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        **Sales AI** is a Snowflake-native sales analytics application.

        It uses:

        - Snowflake Streamlit
        - Cortex Analyst REST API
        - Snowflake semantic view
        - Snowpark session
        - Snowflake audit logging

        Semantic view:

        `SALES_DATA.PUBLIC.SALES_SEMANTIC_MODEL`

        The application converts natural-language sales questions into
        SQL through Cortex Analyst and executes the generated read-only
        query against Snowflake.
        """
    )

    st.markdown("---")

    st.markdown(
        f"**Current User:** `{CURRENT_USER}`"
    )

    st.markdown(
        f"**Semantic View:** `{SEMANTIC_VIEW}`"
    )

    st.markdown(
        f"**Application:** `{APPLICATION_NAME}`"
    )