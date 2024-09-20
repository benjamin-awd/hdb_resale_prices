import numpy as np
import plotly.express as px
import polars as pl
import streamlit as st

from webapp.filter import SidebarFilter
from webapp.read import load_dataframe

st.title("📊 Distribution of Resale Price")
st.write(
    "Find out how much you will need approximately for buying a flat in the respective towns."
)
df = load_dataframe()
df = df.with_columns(pl.col("month").str.strptime(pl.Date, "%Y-%m"))
min_date = df["month"].min()
max_date = df["month"].max()


sf = SidebarFilter(min_date, max_date, df, select_towns=(False, ""))

# Generate a rainbow color palette
towns = sf.df["town"].unique()
colors = ["hsl({}, 70%, 70%)".format(h) for h in np.linspace(0, 360, len(towns))]

fig = px.box(
    sf.df,
    x="town",
    y="resale_price",
    color="town",
    color_discrete_sequence=colors,
    title="Distribution of Resale Prices by Town",
    labels={"resale_price": "Resale Price", "town": "Town"},
)

fig.update_layout(
    xaxis_title="Resale Price",
    yaxis_title="Town",
    height=900,
    legend=dict(orientation="h", yanchor="bottom", y=-0.55, xanchor="right", x=1),
)
fig.update_traces(
    hovertemplate="<b>%{x}</b><br>Resale Price: %{y}<br>",
)

fig.update_layout(hovermode="closest")

st.plotly_chart(fig, use_container_width=True)
