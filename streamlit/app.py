"""
Cortex Analyst UI - Streamlit in Snowflake
Snowflake native version (uses Snowpark, not connector)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from snowflake.snowpark.context import get_active_session

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
# STYLING
# ============================================================================

st.markdown("""
    <style>
    .response-box {
        background: linear-gradient(135deg, #f0f7ff 0%, #e8f4f8 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 4px solid #0066cc;
        margin: 1rem 0;
        font-size: 0.95em;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# GET SNOWFLAKE SESSION
# ============================================================================

session = get_active_session()

# ============================================================================
# MAIN INTERFACE
# ============================================================================

st.title("📊 Sales Analytics with Cortex Analyst")
st.markdown("Ask natural language questions about your sales data")

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
    
    user_question = st.text_area(
        "What would you like to know?",
        placeholder="Examples:\n• How many customers do we have?\n• Which sales reps are exceeding quota?\n• Show top 10 customers by revenue",
        height=120,
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns([4, 1])
    
    with col2:
        ask_button = st.button("🚀 Ask", use_container_width=True, type="primary")
    
    if ask_button and user_question:
        with st.spinner("🤔 Analyzing your question..."):
            try:
                # Call Cortex Analyst
                query = f"""
                SELECT SNOWFLAKE.CORTEX.ANALYST(
                    '{user_question.replace("'", "''")}',
                    'SALES_DATA.PUBLIC.SALES_SEMANTIC_MODEL'
                ) AS response
                """
                
                result = session.sql(query).collect()
                response = result[0]['RESPONSE'] if result else "No response received"
                
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
                
                # Log the query
                try:
                    insert_query = f"""
                    INSERT INTO ANALYST_QUERY_LOG
                    (QUERY_TIMESTAMP, USER_NAME, USER_QUESTION, RESPONSE, SEMANTIC_MODEL_NAME)
                    VALUES
                    (CURRENT_TIMESTAMP(), CURRENT_USER(), '{user_question.replace("'", "''")}', '{response.replace("'", "''")}', 'SALES_SEMANTIC_MODEL')
                    """
                    session.sql(insert_query).collect()
                except Exception as log_error:
                    st.warning(f"⚠️ Query answered but logging failed: {str(log_error)}")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 2: QUERY HISTORY
# ============================================================================

with tab2:
    st.header("Recent Queries")
    
    try:
        query = """
        SELECT 
            QUERY_TIMESTAMP,
            USER_NAME,
            USER_QUESTION
        FROM ANALYST_QUERY_LOG
        WHERE USER_QUESTION IS NOT NULL
        ORDER BY QUERY_TIMESTAMP DESC
        LIMIT 20
        """
        
        result = session.sql(query).collect()
        
        if result:
            df = pd.DataFrame([dict(row) for row in result])
            
            # Stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Queries", len(df))
            with col2:
                st.metric("Unique Users", df['USER_NAME'].nunique())
            with col3:
                latest = str(df['QUERY_TIMESTAMP'].iloc[0])[:19] if len(df) > 0 else "N/A"
                st.metric("Latest Query", latest)
            
            st.divider()
            st.dataframe(df, use_container_width=True)
        
        else:
            st.info("📭 No queries logged yet. Ask a question in the 'Ask Analyst' tab!")
        
    except Exception as e:
        st.error(f"❌ Error fetching history: {str(e)}")

# ============================================================================
# TAB 3: SAMPLE QUESTIONS
# ============================================================================

with tab3:
    st.header("📚 Sample Questions")
    st.markdown("Get inspired - see what you can ask")
    
    samples = {
        "👥 Customer Analysis": [
            "How many customers do we have?",
            "Show me the top 10 customers by revenue",
            "Which customers have high churn risk?",
            "What is the average customer lifetime value?",
            "Show customers by industry"
        ],
        "📈 Sales Performance": [
            "Which sales reps are exceeding quota?",
            "Show me sales by rep for this month",
            "Which sales reps are underperforming?",
            "What is the average deal size?",
            "Show quota attainment by region"
        ],
        "📦 Product Analysis": [
            "Which products have the highest revenue?",
            "Show me products with low inventory",
            "What are the top-selling products?",
            "Show me products by category",
            "Which products are trending?"
        ],
        "💰 Business Metrics": [
            "What is total revenue this year?",
            "Show me revenue trends over time",
            "What is the average order value?",
            "How many orders do we have?",
            "Show me sales by channel"
        ],
        "⚠️ Risk & Alerts": [
            "Which customers have high churn risk?",
            "Show me inventory alerts",
            "List products below reorder level",
            "Which reps are at risk of missing quota?",
            "Show me high-risk forecasts"
        ]
    }
    
    col1, col2 = st.columns(2)
    col_idx = 0
    
    for category, questions in samples.items():
        col = col1 if col_idx % 2 == 0 else col2
        
        with col:
            with st.expander(f"{category}", expanded=False):
                for i, question in enumerate(questions, 1):
                    st.write(f"{i}. {question}")
        
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
        - **Sample Questions**: Pre-built examples for guidance
        """)
    
    with col2:
        st.subheader("📊 Data Sources")
        st.markdown("""
        - **Database**: SALES_DATA
        - **Schema**: PUBLIC
        - **Semantic Model**: SALES_SEMANTIC_MODEL
        - **Tables**: 13+ business tables
        - **Metrics**: 50+ pre-built metrics
        - **Dimensions**: 54+ attributes
        """)
    
    st.divider()
    
    st.subheader("🔧 Technical Details")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Status", "✅ Online")
    
    with col2:
        st.metric("Analyst", "Cortex")
    
    with col3:
        st.metric("Platform", "Snowflake")
    
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