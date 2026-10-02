# ============================================================
# AI DATA ANALYST - STREAMLIT CHAT APPLICATION
# ============================================================

import sys

# ------------------------------------------------------------
# Windows UTF-8 configuration
# Prevents cp1252 UnicodeEncodeError in Windows console
# ------------------------------------------------------------

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

except Exception:
    pass


# ============================================================
# IMPORTS
# ============================================================

import streamlit as st
import pandas as pd

import os
import subprocess
import sys

# Create sample data files if they don't exist
required_files = [
    "data/sales.db",
    "data/employees.xlsx",
    "data/web_analytics.csv",
]

if not all(os.path.exists(file) for file in required_files):
    subprocess.run(
        [sys.executable, "create_data.py"],
        check=True
    )

from agent import agent
from visualization.charts import generate_chart


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="bar_chart",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #666666;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    .source-box {
        padding: 10px;
        border-radius: 8px;
        background-color: #f5f7fa;
        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">AI Data Analyst</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Ask questions about your SQL, Excel, and CSV data.'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Data Sources")

    st.write("The AI analyst can query:")

    st.write("1. SQLite database")
    st.write("2. Excel files")
    st.write("3. CSV files")

    st.divider()

    st.header("Example Questions")

    example_questions = [
        "Which region generated the highest revenue?",
        "Which department has the highest average salary?",
        "Which website channel generated the most conversions?",
        "Show revenue by region.",
        "Show conversions by channel.",
        "Show average salary by department.",
    ]

    for question in example_questions:

        if st.button(
            question,
            use_container_width=True,
        ):
            st.session_state["selected_question"] = question


# ============================================================
# DISPLAY EXISTING CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    role = message.get("role", "assistant")

    with st.chat_message(role):

        content = message.get("content", "")

        if content:
            st.markdown(content)

        # Display chart if available
        chart = message.get("chart")

        if chart is not None:

            st.plotly_chart(
                chart,
                use_container_width=True,
            )

        # Display result data if available
        data = message.get("data")

        if isinstance(data, pd.DataFrame) and not data.empty:

            with st.expander("View Data"):

                st.dataframe(
                    data,
                    use_container_width=True,
                )


# ============================================================
# GET USER QUESTION
# ============================================================

selected_question = st.session_state.pop(
    "selected_question",
    None,
)

chat_question = st.chat_input(
    "Ask a question about your data..."
)

if selected_question:
    question = selected_question
else:
    question = chat_question


# ============================================================
# PROCESS USER QUESTION
# ============================================================

if question:

    # --------------------------------------------------------
    # Add user message to chat history
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
            "chart": None,
            "data": None,
        }
    )

    # --------------------------------------------------------
    # Display user message
    # --------------------------------------------------------

    with st.chat_message("user"):
        st.markdown(question)

    # --------------------------------------------------------
    # AI RESPONSE
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        try:

            with st.spinner("Analyzing your data..."):

                result = agent.ask(question)

            # =================================================
            # ERROR FROM AGENT
            # =================================================

            if not result.get("success", False):

                error_message = (
                    "I could not complete the analysis.\n\n"
                    f"Error: {result.get('error', 'Unknown error')}"
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                        "chart": None,
                        "data": None,
                    }
                )

            # =================================================
            # SUCCESS
            # =================================================

            else:

                # ------------------------------------------------
                # Final natural-language answer
                # ------------------------------------------------

                explanation = result.get(
                    "explanation",
                    "Analysis completed.",
                )

                st.markdown(explanation)

                # ------------------------------------------------
                # Get agent plan
                # ------------------------------------------------

                plan = result.get("plan", {})

                source_type = plan.get(
                    "source_type",
                    "unknown",
                )

                file_key = plan.get(
                    "file_key",
                    "",
                )

                query = plan.get(
                    "query",
                    "",
                )

                chart_type = plan.get(
                    "chart_type",
                    "none",
                )

                chart_x = plan.get(
                    "chart_x",
                    "",
                )

                chart_y = plan.get(
                    "chart_y",
                    "",
                )

                chart_title = plan.get(
                    "chart_title",
                    "",
                )

                # ------------------------------------------------
                # Analysis details
                # ------------------------------------------------

                with st.expander("Analysis Details"):

                    st.write(
                        "Data Source:",
                        source_type,
                    )

                    if file_key:

                        st.write(
                            "File:",
                            file_key,
                        )

                    st.write("Query:")

                    if source_type == "sql":

                        st.code(
                            query,
                            language="sql",
                        )

                    else:

                        st.code(
                            query,
                            language="python",
                        )

                    st.write(
                        "Chart Type:",
                        chart_type,
                    )

                    if chart_type != "none":

                        st.write(
                            "Chart X:",
                            chart_x,
                        )

                        st.write(
                            "Chart Y:",
                            chart_y,
                        )

                        st.write(
                            "Chart Title:",
                            chart_title,
                        )

                # ------------------------------------------------
                # Generate Plotly visualization
                # ------------------------------------------------

                chart = None

                try:

                    chart = generate_chart(result)

                except Exception as chart_error:

                    st.warning(
                        "The data analysis completed, "
                        "but the chart could not be generated."
                    )

                    # Console output is ASCII-only
                    print(
                        "Chart generation error:",
                        str(chart_error),
                    )

                # ------------------------------------------------
                # Display chart
                # ------------------------------------------------

                if chart is not None:

                    st.plotly_chart(
                        chart,
                        use_container_width=True,
                    )

                # ------------------------------------------------
                # Display result data
                # ------------------------------------------------

                result_df = result.get("data")

                if (
                    isinstance(result_df, pd.DataFrame)
                    and not result_df.empty
                ):

                    with st.expander("View Data"):

                        st.dataframe(
                            result_df,
                            use_container_width=True,
                        )

                # ------------------------------------------------
                # Save assistant response
                # ------------------------------------------------

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": explanation,
                        "chart": chart,
                        "data": result_df,
                    }
                )

        # ========================================================
        # UNEXPECTED ERROR
        # ========================================================

        except Exception as e:

            error_message = (
                "An unexpected error occurred.\n\n"
                f"Error: {str(e)}"
            )

            st.error(error_message)

            # ASCII-only console output
            print(
                "Streamlit application error:",
                str(e),
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": error_message,
                    "chart": None,
                    "data": None,
                }
            )
