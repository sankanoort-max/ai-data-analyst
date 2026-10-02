import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def generate_chart(result: dict) -> go.Figure | None:
    """
    Generate a Plotly chart based on the agent's plan and query result.
    """

    # ---------------------------------------------------------
    # Validate result
    # ---------------------------------------------------------

    if not result.get("success", False):
        return None

    df = result.get("data")

    if df is None or df.empty:
        return None

    plan = result.get("plan", {})

    chart_type = plan.get(
        "chart_type",
        "none"
    )

    # ---------------------------------------------------------
    # No chart requested
    # ---------------------------------------------------------

    if chart_type == "none":
        return None

    # ---------------------------------------------------------
    # Copy DataFrame so we don't modify original result
    # ---------------------------------------------------------

    df = df.copy()

    # ---------------------------------------------------------
    # Reset index if required
    # ---------------------------------------------------------

    if (
        df.index.name is not None
        or isinstance(df.index, pd.MultiIndex)
    ):
        df = df.reset_index()

    # ---------------------------------------------------------
    # Get chart columns
    # ---------------------------------------------------------

    x_col = plan.get("chart_x")
    y_col = plan.get("chart_y")

    title = plan.get(
        "chart_title",
        "Query Result"
    )

    # ---------------------------------------------------------
    # Automatically determine X column
    # ---------------------------------------------------------

    if not x_col or x_col not in df.columns:

        categorical_columns = [
            col
            for col in df.columns
            if not pd.api.types.is_numeric_dtype(
                df[col]
            )
        ]

        if categorical_columns:
            x_col = categorical_columns[0]

        else:
            x_col = df.columns[0]

    # ---------------------------------------------------------
    # Automatically determine Y column
    # ---------------------------------------------------------

    if not y_col or y_col not in df.columns:

        numeric_columns = [
            col
            for col in df.columns
            if pd.api.types.is_numeric_dtype(
                df[col]
            )
        ]

        if numeric_columns:
            y_col = numeric_columns[0]

        elif len(df.columns) > 1:
            y_col = df.columns[-1]

        else:
            y_col = df.columns[0]

    # ---------------------------------------------------------
    # Generate chart
    # ---------------------------------------------------------

    try:

        # -----------------------------------------------------
        # BAR
        # -----------------------------------------------------

        if chart_type == "bar":

            fig = px.bar(
                df,
                x=x_col,
                y=y_col,
                title=title,
                text_auto=True,
            )

        # -----------------------------------------------------
        # LINE
        # -----------------------------------------------------

        elif chart_type == "line":

            fig = px.line(
                df,
                x=x_col,
                y=y_col,
                title=title,
                markers=True,
            )

        # -----------------------------------------------------
        # PIE
        # -----------------------------------------------------

        elif chart_type == "pie":

            fig = px.pie(
                df,
                names=x_col,
                values=y_col,
                title=title,
            )

        # -----------------------------------------------------
        # TABLE
        # -----------------------------------------------------

        elif chart_type == "table":

            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(
                            values=list(df.columns),
                        ),
                        cells=dict(
                            values=[
                                df[column]
                                for column in df.columns
                            ],
                        ),
                    )
                ]
            )

            fig.update_layout(
                title=title
            )

        # -----------------------------------------------------
        # Unknown chart
        # -----------------------------------------------------

        else:

            print(
                f"Unsupported chart type: {chart_type}"
            )

            return None

        # -----------------------------------------------------
        # Common layout
        # -----------------------------------------------------

        fig.update_layout(
            template="plotly_white",
            height=450,
            margin=dict(
                l=40,
                r=40,
                t=70,
                b=40,
            ),
        )

        return fig

    except Exception as e:

        print(
            f"Chart generation error: {e}"
        )

        return None


print(
    "Chart generator ready."
)
