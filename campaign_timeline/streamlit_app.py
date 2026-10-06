import calendar
from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

CHANNEL_COLORS = {
    "Paid Social": "#1f77b4",
    "Paid Search": "#2ca02c",
    "Display": "#9467bd",
    "Email": "#ff7f0e",
    "SMS": "#17becf",
}
DEFAULT_MONTH = date(2026, 11, 1)

conn = st.connection("snowflake")


@st.cache_data(ttl=300)
def load_campaigns() -> pd.DataFrame:
    df = conn.query(
        """
        SELECT campaign_id, campaign_name, channel, region, audience,
               start_date, end_date, budget_usd, owner_team, status, source_system
        FROM MERIDIAN_STAY.CURATED.CAMPAIGNS
        ORDER BY region, audience, start_date
        """
    )
    df.columns = [c.lower() for c in df.columns]
    df["start_date"] = pd.to_datetime(df["start_date"]).dt.date
    df["end_date"] = pd.to_datetime(df["end_date"]).dt.date
    df["lane"] = df["region"] + " · " + df["audience"]
    return df


def month_options(df: pd.DataFrame) -> list[date]:
    first = df["start_date"].min().replace(day=1)
    last = df["end_date"].max().replace(day=1)
    return [m.date() for m in pd.date_range(first, last, freq="MS")]


def timeline_chart(df: pd.DataFrame, month_start: date, month_end: date) -> alt.Chart:
    """One row per region · audience; campaigns that share a row and overlap in time compete for the same people."""
    plot = df.copy()
    # Clip bars to the selected month so long-running campaigns don't stretch the axis.
    plot["bar_start"] = plot["start_date"].clip(lower=month_start)
    plot["bar_end"] = plot["end_date"].clip(upper=month_end) + timedelta(days=1)
    plot["bar_start"] = pd.to_datetime(plot["bar_start"])
    plot["bar_end"] = pd.to_datetime(plot["bar_end"])
    lanes = sorted(plot["lane"].unique())

    bars = (
        alt.Chart(plot)
        .mark_bar(cornerRadius=3, height={"band": 0.85})
        .encode(
            x=alt.X(
                "bar_start:T",
                title=None,
                scale=alt.Scale(domain=[pd.Timestamp(month_start), pd.Timestamp(month_end + timedelta(days=1))]),
                axis=alt.Axis(format="%b %d", tickCount="week", grid=True),
            ),
            x2="bar_end:T",
            y=alt.Y("lane:N", title=None, sort=lanes, axis=alt.Axis(labelLimit=260)),
            yOffset=alt.YOffset("campaign_name:N"),
            color=alt.Color(
                "channel:N",
                title="Channel",
                scale=alt.Scale(domain=list(CHANNEL_COLORS), range=list(CHANNEL_COLORS.values())),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[
                alt.Tooltip("campaign_name:N", title="Campaign"),
                alt.Tooltip("channel:N", title="Channel"),
                alt.Tooltip("region:N", title="Region"),
                alt.Tooltip("audience:N", title="Audience"),
                alt.Tooltip("start_date:N", title="Starts"),
                alt.Tooltip("end_date:N", title="Ends"),
                alt.Tooltip("budget_usd:Q", title="Budget (USD)", format="$,.0f"),
                alt.Tooltip("owner_team:N", title="Owner"),
            ],
        )
    )
    height = max(260, 30 * len(plot) + 20 * len(lanes))
    return bars.properties(height=height)


st.title("Meridian Stay campaign timeline")
st.caption(
    "Every planned campaign from the ad platforms, the email & SMS platform, and the CRM, in one view. "
    "Each row is a region and audience. Bars that share a row and overlap in time are competing for the same people."
)

campaigns = load_campaigns()
months = month_options(campaigns)

col_month, col_region = st.columns([1, 3])
selected_month = col_month.selectbox(
    "Month",
    months,
    index=months.index(DEFAULT_MONTH) if DEFAULT_MONTH in months else 0,
    format_func=lambda m: m.strftime("%B %Y"),
)
regions = sorted(campaigns["region"].unique())
selected_regions = col_region.multiselect("Regions", regions, default=regions)

month_end = date(
    selected_month.year,
    selected_month.month,
    calendar.monthrange(selected_month.year, selected_month.month)[1],
)
in_month = campaigns[
    (campaigns["start_date"] <= month_end)
    & (campaigns["end_date"] >= selected_month)
    & (campaigns["region"].isin(selected_regions))
]

m1, m2, m3 = st.columns(3)
m1.metric("Campaigns running", len(in_month))
m2.metric("Budget in flight", f"${in_month['budget_usd'].sum():,.0f}")
m3.metric("Channels active", in_month["channel"].nunique())

if in_month.empty:
    st.info("No campaigns match the selected month and regions.")
else:
    st.altair_chart(timeline_chart(in_month, selected_month, month_end), width="stretch")

    with st.expander("Campaigns running this month", expanded=False):
        st.dataframe(
            in_month[["campaign_name", "channel", "region", "audience", "start_date", "end_date", "budget_usd", "owner_team"]],
            hide_index=True,
            width="stretch",
        )
