"""
Snowflake Cortex Analyst - Streamlit UI
=========================================
Production-ready Streamlit application for Cortex Analyst.

Integration with:
- SALES_DATA.PUBLIC.SALES_SEMANTIC_MODEL
- ANALYST_QUERY_LOG table
- Existing semantic layer

Author: Mounika Bethu
"""

import streamlit as st
import snowflake.connector
from snowflake.connector.errors import ProgrammingError, DatabaseError
import pandas as pd
from datetime import datetime
import json
import os
from typing import Optional, Tuple

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Sales Analytics - Cortex Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================

st.markdown("""
    <style>
    .main {
        padding-top: 1.5rem;
    }
    .stTabs [role="tab"] {
        font-size: 1.05em;
        font-weight: 500;
    }
    .response-box {
        background: linear-gradient(135deg, #f0f7ff 0%, #e8f4f8 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 4px solid #0066cc;
        margin: 1rem 0;
        font-size: 0.95em;
        line-height: 1.6;
    }
    .metric-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
    .error-box {
        background-color: #fff3cd;
        border-left: 4px solid #ff6b6b;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'snowflake_connection' not in st.session_state:
    st.session_state.snowflake_connection = None

if 'is_connected' not in st.session_state:
    st.session_state.is_connected = False

if 'query_count' not in st.session_state:
    st.session_state.query_count = 0

# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

SEMANTIC_MODEL = "SALES_DATA.PUBLIC.SALES_SEMANTIC_MODEL"
QUERY_LOG_TABLE = "SALES_DATA.PUBLIC.ANALYST_QUERY_LOG"
AUDIT_TASK_NAME = "SALES_DATA.PUBLIC.CAPTURE_ANALYST_QUERIES_TASK"

# ============================================================================
# SIDEBAR - CONNECTION CONFIGURATION
# ============================================================================

st.sidebar.header("⚙️ Configuration")

with st.sidebar:
    st.subheader("Snowflake Connection")
    
    # Get credentials from secrets or input
    account = st.text_input(
        "Account",
        value=st.secrets.get("snowflake_account", ""),
        type="password",
        help="e.g., xy12345.us-east-1"
    )
    
    user = st.text_input(
        "User",
        value=st.secrets.get("snowflake_user", ""),
        help="Your Snowflake username"
    )
    
    password = st.text_input(
        "Password",
        value=st.secrets.get("snowflake_password", ""),
        type="password",
        help="Your Snowflake password"
    )
    
    database = st.selectbox(
        "Database",
        ["SALES_DATA"],
        disabled=True
    )
    
    schema = st.selectbox(
        "Schema",
        ["PUBLIC"],
        disabled=True
    )
    
    warehouse = st.selectbox(
        "Warehouse",
        ["COMPUTE_WH"],
        disabled=True
    )
    
    st.divider()
    connect_button = st.button(
        "🔌 Connect to Snowflake",
        use_container_width=True,
        type="primary"
    )

# ============================================================================
# CONNECTION LOGIC
# ============================================================================

def connect_to_snowflake() -> Optional[snowflake.connector.SnowflakeConnection]:
    """
    Establish connection to Snowflake.
    
    Returns:
        SnowflakeConnection object or None if failed
    """
    try:
        conn = snowflake.connector.connect(
            account=account,
            user=user,
            password=password,
            database=database,
            schema=schema,
            warehouse=warehouse
        )
        return conn
    except DatabaseError as e:
        st.error(f"❌ Database Error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)}")
        return None


if connect_button:
    if not all([account, user, password]):
        st.error("❌ Please fill in all connection fields")
    else:
        with st.spinner("🔄 Connecting to Snowflake..."):
            conn = connect_to_snowflake()
            if conn:
                st.session_state.snowflake_connection = conn
                st.session_state.is_connected = True
                st.success("✅ Connected successfully!")
                st.balloons()
            else:
                st.session_state.is_connected = False

# ============================================================================
# MAIN INTERFACE
# ============================================================================

st.title("📊 Sales Analytics")
st.markdown("Ask natural language questions about your sales data")

# Check if connected
if not st.session_state.is_connected or st.session_state.snowflake_connection is None:
    st.warning("⚠️ Please connect to Snowflake in the sidebar")
    st.stop()

# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Ask Analyst",
    "📈 Query History",
    "📚 Sample Questions",
    "ℹ️ About"
])

# ============================================================================
# TAB 1: ASK ANALYST
# ============================================================================

with tab1:
    st.header("Ask Your Question")
    st.markdown("Get instant insights from your sales data using natural language")
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_question = st.text_area(
            "What would you like to know?",
            placeholder="Examples:\n• How many customers do we have?\n• Which sales reps are exceeding quota?\n• Show top 10 customers by revenue\n• Which products have low inventory?",
            height=120,
            label_visibility="collapsed"
        )
    
    with col2:
        st.write("")
        st.write("")
        st.write("")
        ask_button = st.button(
            "🚀 Ask",
            use_container_width=True,
            type="primary"
        )
    
    # ========================================================================
    # PROCESS QUESTION
    # ========================================================================
    
    if ask_button and user_question:
        st.markdown("---")
        
        with st.spinner("🤔 Analyzing your question..."):
            try:
                cursor = st.session_state.snowflake_connection.cursor()
                
                # Clean question for SQL
                escaped_question = user_question.replace("'", "''")
                
                # Call Cortex Analyst
                query = f"""
                SELECT SNOWFLAKE.CORTEX.ANALYST(
                    '{escaped_question}',
                    '{SEMANTIC_MODEL}'
                ) AS response
                """
                
                # Execute and get response
                cursor.execute(query)
                result = cursor.fetchone()
                response = result[0] if result else "No response received"
                
                # Store in session for logging
                st.session_state.last_question = user_question
                st.session_state.last_response = response
                
                # Display response
                st.markdown("### Response:")
                st.markdown(f"""
                <div class="response-box">
                {response}
                </div>
                """, unsafe_allow_html=True)
                
                # Display metadata
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Status", "✅ Success")
                
                with col2:
                    st.metric("Timestamp", datetime.now().strftime("%H:%M:%S"))
                
                with col3:
                    st.metric("Model", "ANALYST")
                
                with col4:
                    st.metric("Database", "SALES_DATA")
                
                # Log to audit table
                try:
                    log_cursor = st.session_state.snowflake_connection.cursor()
                    
                    insert_query = f"""
                    INSERT INTO {QUERY_LOG_TABLE}
                    (QUERY_TIMESTAMP, USER_NAME, USER_QUESTION, RESPONSE, SEMANTIC_MODEL_NAME)
                    VALUES
                    (CURRENT_TIMESTAMP(), CURRENT_USER(), %s, %s, '{SEMANTIC_MODEL.split('.')[-1]}')
                    """
                    
                    log_cursor.execute(insert_query, (user_question, response))
                    st.session_state.snowflake_connection.commit()
                    log_cursor.close()
                    
                    st.session_state.query_count += 1
                    
                except Exception as log_error:
                    st.warning(f"⚠️ Query answered but logging failed: {str(log_error)}")
                
                cursor.close()
                
            except ProgrammingError as e:
                st.error(f"❌ Query Error: {str(e)}")
                st.info("💡 Try rephrasing your question or check the data availability")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 2: QUERY HISTORY
# ============================================================================

with tab2:
    st.header("Recent Queries")
    st.markdown("View all questions asked and responses received")
    
    try:
        hist_cursor = st.session_state.snowflake_connection.cursor()
        
        # Get recent queries
        hist_query = f"""
        SELECT 
            QUERY_TIMESTAMP,
            USER_NAME,
            USER_QUESTION,
            RESPONSE,
            SEMANTIC_MODEL_NAME
        FROM {QUERY_LOG_TABLE}
        WHERE USER_QUESTION IS NOT NULL
        ORDER BY QUERY_TIMESTAMP DESC
        LIMIT 50
        """
        
        hist_cursor.execute(hist_query)
        rows = hist_cursor.fetchall()
        
        if rows:
            # Convert to DataFrame
            df = pd.DataFrame(
                rows,
                columns=['Timestamp', 'User', 'Question', 'Response', 'Model']
            )
            
            # Display stats
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Queries", len(df))
            
            with col2:
                unique_users = df['User'].nunique()
                st.metric("Unique Users", unique_users)
            
            with col3:
                latest = df['Timestamp'].iloc[0].strftime("%Y-%m-%d %H:%M:%S") if len(df) > 0 else "N/A"
                st.metric("Latest Query", latest)
            
            st.divider()
            
            # Display table
            st.subheader("Query Log")
            
            # Make response column narrower
            df_display = df.copy()
            df_display['Response'] = df_display['Response'].str[:100] + "..."
            
            st.dataframe(
                df_display,
                use_container_width=True,
                height=400,
                hide_index=True
            )
            
            # Expandable details
            with st.expander("📋 View Full Responses"):
                for idx, row in df.iterrows():
                    with st.expander(f"{row['Timestamp']} - {row['User']}"):
                        st.markdown(f"**Question:** {row['Question']}")
                        st.markdown(f"**Response:**\n{row['Response']}")
        
        else:
            st.info("📭 No queries logged yet. Ask a question in the 'Ask Analyst' tab!")
        
        hist_cursor.close()
        
    except Exception as e:
        st.error(f"❌ Error fetching history: {str(e)}")

# ============================================================================
# TAB 3: SAMPLE QUESTIONS
# ============================================================================

with tab3:
    st.header("📚 Sample Questions")
    st.markdown("Get inspired - see what you can ask")
    
    # Sample questions organized by category
    samples = {
        "👥 Customer Analysis": {
            "questions": [
                "How many customers do we have?",
                "Show me the top 10 customers by revenue",
                "Which customers have high churn risk?",
                "What is the average customer lifetime value?",
                "How many customers are in each industry?"
            ],
            "emoji": "👥"
        },
        "📈 Sales Performance": {
            "questions": [
                "Which sales reps are exceeding quota?",
                "Show me sales by rep for this month",
                "Which sales reps are underperforming?",
                "What is the average deal size?",
                "Show quota attainment by region"
            ],
            "emoji": "📈"
        },
        "📦 Product Analysis": {
            "questions": [
                "Which products have the highest revenue?",
                "Show me products with low inventory",
                "What are the top-selling products?",
                "Show me products by category",
                "Which products are trending?"
            ],
            "emoji": "📦"
        },
        "💰 Business Metrics": {
            "questions": [
                "What is total revenue this year?",
                "Show me revenue trends over time",
                "What is the average order value?",
                "How many orders do we have?",
                "Show me sales by channel"
            ],
            "emoji": "💰"
        },
        "⚠️ Risk & Alerts": {
            "questions": [
                "Which customers have high churn risk?",
                "Show me inventory alerts",
                "List products below reorder level",
                "Which reps are at risk of missing quota?",
                "What is our pipeline status?"
            ],
            "emoji": "⚠️"
        }
    }
    
    col1, col2 = st.columns(2)
    
    col_idx = 0
    for category, data in samples.items():
        col = col1 if col_idx % 2 == 0 else col2
        
        with col:
            with st.expander(f"{data['emoji']} {category}", expanded=False):
                for i, question in enumerate(data['questions'], 1):
                    if st.button(
                        f"{i}. {question}",
                        key=f"sample_{category}_{i}",
                        use_container_width=True
                    ):
                        st.session_state.selected_sample = question
                        st.switch_to_form("Ask Analyst")
        
        col_idx += 1
    
    st.divider()
    
    st.markdown("""
    ### 💡 Tips for Better Results
    
    - **Be specific**: Instead of "Show customers", try "Show top 10 customers by revenue"
    - **Use timeframes**: Ask about "this month", "last quarter", "2024"
    - **Request rankings**: Use "top 5", "bottom 10", "highest", "lowest"
    - **Add filters**: Try "by region", "by industry", "by status"
    - **Ask for aggregations**: "total", "average", "count", "sum"
    """)

# ============================================================================
# TAB 4: ABOUT
# ============================================================================

with tab4:
    st.header("ℹ️ About This Application")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 Features")
        st.markdown("""
        - **Natural Language Queries**: Ask questions in plain English
        - **Instant Responses**: Get answers within seconds
        - **Automatic Logging**: All queries logged for audit
        - **Query History**: Access past questions and responses
        - **Sample Questions**: Get inspired with pre-built examples
        """)
    
    with col2:
        st.subheader("📊 Data Sources")
        st.markdown(f"""
        - **Database**: SALES_DATA
        - **Schema**: PUBLIC
        - **Semantic Model**: SALES_SEMANTIC_MODEL
        - **Tables**: 13+ business tables
        - **Metrics**: 50+ pre-built metrics
        """)
    
    st.divider()
    
    st.subheader("🔧 Technical Details")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Status", "✅ Online")
    
    with col2:
        st.metric("Analyst", "Cortex")
    
    with col3:
        st.metric("Queries Today", st.session_state.query_count)
    
    st.divider()
    
    st.subheader("📋 Available Tables")
    
    available_tables = [
        "CUSTOMERS", "PRODUCTS", "SALES_REPS", "ORDERS",
        "ORDER_ITEMS", "CUSTOMER_SEGMENTS", "PRODUCT_INVENTORY",
        "CUSTOMER_LIFETIME_VALUE", "SALES_PERFORMANCE",
        "REP_TERRITORIES", "PRODUCT_DEMAND_FREQUENCY",
        "MONTHLY_SALES_TRENDS", "DEMAND_FORECAST"
    ]
    
    cols = st.columns(4)
    for idx, table in enumerate(available_tables):
        with cols[idx % 4]:
            st.caption(f"📌 {table}")
    
    st.divider()
    
    st.markdown("""
    **Built with Streamlit + Snowflake Cortex Analyst**
    
    All interactions are logged and secured. For support, contact your data team.
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.85em;">
    <p>🔒 All queries are automatically logged for audit and compliance</p>
    <p>Powered by Snowflake Cortex Analyst</p>
</div>
""", unsafe_allow_html=True)