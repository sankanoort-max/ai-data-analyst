import os
import pandas as pd
import numpy as np


# ---------------------------------------------------------
# CSV Configuration
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

CSV_FILES = {
    "web_analytics": os.path.join(
        BASE_DIR,
        "data",
        "web_analytics.csv"
    )
}


# ---------------------------------------------------------
# Get CSV File Information
# ---------------------------------------------------------

def get_csv_info() -> str:
    """
    Return schema information for all registered CSV files.
    """

    parts = []

    for name, path in CSV_FILES.items():

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"CSV file not found: {path}"
            )

        df_sample = pd.read_csv(
            path,
            nrows=3
        )

        df_full = pd.read_csv(path)

        cols = ", ".join(
            [
                f"{c} ({df_sample[c].dtype})"
                for c in df_sample.columns
            ]
        )

        parts.append(
            f"CSV file: {name}\n"
            f"  Path: {path}\n"
            f"  Columns: {cols}\n"
            f"  Shape: {df_full.shape}\n"
            f"  Sample:\n"
            f"{df_sample.head(2).to_string(index=False)}"
        )

    return "\n\n".join(parts)


# ---------------------------------------------------------
# Query CSV File
# ---------------------------------------------------------

def query_csv(
    file_key: str,
    pandas_code: str
) -> pd.DataFrame:
    """
    Load a CSV file and run a Pandas expression.
    """

    if file_key not in CSV_FILES:

        raise ValueError(
            f"Unknown CSV file: {file_key}. "
            f"Available: {list(CSV_FILES.keys())}"
        )

    df = pd.read_csv(
        CSV_FILES[file_key]
    )

    local_vars = {
        "df": df,
        "pd": pd,
        "np": np
    }

    try:

        exec(
            f"result = {pandas_code}",
            {},
            local_vars
        )

    except Exception as e:

        raise RuntimeError(
            f"CSV query failed: {e}"
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

    print("\n=== CSV INFORMATION ===\n")

    print(
        get_csv_info()
    )

    print("\n=== TEST QUERY ===\n")

    result = query_csv(
        "web_analytics",
        "df.groupby('channel')['conversions'].sum()"
    )

    print(
        result.to_string()
    )
