import os
import pandas as pd
import numpy as np


# ---------------------------------------------------------
# Excel Configuration
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

EXCEL_FILES = {
    "employees": os.path.join(
        BASE_DIR,
        "data",
        "employees.xlsx"
    )
}


# ---------------------------------------------------------
# Get Excel File Information
# ---------------------------------------------------------

def get_excel_info() -> str:
    """
    Return schema information for all registered Excel files.
    """

    parts = []

    for name, path in EXCEL_FILES.items():

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Excel file not found: {path}"
            )

        df_sample = pd.read_excel(
            path,
            nrows=3
        )

        df_full = pd.read_excel(path)

        cols = ", ".join(
            [
                f"{c} ({df_sample[c].dtype})"
                for c in df_sample.columns
            ]
        )

        parts.append(
            f"Excel file: {name}\n"
            f"  Path: {path}\n"
            f"  Columns: {cols}\n"
            f"  Shape: {df_full.shape}\n"
            f"  Sample:\n"
            f"{df_sample.head(2).to_string(index=False)}"
        )

    return "\n\n".join(parts)


# ---------------------------------------------------------
# Query Excel File
# ---------------------------------------------------------

def query_excel(
    file_key: str,
    pandas_code: str
) -> pd.DataFrame:
    """
    Load an Excel file and run a Pandas expression.
    """

    if file_key not in EXCEL_FILES:

        raise ValueError(
            f"Unknown Excel file: {file_key}. "
            f"Available: {list(EXCEL_FILES.keys())}"
        )

    df = pd.read_excel(
        EXCEL_FILES[file_key]
    )

    # Allowed objects for the expression
    local_vars = {
        "df": df,
        "pd": pd,
        "np": np
    }

    # Execute expression
    try:

        exec(
            f"result = {pandas_code}",
            {},
            local_vars
        )

    except Exception as e:

        raise RuntimeError(
            f"Excel query failed: {e}"
        )

    result = local_vars["result"]

    # Convert Series to DataFrame
    if isinstance(result, pd.Series):

        result = result.to_frame()

    # Convert scalar result to DataFrame
    elif not isinstance(result, pd.DataFrame):

        result = pd.DataFrame(
            {
                "result": [result]
            }
        )

    return result


# ---------------------------------------------------------
# Test
# ---------------------------------------------------------

if __name__ == "__main__":

    print("\n=== EXCEL INFORMATION ===\n")

    print(
        get_excel_info()
    )

    print("\n=== TEST QUERY ===\n")

    result = query_excel(
        "employees",
        "df.groupby('department')['salary'].mean().round(2)"
    )

    print(
        result.to_string()
    )
