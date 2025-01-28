# server/utils/response_utils.py
import pandas as pd
import plotly.express as px

def to_table(records):
    if not records:
        return "<p>No data</p>"
    df = pd.DataFrame(records)
    return df.to_html(index=False)

def generate_chart(chart_type, df: pd.DataFrame, x_col, y_col):
    if chart_type == "bar":
        fig = px.bar(df, x=x_col, y=y_col)
    elif chart_type == "line":
        fig = px.line(df, x=x_col, y=y_col)
    elif chart_type == "pie":
        fig = px.pie(df, names=x_col, values=y_col)
    else:
        fig = px.scatter(df, x=x_col, y=y_col)
    return fig.to_html(include_plotlyjs='cdn')
