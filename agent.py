import json
import re
import traceback
import pandas as pd

from langchain_ollama import ChatOllama

from tools.sql_tool import (
    get_sql_schema,
    run_sql_query,
    sql_engine,
)

from tools.excel_tool import (
    get_excel_info,
    query_excel,
    EXCEL_FILES,
)

from tools.csv_tool import (
    get_csv_info,
    query_csv,
    CSV_FILES,
)


# =========================================================
# Llama 3 Configuration
# =========================================================

from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3:latest",
    temperature=0,
)


# =========================================================
# Data Metrics Agent
# =========================================================

class DataMetricsAgent:
    """
    AI agent that routes natural-language questions
    to the correct data source.
    """

    def __init__(
        self,
        llm,
        sql_engine,
        excel_files: dict,
        csv_files: dict,
    ):

        self.llm = llm
        self.sql_engine = sql_engine
        self.excel_files = excel_files
        self.csv_files = csv_files

        self.conversation_history = []

        # Pre-load schema information
        self.schema_context = self._build_schema_context()

    # -----------------------------------------------------
    # Build Schema Context
    # -----------------------------------------------------

    def _build_schema_context(self) -> str:
        """
        Build a description of all available data sources.
        """

        parts = [
            "=== AVAILABLE DATA SOURCES ==="
        ]

        # SQL
        parts.append(
            "\n--- SQL DATABASE (source_type: sql) ---"
        )

        parts.append(
            get_sql_schema()
        )

        # Excel
        parts.append(
            "\n--- EXCEL FILES (source_type: excel) ---"
        )

        parts.append(
            get_excel_info()
        )

        # CSV
        parts.append(
            "\n--- CSV FILES (source_type: csv) ---"
        )

        parts.append(
            get_csv_info()
        )

        return "\n".join(parts)

    # -----------------------------------------------------
    # Routing Prompt
    # -----------------------------------------------------

    def _get_routing_prompt(
        self,
        question: str
    ) -> str:
        """
        Create the prompt used by Llama 3 to decide
        which data source should be used.
        """

        history_text = ""

        if self.conversation_history:

            recent = self.conversation_history[-6:]

            history_text = (
                "\n--- Recent conversation ---\n"
            )

            for h in recent:

                history_text += (
                    f"{h['role'].upper()}: "
                    f"{h['content']}\n"
                )

        return f"""
You are a data analytics agent.

Given the user's question and the available data
sources below, perform these tasks:

1. Determine which data source should be queried.
2. Write the exact query needed to answer the question.
3. Specify the best chart type for the result.

{self.schema_context}

{history_text}

USER QUESTION:
{question}

Return ONLY valid JSON.

Use exactly this structure:

{{
  "source_type": "sql",
  "file_key": "",
  "query": "",
  "chart_type": "bar",
  "chart_x": "<column name for category or date>",
  "chart_y": "<column name for numeric value>",
  "chart_title": "<descriptive chart title>"
}}

Allowed source_type values:

- sql
- excel
- csv

For SQL:
- Write a valid SQLite SELECT query.
- Do not use INSERT.
- Do not use UPDATE.
- Do not use DELETE.
- Do not use DROP.
- Do not use ALTER.

For Excel and CSV:
- Write a Pandas expression.
- The DataFrame variable is called df.
- Prefer returning a DataFrame rather than a Series.
- When grouping by a category, always keep the category column in the result.
- Do not select a single column before groupby aggregation if doing so would remove the category name.
- For "highest", "lowest", "most", or "least" questions, return the category column and the calculated value.
- Sort the result so the requested highest or lowest value is clear.

Examples:

df.groupby('department', as_index=False).agg(average_salary=('salary', 'mean')).sort_values('average_salary', ascending=False)

df.groupby('channel', as_index=False).agg(total_conversions=('conversions', 'sum')).sort_values('total_conversions', ascending=False)

df[df['salary'] > 100000][['name', 'salary']]

df.describe()

Allowed chart_type values:

- bar
- line
- pie
- table
- none

Chart selection rules:

- Pick the chart type that best fits the result data.

- For categorical comparisons, use "bar".
  - chart_x must be the category column.
  - chart_y must be the numeric value column.

- For time-based data, use "line".
  - chart_x must be the date or time column.
  - chart_y must be the numeric metric column.

- For composition or share-of-total results, use "pie".

Do not include markdown.
Do not include explanations.

JSON response:
"""

    # -----------------------------------------------------
    # Parse LLM JSON
    # -----------------------------------------------------

    def _parse_llm_response(
        self,
        response
    ) -> dict:
        """
        Parse Llama 3's JSON response.
        """

        # ChatOllama returns an AIMessage
        if hasattr(response, "content"):

            response = response.content

        response = str(response).strip()

        # Remove markdown code fences
        response = re.sub(
            r"```json\s*",
            "",
            response,
            flags=re.IGNORECASE,
        )

        response = re.sub(
            r"```\s*",
            "",
            response,
        )

        # Find JSON object
        match = re.search(
            r"\{.*\}",
            response,
            re.DOTALL,
        )

        if not match:

            raise ValueError(
                "Could not find JSON in Llama response:\n"
                + response
            )

        json_text = match.group()

        try:

            return json.loads(
                json_text
            )

        except json.JSONDecodeError as e:

            raise ValueError(
                f"Invalid JSON returned by Llama 3: {e}\n\n"
                f"Response:\n{response}"
            )

    # -----------------------------------------------------
    # Validate Plan
    # -----------------------------------------------------

    def _validate_plan(
        self,
        plan: dict
    ):
        """
        Validate the plan returned by Llama 3.
        """

        required_fields = [
            "source_type",
            "file_key",
            "query",
            "chart_type",
            "chart_x",
            "chart_y",
            "chart_title",
        ]

        for field in required_fields:

            if field not in plan:

                raise ValueError(
                    f"Missing field in LLM plan: {field}"
                )

        allowed_sources = {
            "sql",
            "excel",
            "csv",
        }

        if plan["source_type"] not in allowed_sources:

            raise ValueError(
                f"Invalid source_type: "
                f"{plan['source_type']}"
            )

        allowed_charts = {
            "bar",
            "line",
            "pie",
            "table",
            "none",
        }

        if plan["chart_type"] not in allowed_charts:

            raise ValueError(
                f"Invalid chart_type: "
                f"{plan['chart_type']}"
            )

        if not plan["query"].strip():

            raise ValueError(
                "LLM returned an empty query."
            )

    # -----------------------------------------------------
    # Execute Query
    # -----------------------------------------------------

    def _execute_query(
        self,
        plan: dict
    ) -> pd.DataFrame:

        source = plan["source_type"]
        query = plan["query"]

        # SQL
        if source == "sql":

            return run_sql_query(
                query
            )

        # Excel
        elif source == "excel":

            return query_excel(
                plan["file_key"],
                query,
            )

        # CSV
        elif source == "csv":

            return query_csv(
                plan["file_key"],
                query,
            )

        else:

            raise ValueError(
                f"Unknown source type: {source}"
            )

    # -----------------------------------------------------
    # Generate Explanation
    # -----------------------------------------------------

    def _generate_explanation(
        self,
        question: str,
        result_df: pd.DataFrame,
        plan: dict,
    ) -> str:

        if result_df.empty:

            result_str = (
                "The query returned no results."
            )

        else:

            result_str = result_df.to_string(
                max_rows=20,
                max_cols=10,
                index=False,
            )

        prompt = f"""
You are a helpful data analyst.

Answer the user's question using ONLY
the data result provided below.

User question:
{question}

Data source:
{plan['source_type']}

Query:
{plan['query']}

Data result:
{result_str}

Instructions:

- Give a clear answer.
- Include the important numbers.
- Do not invent information.
- Do not change the numbers.
- Keep the answer concise.
- Use 2 to 4 sentences.
"""

        response = self.llm.invoke(
            prompt
        )

        # ChatOllama returns AIMessage
        if hasattr(response, "content"):

            return response.content.strip()

        return str(response).strip()

    # -----------------------------------------------------
    # Main Agent
    # -----------------------------------------------------

    def ask(
        self,
        question: str
    ) -> dict:
        """
        Process a user question from start to finish.
        """

        self.conversation_history.append(
            {
                "role": "user",
                "content": question,
            }
        )

        try:

            # =============================================
            # Step 1: Ask Llama 3 to route and plan
            # =============================================

            routing_prompt = (
                self._get_routing_prompt(
                    question
                )
            )

            raw_response = self.llm.invoke(
                routing_prompt
            )

            plan = self._parse_llm_response(
                raw_response
            )

            self._validate_plan(
                plan
            )

            # =============================================
            # Step 2: Execute query
            # =============================================

            result_df = self._execute_query(
                plan
            )

            # =============================================
            # Step 3: Generate natural-language answer
            # =============================================

            explanation = (
                self._generate_explanation(
                    question,
                    result_df,
                    plan,
                )
            )

            # =============================================
            # Step 4: Save conversation
            # =============================================

            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": explanation,
                }
            )

            return {
                "success": True,
                "question": question,
                "plan": plan,
                "data": result_df,
                "explanation": explanation,
            }

        except Exception as e:

            error_msg = (
                f"Sorry, I encountered an error: "
                f"{str(e)}"
            )

            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": error_msg,
                }
            )

            return {
                "success": False,
                "question": question,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }


# =========================================================
# Create Agent
# =========================================================

agent = DataMetricsAgent(
    llm=llm,
    sql_engine=sql_engine,
    excel_files=EXCEL_FILES,
    csv_files=CSV_FILES,
)

print(
    "✅ Agent initialized with 3 data sources."
)


# =========================================================
# Test Agent
# =========================================================

if __name__ == "__main__":

    test_questions = [

        "Which region generated the highest revenue?",

        "Show me monthly revenue trends for 2025",

        "How many employees have 'Exceeds' performance?",

        "What is the average bounce rate by channel?",

        "Which department has the highest average salary?",

        "Which website channel generated the most conversions?",
    ]

    for question in test_questions:

        print("\n")
        print("=" * 70)
        print(
            f"QUESTION: {question}"
        )
        print("=" * 70)

        result = agent.ask(
            question
        )

        if result["success"]:

            print("\nSOURCE:")
            print(
                result["plan"]["source_type"]
            )

            if result["plan"]["file_key"]:

                print("\nFILE:")
                print(
                    result["plan"]["file_key"]
                )

            print("\nQUERY:")
            print(
                result["plan"]["query"]
            )

            print("\nCHART:")
            print(
                result["plan"]["chart_type"]
            )

            print("\nRESULT:")

            if result["data"].empty:

                print(
                    "No results returned."
                )

            else:

                print(
                    result["data"].to_string(
                        index=False
                    )
                )

            print("\nFINAL ANSWER:")
            print(
                result["explanation"]
            )

        else:

            print("\n❌ ERROR:")
            print(
                result["error"]
            )

            print("\nTRACEBACK:")
            print(
                result["traceback"]
            )
