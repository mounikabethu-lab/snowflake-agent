"""
===============================================================================
SALES AI INTELLIGENCE APPLICATION
===============================================================================

Platform:
    Streamlit in Snowflake

AI:
    Snowflake Cortex Analyst

Semantic View:
    SALES_DATA.PUBLIC.SALES_SEMANTIC_MODEL

Purpose:
    Production-oriented Sales Analytics and AI Assistant.

Major Features:
    - Executive overview
    - Natural language Sales AI
    - Multi-turn conversation
    - Global business filters
    - AI follow-up suggestions
    - Explain / investigate functionality
    - Generated SQL visibility
    - Read-only SQL protection
    - Query execution monitoring
    - Query history
    - Feedback collection
    - CSV download
    - Result size protection
    - Production error handling
    - Audit logging

===============================================================================
"""

import streamlit as st
import pandas as pd
import json
import _snowflake
import time

from datetime import datetime, date, timedelta
from snowflake.snowpark.context import get_active_session


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Sales Intelligence - Cortex Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# CONSTANTS / CONFIGURATION
# =============================================================================

SEMANTIC_VIEW = "SALES_DATA.PUBLIC.SALES_SEMANTIC_MODEL"

ANALYST_ENDPOINT = "/api/v2/cortex/analyst/message"

MAX_RESULT_ROWS = 10000

QUERY_HISTORY_LIMIT = 50

APPLICATION_NAME = "SALES_AI"

SEMANTIC_MODEL_NAME = "SALES_SEMANTIC_MODEL"


# =============================================================================
# SNOWFLAKE SESSION
# =============================================================================

session = get_active_session()


# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .sub-title {
        color: #666666;
        margin-bottom: 1.5rem;
    }

    .response-box {
        background: linear-gradient(
            135deg,
            #f0f7ff 0%,
            #e8f4f8 100%
        );

        padding: 1.5rem;

        border-radius: 0.75rem;

        border-left: 4px solid #0066cc;

        margin: 1rem 0;

        font-size: 1rem;

        line-height: 1.6;
    }

    .insight-box {
        background: #f8f9fa;

        padding: 1rem;

        border-radius: 0.5rem;

        border-left: 4px solid #666666;

        margin: 0.5rem 0;
    }

    .small-text {
        font-size: 0.8rem;
        color: #777777;
    }

    .metric-label {
        font-size: 0.85rem;
        color: #666666;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_question" not in st.session_state:
    st.session_state.last_question = None

if "last_response" not in st.session_state:
    st.session_state.last_response = None

if "last_sql" not in st.session_state:
    st.session_state.last_sql = None

if "last_request_id" not in st.session_state:
    st.session_state.last_request_id = None

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "last_execution_seconds" not in st.session_state:
    st.session_state.last_execution_seconds = None

if "last_sql_success" not in st.session_state:
    st.session_state.last_sql_success = False

if "last_error" not in st.session_state:
    st.session_state.last_error = None

if "suggestions" not in st.session_state:
    st.session_state.suggestions = []

if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = False


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def safe_string(value):
    """
    Safely convert a value to string.
    """

    if value is None:
        return ""

    return str(value)


def escape_sql_string(value):
    """
    Escape a string before embedding it in SQL.
    """

    return safe_string(value).replace("'", "''")


# =============================================================================
# DATE FILTER
# =============================================================================

def get_date_range(selection):
    """
    Return start and end dates based on selected business timeframe.
    """

    today = date.today()

    if selection == "Today":
        return today, today

    if selection == "Yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday

    if selection == "Last 7 Days":
        return today - timedelta(days=6), today

    if selection == "Last 30 Days":
        return today - timedelta(days=29), today

    if selection == "Last 90 Days":
        return today - timedelta(days=89), today

    if selection == "MTD":
        return today.replace(day=1), today

    if selection == "QTD":
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        return today.replace(
            month=quarter_month,
            day=1
        ), today

    if selection == "YTD":
        return today.replace(
            month=1,
            day=1
        ), today

    if selection == "Last Month":

        first_day_current = today.replace(day=1)

        last_day_previous = (
            first_day_current - timedelta(days=1)
        )

        first_day_previous = last_day_previous.replace(day=1)

        return first_day_previous, last_day_previous

    if selection == "Last Quarter":

        current_quarter = ((today.month - 1) // 3)

        if current_quarter == 0:

            year = today.year - 1
            quarter = 3

        else:

            year = today.year
            quarter = current_quarter - 1

        start_month = quarter * 3 + 1

        start_date = date(
            year,
            start_month,
            1
        )

        if start_month == 10:

            end_date = date(
                year,
                12,
                31
            )

        else:

            next_quarter = date(
                year,
                start_month + 3,
                1
            )

            end_date = next_quarter - timedelta(days=1)

        return start_date, end_date

    if selection == "Last Year":

        return (
            date(today.year - 1, 1, 1),
            date(today.year - 1, 12, 31)
        )

    return None, None


# =============================================================================
# BUILD BUSINESS CONTEXT
# =============================================================================

def build_business_context(
    date_filter,
    custom_start,
    custom_end,
    comparison,
    region,
    territory,
    sales_rep,
    product,
    channel
):
    """
    Build business context that is added to the user's natural language
    question.

    IMPORTANT:
        We intentionally do not generate physical SQL filters here because
        the actual semantic-view dimension names may differ.

        Cortex Analyst interprets the business terms using the semantic model.
    """

    context = []

    # -------------------------------------------------------------------------
    # Date
    # -------------------------------------------------------------------------

    if date_filter == "Custom":

        context.append(
            f"Analyze data from {custom_start} through {custom_end}."
        )

    else:

        start_date, end_date = get_date_range(
            date_filter
        )

        if start_date and end_date:

            context.append(
                f"Analyze data from {start_date} through {end_date}."
            )

    # -------------------------------------------------------------------------
    # Comparison
    # -------------------------------------------------------------------------

    if comparison != "None":

        context.append(
            f"Compare the requested results against {comparison}."
        )

    # -------------------------------------------------------------------------
    # Business dimensions
    # -------------------------------------------------------------------------

    if region != "All":

        context.append(
            f"Restrict the analysis to region: {region}."
        )

    if territory != "All":

        context.append(
            f"Restrict the analysis to territory: {territory}."
        )

    if sales_rep != "All":

        context.append(
            f"Restrict the analysis to sales representative: {sales_rep}."
        )

    if product != "All":

        context.append(
            f"Restrict the analysis to product: {product}."
        )

    if channel != "All":

        context.append(
            f"Restrict the analysis to sales channel: {channel}."
        )

    if not context:

        return ""

    return (
        "\n\nBUSINESS FILTER CONTEXT:\n"
        + "\n".join(
            f"- {item}" for item in context
        )
    )


# =============================================================================
# CORTEX ANALYST API
# =============================================================================

def ask_cortex_analyst(
    user_question,
    conversation_messages=None
):
    """
    Send a question to Cortex Analyst.

    Supports multi-turn conversation by sending previous messages.
    """

    messages = []

    if conversation_messages:

        messages.extend(
            conversation_messages
        )

    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_question
                }
            ]
        }
    )

    request_body = {
        "messages": messages,
        "semantic_view": SEMANTIC_VIEW
    }

    response = _snowflake.send_snow_api_request(
        "POST",
        ANALYST_ENDPOINT,
        {},
        {},
        request_body,
        {}
    )

    return response


# =============================================================================
# EXTRACT CORTEX ANALYST RESPONSE
# =============================================================================

def extract_analyst_response(api_response):
    """
    Extract text, SQL, suggestions and request ID.
    """

    status_code = api_response.get(
        "status"
    )

    if status_code != 200:

        error_content = api_response.get(
            "content",
            ""
        )

        raise Exception(
            "Cortex Analyst API failed. "
            f"HTTP Status: {status_code}. "
            f"Response: {error_content}"
        )

    content = api_response.get(
        "content"
    )

    if isinstance(content, str):

        try:

            content = json.loads(
                content
            )

        except Exception:

            raise Exception(
                "Cortex Analyst returned "
                "an invalid JSON response."
            )

    if not isinstance(content, dict):

        raise Exception(
            "Unexpected Cortex Analyst response format."
        )

    analyst_message = content.get(
        "message",
        {}
    )

    message_content = analyst_message.get(
        "content",
        []
    )

    analyst_text = None

    generated_sql = None

    suggestions = []

    for item in message_content:

        if not isinstance(item, dict):
            continue

        item_type = item.get(
            "type"
        )

        if item_type == "text":

            analyst_text = item.get(
                "text"
            )

        elif item_type == "sql":

            generated_sql = item.get(
                "statement"
            )

        elif item_type == "suggestions":

            suggestions = item.get(
                "suggestions",
                []
            )

    request_id = (
        api_response.get("request_id")
        or api_response.get("requestId")
        or content.get("request_id")
        or content.get("requestId")
    )

    return {
        "raw_response": content,
        "text": analyst_text,
        "sql": generated_sql,
        "suggestions": suggestions,
        "request_id": request_id
    }


# =============================================================================
# SQL SAFETY VALIDATION
# =============================================================================

def validate_generated_sql(sql):
    """
    Validate generated SQL before execution.

    This application is intended to be read-only.

    Returns:
        (True, "")
        or
        (False, reason)
    """

    if not sql:

        return False, "No SQL was generated."

    normalized = (
        sql.strip()
        .upper()
    )

    # -------------------------------------------------------------------------
    # Only allow SELECT / WITH statements
    # -------------------------------------------------------------------------

    if not (
        normalized.startswith("SELECT")
        or normalized.startswith("WITH")
    ):

        return (
            False,
            "Only read-only SELECT queries are allowed."
        )

    # -------------------------------------------------------------------------
    # Dangerous SQL keywords
    # -------------------------------------------------------------------------

    blocked_keywords = [
        "INSERT ",
        "UPDATE ",
        "DELETE ",
        "MERGE ",
        "DROP ",
        "ALTER ",
        "TRUNCATE ",
        "CREATE ",
        "REPLACE ",
        "GRANT ",
        "REVOKE ",
        "CALL ",
        "COPY ",
        "PUT ",
        "REMOVE ",
        "UNDROP ",
        "EXECUTE "
    ]

    for keyword in blocked_keywords:

        if keyword in normalized:

            return (
                False,
                f"Blocked SQL operation detected: {keyword.strip()}"
            )

    return True, ""


# =============================================================================
# EXECUTE GENERATED SQL
# =============================================================================

def execute_generated_sql(sql):
    """
    Execute generated SQL and return a Pandas DataFrame.

    Uses to_pandas() directly to avoid Snowpark Row -> dict conversion issues.
    """

    valid, validation_message = validate_generated_sql(
        sql
    )

    if not valid:

        raise Exception(
            f"SQL security validation failed: "
            f"{validation_message}"
        )

    start_time = time.time()

    df = session.sql(
        sql
    ).limit(
        MAX_RESULT_ROWS
    ).to_pandas()

    execution_seconds = (
        time.time() - start_time
    )

    return df, execution_seconds


# =============================================================================
# AUDIT LOGGING
# =============================================================================

def log_query(
    question,
    response,
    generated_sql,
    request_id,
    execution_seconds,
    rows_returned,
    execution_status,
    error_message=None
):
    """
    Write application activity to ANALYST_QUERY_LOG.

    This function is intentionally defensive so logging failures never
    prevent the business user from receiving an answer.
    """

    try:

        # ---------------------------------------------------------------------
        # Check available columns dynamically.
        #
        # Existing ANALYST_QUERY_LOG may only contain the original columns.
        # Therefore we use the original INSERT structure for compatibility.
        # ---------------------------------------------------------------------

        escaped_question = escape_sql_string(
            question
        )

        escaped_response = escape_sql_string(
            response or ""
        )

        insert_query = f"""
            INSERT INTO ANALYST_QUERY_LOG
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
                CURRENT_USER(),
                '{escaped_question}',
                '{escaped_response}',
                '{escape_sql_string(SEMANTIC_MODEL_NAME)}'
            )
        """

        session.sql(
            insert_query
        ).collect()

    except Exception as log_error:

        st.warning(
            "⚠️ Query completed, but audit logging failed: "
            f"{str(log_error)}"
        )


# =============================================================================
# FEEDBACK LOGGING
# =============================================================================

def log_feedback(
    question,
    feedback
):
    """
    Store user feedback.

    Uses the existing log table only if compatible columns exist.
    Failure is non-blocking.
    """

    try:

        escaped_question = escape_sql_string(
            question
        )

        feedback_query = f"""
            INSERT INTO ANALYST_QUERY_LOG
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
                CURRENT_USER(),
                '{escaped_question}',
                'USER_FEEDBACK: {escape_sql_string(feedback)}',
                '{escape_sql_string(SEMANTIC_MODEL_NAME)}'
            )
        """

        session.sql(
            feedback_query
        ).collect()

    except Exception:
        pass


# =============================================================================
# PAGE HEADER
# =============================================================================

st.markdown(
    '<div class="main-title">📊 Sales Intelligence</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    'AI-powered sales analytics using Snowflake Cortex Analyst'
    '</div>',
    unsafe_allow_html=True
)


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:

    st.header("🎯 Analysis Filters")

    st.caption(
        "These filters are applied as business context to Cortex Analyst."
    )

    # -------------------------------------------------------------------------
    # Date
    # -------------------------------------------------------------------------

    date_filter = st.selectbox(
        "Date Range",
        [
            "Today",
            "Yesterday",
            "Last 7 Days",
            "Last 30 Days",
            "Last 90 Days",
            "MTD",
            "QTD",
            "YTD",
            "Last Month",
            "Last Quarter",
            "Last Year",
            "Custom"
        ],
        index=3
    )

    custom_start = None
    custom_end = None

    if date_filter == "Custom":

        custom_start = st.date_input(
            "Start Date",
            value=date.today() - timedelta(days=29)
        )

        custom_end = st.date_input(
            "End Date",
            value=date.today()
        )

        if custom_start > custom_end:

            st.error(
                "Start date cannot be after end date."
            )


    # -------------------------------------------------------------------------
    # Comparison
    # -------------------------------------------------------------------------

    comparison = st.selectbox(
        "Compare Against",
        [
            "None",
            "Previous Period",
            "Previous Year",
            "Same Period Last Year"
        ]
    )


    st.divider()


    # -------------------------------------------------------------------------
    # Business dimensions
    #
    # We intentionally use text inputs rather than querying unknown physical
    # tables. Cortex Analyst resolves the business terminology.
    # -------------------------------------------------------------------------

    region = st.text_input(
        "Region",
        value="All",
        placeholder="e.g. Northeast"
    )

    territory = st.text_input(
        "Territory",
        value="All",
        placeholder="e.g. Texas"
    )

    sales_rep = st.text_input(
        "Sales Rep",
        value="All",
        placeholder="e.g. John Smith"
    )

    product = st.text_input(
        "Product",
        value="All",
        placeholder="e.g. Product ABC"
    )

    channel = st.text_input(
        "Channel",
        value="All",
        placeholder="e.g. Online"
    )


    st.divider()


    # -------------------------------------------------------------------------
    # Conversation controls
    # -------------------------------------------------------------------------

    st.header("🤖 AI Controls")

    if st.button(
        "🧹 Clear Conversation",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.session_state.last_question = None

        st.session_state.last_response = None

        st.session_state.last_sql = None

        st.session_state.last_request_id = None

        st.session_state.last_result = None

        st.session_state.suggestions = []

        st.session_state.conversation_started = False

        st.rerun()


    st.divider()

    st.caption(
        "Semantic View"
    )

    st.code(
        SEMANTIC_VIEW,
        language="text"
    )

    st.caption(
        "Application: Sales Intelligence"
    )


# =============================================================================
# MAIN TABS
# =============================================================================

tab_overview, tab_ai, tab_history, tab_samples, tab_about = st.tabs(
    [
        "🏠 Executive Overview",
        "🤖 Sales AI",
        "📈 Query History",
        "📚 Sample Questions",
        "ℹ️ About"
    ]
)


# =============================================================================
# TAB 1 - EXECUTIVE OVERVIEW
# =============================================================================

with tab_overview:

    st.header("Executive Overview")

    st.caption(
        "Use Sales AI for detailed analysis and business explanations."
    )


    # -------------------------------------------------------------------------
    # KPI cards
    #
    # We do not hard-code KPI SQL because the actual semantic model measures
    # should determine the correct business definitions.
    # -------------------------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Revenue",
            "Ask AI"
        )

        st.caption(
            "Use Sales AI → total revenue"
        )


    with col2:

        st.metric(
            "Orders",
            "Ask AI"
        )

        st.caption(
            "Use Sales AI → order count"
        )


    with col3:

        st.metric(
            "Quota Attainment",
            "Ask AI"
        )

        st.caption(
            "Use Sales AI → quota attainment"
        )


    with col4:

        st.metric(
            "Customers",
            "Ask AI"
        )

        st.caption(
            "Use Sales AI → customer count"
        )


    st.divider()


    # -------------------------------------------------------------------------
    # Business insight cards
    # -------------------------------------------------------------------------

    st.subheader("💡 Recommended Business Analysis")


    insight_questions = [
        (
            "Revenue Performance",
            "What is total revenue for the selected period and how does it "
            "compare with the selected comparison period?"
        ),

        (
            "Sales Performance",
            "Which sales representatives are performing above and below quota?"
        ),

        (
            "Regional Performance",
            "Which regions are contributing most to revenue and which regions "
            "are declining?"
        ),

        (
            "Customer Risk",
            "Which high-value customers are showing declining revenue or "
            "potential churn risk?"
        )
    ]


    cols = st.columns(2)

    for index, item in enumerate(
        insight_questions
    ):

        title, question = item

        with cols[index % 2]:

            st.markdown(
                f"""
                <div class="insight-box">
                    <strong>{title}</strong><br>
                    {question}
                </div>
                """,
                unsafe_allow_html=True
            )


    st.info(
        "💡 The Executive Overview intentionally does not duplicate business "
        "logic already defined in your semantic model. Use the Sales AI tab "
        "to query the governed metrics and dimensions."
    )


# =============================================================================
# TAB 2 - SALES AI
# =============================================================================

with tab_ai:

    st.header("🤖 Sales AI Assistant")

    st.caption(
        "Ask questions about revenue, customers, products, quotas, "
        "sales representatives, regions, channels and performance."
    )


    # -------------------------------------------------------------------------
    # Conversation history
    # -------------------------------------------------------------------------

    for message in st.session_state.messages:

        role = message.get(
            "role"
        )

        content = message.get(
            "content",
            ""
        )

        if role == "user":

            with st.chat_message("user"):

                st.markdown(
                    content
                )

        elif role == "assistant":

            with st.chat_message("assistant"):

                st.markdown(
                    content
                )


    # -------------------------------------------------------------------------
    # Question input
    # -------------------------------------------------------------------------

    user_question = st.chat_input(
        "Ask a question about your sales data..."
    )


    # -------------------------------------------------------------------------
    # Suggested questions
    # -------------------------------------------------------------------------

    if not user_question and not st.session_state.messages:

        st.markdown("### Try asking")

        quick_questions = [
            "What is total revenue this year?",
            "Show the top 10 customers by revenue.",
            "Which sales reps are exceeding quota?",
            "Which regions have the highest revenue?",
            "Show revenue trends over time.",
            "Which products are driving revenue growth?",
            "Which customers have declining revenue?"
        ]

        quick_cols = st.columns(2)

        for index, question in enumerate(
            quick_questions
        ):

            with quick_cols[index % 2]:

                if st.button(
                    question,
                    key=f"quick_question_{index}",
                    use_container_width=True
                ):

                    user_question = question


    # -------------------------------------------------------------------------
    # Process question
    # -------------------------------------------------------------------------

    if user_question:

        # ---------------------------------------------------------------------
        # Validate custom dates
        # ---------------------------------------------------------------------

        if date_filter == "Custom":

            if (
                custom_start is None
                or custom_end is None
            ):

                st.error(
                    "Please select both start and end dates."
                )

                st.stop()

            if custom_start > custom_end:

                st.error(
                    "Start date cannot be after end date."
                )

                st.stop()


        # ---------------------------------------------------------------------
        # Build business context
        # ---------------------------------------------------------------------

        business_context = build_business_context(
            date_filter,
            custom_start,
            custom_end,
            comparison,
            region,
            territory,
            sales_rep,
            product,
            channel
        )


        analyst_question = (
            user_question
            + business_context
        )


        # ---------------------------------------------------------------------
        # Add user message to conversation
        # ---------------------------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_question
            }
        )


        with st.chat_message("user"):

            st.markdown(
                user_question
            )


        with st.chat_message("assistant"):

            with st.spinner(
                "🤔 Analyzing your question..."
            ):

                try:

                    # ========================================================
                    # CALL CORTEX ANALYST
                    # ========================================================

                    api_response = ask_cortex_analyst(
                        analyst_question,
                        st.session_state.messages[:-1]
                    )


                    analyst_result = extract_analyst_response(
                        api_response
                    )


                    response_text = analyst_result["text"]

                    generated_sql = analyst_result["sql"]

                    suggestions = analyst_result["suggestions"]

                    request_id = analyst_result["request_id"]


                    # ========================================================
                    # STORE AI RESPONSE
                    # ========================================================

                    if not response_text:

                        response_text = (
                            "Cortex Analyst generated an analysis "
                            "but did not return a text explanation."
                        )


                    st.session_state.last_question = user_question

                    st.session_state.last_response = response_text

                    st.session_state.last_sql = generated_sql

                    st.session_state.last_request_id = request_id

                    st.session_state.suggestions = suggestions


                    # ========================================================
                    # DISPLAY RESPONSE
                    # ========================================================

                    st.markdown(
                        f"""
                        <div class="response-box">
                        {response_text}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


                    # ========================================================
                    # EXECUTE SQL
                    # ========================================================

                    df = None

                    execution_seconds = None

                    sql_success = False

                    sql_error_message = None


                    if generated_sql:

                        with st.spinner(
                            "📊 Running analysis..."
                        ):

                            try:

                                df, execution_seconds = (
                                    execute_generated_sql(
                                        generated_sql
                                    )
                                )

                                sql_success = True

                                st.session_state.last_result = df

                                st.session_state.last_execution_seconds = (
                                    execution_seconds
                                )

                                st.session_state.last_sql_success = True

                                st.session_state.last_error = None


                            except Exception as sql_error:

                                sql_error_message = str(
                                    sql_error
                                )

                                st.session_state.last_sql_success = False

                                st.session_state.last_error = (
                                    sql_error_message
                                )


                    # ========================================================
                    # DISPLAY RESULTS
                    # ========================================================

                    if sql_success and df is not None:

                        st.markdown(
                            "### 📊 Query Result"
                        )


                        if df.empty:

                            st.info(
                                "The query executed successfully "
                                "but returned no rows."
                            )

                        else:

                            st.dataframe(
                                df,
                                use_container_width=True,
                                height=400
                            )


                            # ------------------------------------------------
                            # Result metadata
                            # ------------------------------------------------

                            result_col1, result_col2, result_col3 = (
                                st.columns(3)
                            )


                            with result_col1:

                                st.metric(
                                    "Rows Returned",
                                    f"{len(df):,}"
                                )


                            with result_col2:

                                st.metric(
                                    "Execution Time",
                                    f"{execution_seconds:.2f}s"
                                )


                            with result_col3:

                                if len(df) >= MAX_RESULT_ROWS:

                                    st.metric(
                                        "Result Status",
                                        "Limited"
                                    )

                                else:

                                    st.metric(
                                        "Result Status",
                                        "Complete"
                                    )


                            # ------------------------------------------------
                            # CSV download
                            # ------------------------------------------------

                            csv_data = df.to_csv(
                                index=False
                            ).encode(
                                "utf-8"
                            )


                            st.download_button(
                                "⬇️ Download Results as CSV",
                                data=csv_data,
                                file_name=(
                                    "sales_ai_result.csv"
                                ),
                                mime="text/csv"
                            )


                    elif generated_sql and sql_error_message:

                        st.warning(
                            "⚠️ Cortex Analyst generated SQL, "
                            "but the SQL could not be executed."
                        )

                        st.error(
                            sql_error_message
                        )


                    # ========================================================
                    # GENERATED SQL
                    # ========================================================

                    if generated_sql:

                        with st.expander(
                            "🔍 View Generated SQL"
                        ):

                            st.code(
                                generated_sql,
                                language="sql"
                            )


                    # ========================================================
                    # TECHNICAL DETAILS
                    # ========================================================

                    with st.expander(
                        "🔧 Technical Details"
                    ):

                        tech_col1, tech_col2 = st.columns(2)


                        with tech_col1:

                            st.write(
                                "**Request ID**"
                            )

                            st.code(
                                safe_string(
                                    request_id
                                )
                                if request_id
                                else "Not returned"
                            )


                            st.write(
                                "**Semantic View**"
                            )

                            st.code(
                                SEMANTIC_VIEW
                            )


                        with tech_col2:

                            st.write(
                                "**Execution Status**"
                            )

                            if sql_success:

                                st.success(
                                    "SQL executed successfully"
                                )

                            elif generated_sql:

                                st.error(
                                    "SQL execution failed"
                                )

                            else:

                                st.info(
                                    "No SQL returned"
                                )


                            if execution_seconds is not None:

                                st.write(
                                    f"**Execution Time:** "
                                    f"{execution_seconds:.2f} seconds"
                                )


                    # ========================================================
                    # FEEDBACK
                    # ========================================================

                    st.divider()

                    st.write(
                        "Was this answer helpful?"
                    )


                    feedback_col1, feedback_col2, feedback_col3 = (
                        st.columns([1, 1, 8])
                    )


                    with feedback_col1:

                        if st.button(
                            "👍 Yes",
                            key=(
                                f"feedback_yes_"
                                f"{datetime.now().timestamp()}"
                            )
                        ):

                            log_feedback(
                                user_question,
                                "POSITIVE"
                            )

                            st.success(
                                "Thank you!"
                            )


                    with feedback_col2:

                        if st.button(
                            "👎 No",
                            key=(
                                f"feedback_no_"
                                f"{datetime.now().timestamp()}"
                            )
                        ):

                            log_feedback(
                                user_question,
                                "NEGATIVE"
                            )

                            st.info(
                                "Feedback recorded."
                            )


                    # ========================================================
                    # FOLLOW-UP SUGGESTIONS
                    # ========================================================

                    if suggestions:

                        st.markdown(
                            "### 💡 Continue Analysis"
                        )

                        suggestion_cols = st.columns(
                            min(
                                3,
                                len(suggestions)
                            )
                        )

                        for index, suggestion in enumerate(
                            suggestions
                        ):

                            with suggestion_cols[
                                index % len(suggestion_cols)
                            ]:

                                if st.button(
                                    suggestion,
                                    key=(
                                        f"suggestion_"
                                        f"{index}_"
                                        f"{len(st.session_state.messages)}"
                                    ),
                                    use_container_width=True
                                ):

                                    st.session_state.next_question = (
                                        suggestion
                                    )

                                    st.rerun()


                    # ========================================================
                    # COMMON AI ACTIONS
                    # ========================================================

                    st.markdown(
                        "### 🔎 Investigate Further"
                    )


                    action_cols = st.columns(3)


                    with action_cols[0]:

                        if st.button(
                            "Why?",
                            use_container_width=True
                        ):

                            st.session_state.next_question = (
                                "Explain the main reasons behind "
                                "the result above. Break the analysis "
                                "down by the most important business "
                                "dimensions."
                            )

                            st.rerun()


                    with action_cols[1]:

                        if st.button(
                            "Compare",
                            use_container_width=True
                        ):

                            st.session_state.next_question = (
                                "Compare this result against the "
                                "previous period and explain the "
                                "largest positive and negative changes."
                            )

                            st.rerun()


                    with action_cols[2]:

                        if st.button(
                            "Top Drivers",
                            use_container_width=True
                        ):

                            st.session_state.next_question = (
                                "Identify the top factors, customers, "
                                "products, regions or sales representatives "
                                "driving this result."
                            )

                            st.rerun()


                    # ========================================================
                    # ADD ASSISTANT RESPONSE TO CONVERSATION
                    # ========================================================

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response_text
                        }
                    )


                    # ========================================================
                    # LOG QUERY
                    # ========================================================

                    log_query(
                        question=user_question,
                        response=response_text,
                        generated_sql=generated_sql,
                        request_id=request_id,
                        execution_seconds=execution_seconds,
                        rows_returned=(
                            len(df)
                            if df is not None
                            else 0
                        ),
                        execution_status=(
                            "SUCCESS"
                            if sql_success
                            else "FAILED"
                        ),
                        error_message=sql_error_message
                    )


                except Exception as e:

                    error_message = str(
                        e
                    )

                    st.session_state.last_error = (
                        error_message
                    )

                    st.error(
                        "❌ Unable to process your request."
                    )

                    st.error(
                        error_message
                    )

                    # --------------------------------------------------------
                    # Log failed AI request
                    # --------------------------------------------------------

                    log_query(
                        question=user_question,
                        response="",
                        generated_sql=None,
                        request_id=None,
                        execution_seconds=None,
                        rows_returned=0,
                        execution_status="FAILED",
                        error_message=error_message
                    )


    # -------------------------------------------------------------------------
    # Handle suggested next question
    # -------------------------------------------------------------------------

    if "next_question" in st.session_state:

        next_question = (
            st.session_state.pop(
                "next_question"
            )
        )

        # Put the suggested question into the chat flow.
        # Streamlit chat_input cannot be programmatically populated directly,
        # so we show it as a prompt for the next interaction.

        st.info(
            f"Suggested follow-up: **{next_question}**"
        )


# =============================================================================
# TAB 3 - QUERY HISTORY
# =============================================================================

with tab_history:

    st.header("📈 Query History")

    st.caption(
        "Recent questions submitted through Sales AI."
    )


    try:

        history_query = f"""
            SELECT
                QUERY_TIMESTAMP,
                USER_NAME,
                USER_QUESTION,
                RESPONSE,
                SEMANTIC_MODEL_NAME
            FROM ANALYST_QUERY_LOG
            WHERE USER_QUESTION IS NOT NULL
            ORDER BY QUERY_TIMESTAMP DESC
            LIMIT {QUERY_HISTORY_LIMIT}
        """


        history_df = session.sql(
            history_query
        ).to_pandas()


        if history_df.empty:

            st.info(
                "📭 No queries logged yet."
            )

        else:

            # ---------------------------------------------------------------
            # Statistics
            # ---------------------------------------------------------------

            col1, col2, col3 = st.columns(3)


            with col1:

                st.metric(
                    "Queries",
                    f"{len(history_df):,}"
                )


            with col2:

                st.metric(
                    "Unique Users",
                    history_df[
                        "USER_NAME"
                    ].nunique()
                )


            with col3:

                latest_timestamp = (
                    str(
                        history_df[
                            "QUERY_TIMESTAMP"
                        ].iloc[0]
                    )[:19]
                )

                st.metric(
                    "Latest Query",
                    latest_timestamp
                )


            st.divider()


            # ---------------------------------------------------------------
            # Search history
            # ---------------------------------------------------------------

            history_search = st.text_input(
                "🔎 Search questions",
                placeholder=(
                    "Search by question..."
                )
            )


            display_df = history_df.copy()


            if history_search:

                mask = (
                    display_df[
                        "USER_QUESTION"
                    ]
                    .astype(str)
                    .str.contains(
                        history_search,
                        case=False,
                        na=False
                    )
                )

                display_df = display_df[
                    mask
                ]


            st.dataframe(
                display_df[
                    [
                        "QUERY_TIMESTAMP",
                        "USER_NAME",
                        "USER_QUESTION",
                        "RESPONSE"
                    ]
                ],
                use_container_width=True,
                height=500
            )


    except Exception as e:

        st.error(
            f"❌ Error fetching query history: {str(e)}"
        )


# =============================================================================
# TAB 4 - SAMPLE QUESTIONS
# =============================================================================

with tab_samples:

    st.header("📚 Business Questions")

    st.caption(
        "Examples designed for sales executives, managers and leadership."
    )


    sample_categories = {

        "💰 Revenue": [

            "What is total revenue this year?",

            "Show revenue by month for the current year.",

            "How does revenue compare with last year?",

            "Which regions are driving revenue growth?",

            "Why did revenue decline last month?"

        ],


        "👥 Sales Team": [

            "Which sales reps are exceeding quota?",

            "Which sales reps are below 80% quota attainment?",

            "Rank sales reps by revenue.",

            "Which reps have the highest growth?",

            "Which territories are underperforming?"

        ],


        "👤 Customers": [

            "Show the top 10 customers by revenue.",

            "Which customers have declining revenue?",

            "Which customers have the highest lifetime value?",

            "Which high-value customers are at risk?",

            "Which customers have not purchased recently?"

        ],


        "📦 Products": [

            "Which products have the highest revenue?",

            "Which products are growing fastest?",

            "Which products have declining sales?",

            "Show revenue by product category.",

            "Which products contribute most to revenue?"

        ],


        "🌎 Regions": [

            "Show revenue by region.",

            "Which region has the highest growth?",

            "Which territories are underperforming?",

            "Compare regional performance.",

            "Which regions are below target?"

        ],


        "📊 Management": [

            "What are the biggest business risks?",

            "What are the top revenue drivers?",

            "Where are we missing quota?",

            "What changed compared with last month?",

            "Summarize sales performance for leadership."

        ]

    }


    categories = list(
        sample_categories.items()
    )


    cols = st.columns(2)


    for index, category_data in enumerate(
        categories
    ):

        category, questions = category_data

        with cols[index % 2]:

            with st.expander(
                category,
                expanded=False
            ):

                for question in questions:

                    st.write(
                        f"• {question}"
                    )


# =============================================================================
# TAB 5 - ABOUT
# =============================================================================

with tab_about:

    st.header("ℹ️ About Sales Intelligence")


    st.markdown(
        """
        ### 🤖 AI-Powered Sales Analytics

        Sales Intelligence combines Snowflake data, a governed semantic
        model and Cortex Analyst to allow business users to ask questions
        about sales data using natural language.

        ### Business Users

        **Sales Executives**

        - Revenue performance
        - Quota attainment
        - Customer performance
        - Territory analysis

        **Sales Managers**

        - Rep performance
        - Regional performance
        - Customer risk
        - Product performance

        **Leadership**

        - Revenue trends
        - Growth
        - Business risks
        - Top revenue drivers

        ### 🔐 Security

        The application is designed for read-only analytics.

        Generated SQL is validated before execution and destructive SQL
        operations are blocked.

        ### 🧠 AI Governance

        User questions and AI responses are logged for operational monitoring,
        troubleshooting and future AI quality improvement.
        """
    )


    st.divider()


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Platform",
            "Snowflake"
        )


    with col2:

        st.metric(
            "AI",
            "Cortex Analyst"
        )


    with col3:

        st.metric(
            "Semantic Model",
            "Sales"
        )


    with col4:

        st.metric(
            "Mode",
            "Read Only"
        )


    st.divider()


    st.subheader(
        "Technical Configuration"
    )


    st.code(
        f"""
Application:
    {APPLICATION_NAME}

Semantic View:
    {SEMANTIC_VIEW}

Maximum Result Rows:
    {MAX_RESULT_ROWS}

Query History:
    {QUERY_HISTORY_LIMIT} records

Execution:
    Snowpark
        """,
        language="text"
    )


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")

st.markdown(
    """
    <div style="
        text-align: center;
        color: #777777;
        font-size: 0.8rem;
    ">
        <p>
            🔒 Sales Intelligence | Governed Snowflake Analytics
        </p>

        <p>
            Powered by Snowflake Cortex Analyst
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
