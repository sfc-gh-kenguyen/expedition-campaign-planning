import calendar
import html
from datetime import date

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

CHANNEL_COLORS = {
    "Paid Social": "#1f77b4",
    "Paid Search": "#2ca02c",
    "Display": "#9467bd",
    "Email": "#ff7f0e",
    "SMS": "#17becf",
}
MAX_CHIPS_PER_DAY = 5

conn = st.connection("snowflake")


@st.cache_data(ttl=300)
def load_campaigns() -> pd.DataFrame:
    df = conn.query(
        """
        SELECT campaign_id, campaign_name, channel, region, audience,
               start_date, end_date, budget_usd, owner_team, source_system
        FROM MERIDIAN_STAY.CURATED.CAMPAIGNS
        ORDER BY start_date, campaign_name
        """
    )
    df.columns = [c.lower() for c in df.columns]
    df["start_date"] = pd.to_datetime(df["start_date"]).dt.date
    df["end_date"] = pd.to_datetime(df["end_date"]).dt.date
    return df


def month_options(df: pd.DataFrame) -> list[date]:
    first = df["start_date"].min().replace(day=1)
    last = df["end_date"].max().replace(day=1)
    months = pd.date_range(first, last, freq="MS")
    return [m.date() for m in months]


def active_on(df: pd.DataFrame, day: date) -> pd.DataFrame:
    return df[(df["start_date"] <= day) & (df["end_date"] >= day)]


def build_calendar_html(df: pd.DataFrame, month_start: date) -> tuple[str, int]:
    """Renders a month grid as self-contained HTML (no external scripts or styles)."""
    weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(month_start.year, month_start.month)
    parts = [
        """
        <style>
          body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
          .cal { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
          .dow { font-size: 12px; font-weight: 600; color: #555; text-align: center; padding: 4px 0; }
          .day { border: 1px solid #e3e3e3; border-radius: 6px; padding: 4px; height: 140px; overflow: hidden; background: #fff; }
          .day.outside { background: #f7f7f7; opacity: 0.55; }
          .num { font-size: 12px; font-weight: 600; color: #888; margin-bottom: 2px; }
          .event { font-size: 11px; line-height: 1.25; border-radius: 4px; padding: 2px 4px; margin-top: 2px;
                   white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #1b1b1b; }
          .more { font-size: 11px; color: #666; margin-top: 2px; }
        </style>
        <div class="cal">
        """
    ]
    for dow in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
        parts.append(f'<div class="dow">{dow}</div>')

    for week in weeks:
        for day in week:
            outside = " outside" if day.month != month_start.month else ""
            parts.append(f'<div class="day{outside}"><div class="num">{day.day}</div>')
            events = active_on(df, day)
            for _, ev in events.head(MAX_CHIPS_PER_DAY).iterrows():
                color = CHANNEL_COLORS.get(ev["channel"], "#999999")
                tooltip = html.escape(
                    f"{ev['campaign_name']} | {ev['channel']} | {ev['region']} | {ev['audience']} "
                    f"| {ev['start_date']} to {ev['end_date']}"
                )
                parts.append(
                    f'<div class="event" title="{tooltip}" '
                    f'style="background:{color}22; border-left:3px solid {color};">'
                    f"{html.escape(ev['campaign_name'])}</div>"
                )
            hidden = len(events) - MAX_CHIPS_PER_DAY
            if hidden > 0:
                parts.append(f'<div class="more">+{hidden} more</div>')
            parts.append("</div>")

    parts.append("</div>")
    height = 40 + len(weeks) * 146
    return "".join(parts), height


st.title("Meridian Stay campaign calendar")
st.caption("One shared view of every planned campaign across ad platforms, the email & SMS platform, and the CRM.")

campaigns = load_campaigns()
months = month_options(campaigns)
selected_month = st.selectbox(
    "Month",
    months,
    index=months.index(date(2026, 11, 1)) if date(2026, 11, 1) in months else 0,
    format_func=lambda m: m.strftime("%B %Y"),
)

month_end = date(
    selected_month.year,
    selected_month.month,
    calendar.monthrange(selected_month.year, selected_month.month)[1],
)
in_month = campaigns[(campaigns["start_date"] <= month_end) & (campaigns["end_date"] >= selected_month)]

col1, col2, col3 = st.columns(3)
col1.metric("Campaigns running", len(in_month))
col2.metric("Budget in flight", f"${in_month['budget_usd'].sum():,.0f}")
col3.metric("Channels active", in_month["channel"].nunique())

st.markdown(
    " ".join(
        f'<span style="border-left:4px solid {c}; padding:0 6px; margin-right:8px; font-size:13px;">{ch}</span>'
        for ch, c in CHANNEL_COLORS.items()
    ),
    unsafe_allow_html=True,
)

calendar_html, calendar_height = build_calendar_html(campaigns, selected_month)
components.html(calendar_html, height=calendar_height, scrolling=False)

with st.expander("Campaigns running this month", expanded=False):
    st.dataframe(
        in_month[["campaign_name", "channel", "region", "audience", "start_date", "end_date", "budget_usd", "owner_team"]],
        hide_index=True,
        width="stretch",
    )
