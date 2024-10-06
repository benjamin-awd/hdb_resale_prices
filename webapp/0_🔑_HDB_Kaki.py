# ruff:  noqa: E402
import streamlit as st

from webapp.logo import icon, logo

st.set_page_config(page_title="HDB Kaki", page_icon=icon, layout="wide")

from datetime import datetime

import plotly.express as px
import plotly.graph_objects as go
import polars as pl
from plotly.subplots import make_subplots

from webapp.filter import SidebarFilter
from webapp.read import get_last_updated_badge, load_dataframe

st.image(logo, width=500)

last_updated_badge = get_last_updated_badge()
st.image(last_updated_badge)

st.markdown("## Resale Visualizations")

st.markdown(
    "HDB Kaki helps you stay updated on the latest movements in the HDB resale market."
)

group_by = st.radio(
    "Group by:",
    ("Lease Years", "Town"),
)

source = "Source: <a href='https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view'>data.gov.sg</a>"
annotations = dict(
    margin=dict(l=50, r=50, t=100, b=100),
    annotations=[
        dict(
            x=0.5,
            y=-0.33,
            xref="paper",
            yref="paper",
            text=source,
            showarrow=False,
        )
    ],
    height=500,
)


def plot_lease_years(sf: SidebarFilter):
    """Plot percentage change in median resale price by lease years."""
    chart_df = (
        sf.df.group_by(["quarter_label", "cat_remaining_lease_years"])
        .agg(pl.median("resale_price").alias("median_resale_price"))
        .sort(["cat_remaining_lease_years", "quarter_label"])
        .with_columns(
            (
                (
                    pl.col("median_resale_price")
                    / pl.first("median_resale_price").over("cat_remaining_lease_years")
                    - 1
                )
                * 100
            ).alias("percentage_change")
        )
        .sort(by="quarter_label")
    )

    fig = px.line(
        chart_df,
        x="quarter_label",
        y="percentage_change",
        color="cat_remaining_lease_years",
        title=f"Percentage Change in Median Resale Price since {str(sf.start_date)[:7]}",
        labels={
            "percentage_change": "Percentage Change (%)",
            "quarter_label": "Quarter",
            "cat_remaining_lease_years": "Remaining Lease Years",
        },
    )

    fig.update_yaxes(ticksuffix="%")
    fig.update_traces(hovertemplate="%{y:.2f}%")
    fig.update_layout(hovermode="x unified", **annotations)

    st.plotly_chart(fig, use_container_width=True)


def plot_town(sf: SidebarFilter):
    """Plot median resale price and transaction volumes by town."""
    show_transaction_volumes = st.sidebar.checkbox(
        "Show transaction volumes", value=False
    )

    chart_df = (
        sf.df.group_by(["quarter_label", "town"])
        .agg(
            pl.median("resale_price").alias("resale_price"),
            pl.count("resale_price").alias("transaction_volume"),
        )
        .sort(["town", "quarter_label"])
    )

    fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])

    for town in chart_df["town"].unique().sort():
        town_df = chart_df.filter(pl.col("town") == town)

        fig.add_trace(
            go.Scatter(
                x=town_df["quarter_label"],
                y=town_df["resale_price"],
                mode="lines",
                name=town,
                hovertemplate="$%{y}",
                line=dict(shape="spline"),
            ),
            secondary_y=False,
        )

        if show_transaction_volumes:
            fig.add_trace(
                go.Bar(
                    x=town_df["quarter_label"],
                    y=town_df["transaction_volume"],
                    name=town,
                    hovertemplate="%{y} transactions",
                ),
                secondary_y=True,
            )

    fig.update_xaxes(tickformat="%Y-%m")
    fig.update_yaxes(
        showgrid=False, zeroline=False, secondary_y=True, showticklabels=False
    )

    custom_layout = {
        "yaxis": dict(
            range=[
                chart_df["resale_price"].min() * 0.6,
                chart_df["resale_price"].max() * 1.2,
            ]
        ),
        "yaxis2": (
            dict(range=[0, chart_df["transaction_volume"].max() * 15])
            if show_transaction_volumes
            else {}
        ),
    }

    fig.update_layout(
        title="Median Resale Price by Town",
        yaxis_title="Median Resale Price",
        hovermode="x unified",
        barmode="stack",
        **custom_layout,
        **annotations,
    )

    st.plotly_chart(fig, use_container_width=True)


sf = SidebarFilter(
    min_date=datetime.strptime("2017-01-01", "%Y-%m-%d").date(),
    select_towns=(True, "multi"),
    select_lease_years=False,
    default_town="ANG MO KIO" if group_by == "Town" else None,
)

if group_by == "Lease Years":
    plot_lease_years(sf)
if group_by == "Town":
    plot_town(sf)

st.markdown("### Download")
st.write(
    "Download the full dataset for resale flat prices based on registration date from Jan-2017 onwards"
)
st.write(
    "Note: the original dataset can be found here: [data.gov.sg](https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view)."
)
st.download_button(
    "Download CSV",
    load_dataframe().write_csv(),
    "hdb_resale_data.csv",
    "text/csv",
    key="download-csv",
)
