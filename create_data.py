import pandas as pd
import numpy as np
import sqlite3
import os

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
np.random.seed(42)

DATA_DIR = "./data"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------
# 1. Sales data → SQLite database
# ---------------------------------------------------------
dates = pd.date_range(
    start="2024-01-01",
    end="2025-12-31",
    freq="D"
)

sales_df = pd.DataFrame({
    "date": dates,
    "region": np.random.choice(
        ["North", "South", "East", "West"],
        len(dates)
    ),
    "product": np.random.choice(
        ["Widget A", "Widget B", "Widget C", "Premium X"],
        len(dates)
    ),
    "revenue": np.round(
        np.random.uniform(500, 15000, len(dates)),
        2
    ),
    "units_sold": np.random.randint(
        10, 500, len(dates)
    ),
    "cost": np.round(
        np.random.uniform(200, 8000, len(dates)),
        2
    ),
})

# Calculate profit
sales_df["profit"] = (
    sales_df["revenue"] - sales_df["cost"]
)

# Add time dimensions
sales_df["quarter"] = (
    sales_df["date"]
    .dt.to_period("Q")
    .astype(str)
)

sales_df["month"] = (
    sales_df["date"]
    .dt.to_period("M")
    .astype(str)
)

# Save to SQLite
sales_db = os.path.join(DATA_DIR, "sales.db")

conn = sqlite3.connect(sales_db)

sales_df.to_sql(
    "sales",
    conn,
    if_exists="replace",
    index=False
)

conn.close()

print(
    f"✅ SQLite: {sales_db} — "
    f"{len(sales_df)} rows"
)

# ---------------------------------------------------------
# 2. Employee data → Excel
# ---------------------------------------------------------
departments = [
    "Engineering",
    "Sales",
    "Marketing",
    "HR",
    "Finance",
    "Operations"
]

emp_df = pd.DataFrame({
    "employee_id": range(1, 201),

    "name": [
        f"Employee_{i}"
        for i in range(1, 201)
    ],

    "department": np.random.choice(
        departments,
        200
    ),

    "salary": np.round(
        np.random.uniform(45000, 180000, 200),
        2
    ),

    "hire_date": pd.date_range(
        start="2018-01-01",
        periods=200,
        freq="11D"
    ),

    "performance_score": np.random.choice(
        ["Exceeds", "Meets", "Below"],
        200,
        p=[0.25, 0.55, 0.20]
    ),
})

employees_file = os.path.join(
    DATA_DIR,
    "employees.xlsx"
)

emp_df.to_excel(
    employees_file,
    index=False
)

print(
    f"✅ Excel: {employees_file} — "
    f"{len(emp_df)} rows"
)

# ---------------------------------------------------------
# 3. Website analytics → CSV
# ---------------------------------------------------------
web_dates = pd.date_range(
    start="2025-01-01",
    end="2025-12-31",
    freq="D"
)

web_df = pd.DataFrame({
    "date": web_dates,

    "page_views": np.random.randint(
        1000,
        50000,
        len(web_dates)
    ),

    "unique_visitors": np.random.randint(
        500,
        20000,
        len(web_dates)
    ),

    "bounce_rate": np.round(
        np.random.uniform(
            0.20,
            0.75,
            len(web_dates)
        ),
        3
    ),

    "avg_session_duration_sec": np.random.randint(
        30,
        600,
        len(web_dates)
    ),

    "conversions": np.random.randint(
        5,
        500,
        len(web_dates)
    ),

    "channel": np.random.choice(
        [
            "Organic",
            "Paid",
            "Social",
            "Email",
            "Direct"
        ],
        len(web_dates)
    ),
})

web_file = os.path.join(
    DATA_DIR,
    "web_analytics.csv"
)

web_df.to_csv(
    web_file,
    index=False
)

print(
    f"✅ CSV: {web_file} — "
    f"{len(web_df)} rows"
)

# ---------------------------------------------------------
# Final validation
# ---------------------------------------------------------
print("\n📂 Sample data created successfully!")
print(f"   Sales records     : {len(sales_df)}")
print(f"   Employee records  : {len(emp_df)}")
print(f"   Web analytics     : {len(web_df)}")