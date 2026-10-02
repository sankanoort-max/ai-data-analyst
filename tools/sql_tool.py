import os
import pandas as pd
from sqlalchemy import create_engine, text


# ---------------------------------------------------------
# SQL Database Configuration
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SQL_DB_PATH = os.path.join(
    BASE_DIR,
    "data",
    "sales.db"
)

sql_engine = create_engine(
    f"sqlite:///{SQL_DB_PATH}"
)


# ---------------------------------------------------------
# Get Database Schema
# ---------------------------------------------------------

def get_sql_schema() -> str:
    """
    Return the schema of all tables in the database.
    """

    with sql_engine.connect() as conn:

        tables = conn.execute(
            text(
                "SELECT name "
                "FROM sqlite_master "
                "WHERE type='table'"
            )
        ).fetchall()

        schema_parts = []

        for (table_name,) in tables:

            cols = conn.execute(
                text(
                    f"PRAGMA table_info('{table_name}')"
                )
            ).fetchall()

            col_defs = ", ".join(
                [
                    f"{c[1]} ({c[2]})"
                    for c in cols
                ]
            )

            sample = conn.execute(
                text(
                    f"SELECT * FROM '{table_name}' LIMIT 2"
                )
            ).fetchall()

            schema_parts.append(
                f"Table: {table_name}\n"
                f"  Columns: {col_defs}\n"
                f"  Sample rows: {sample}"
            )

        return "\n\n".join(schema_parts)


# ---------------------------------------------------------
# Execute SQL Query
# ---------------------------------------------------------

def run_sql_query(query: str) -> pd.DataFrame:
    """
    Execute a SQL query and return results as a DataFrame.
    """

    # Only allow SELECT queries
    if not query.strip().lower().startswith("select"):
        raise ValueError(
            "Only SELECT queries are allowed."
        )

    with sql_engine.connect() as conn:

        return pd.read_sql(
            text(query),
            conn
        )


# ---------------------------------------------------------
# Test
# ---------------------------------------------------------

if __name__ == "__main__":

    print("\n=== DATABASE SCHEMA ===\n")

    print(
        get_sql_schema()
    )

    print("\n=== TEST QUERY ===\n")

    query = """
    SELECT
        region,
        ROUND(SUM(revenue), 2) AS total_revenue
    FROM sales
    GROUP BY region
    ORDER BY total_revenue DESC
    """

    result = run_sql_query(query)

    print(
        result.to_string(index=False)
    )
