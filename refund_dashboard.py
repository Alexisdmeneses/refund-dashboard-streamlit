
# Block 1 — imports + config + CSS

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import re

st.set_page_config(
    page_title="Refund Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0e0e14;
    color: #e8e8f0;
}
.main { background-color: #0e0e14; }
h1, h2, h3 { font-family: 'Space Mono', monospace; }

.metric-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 12px;
}
.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 2.2rem;
    font-weight: 700;
    color: #7c6af7;
}
.metric-label {
    font-size: 0.78rem;
    color: #8888aa;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 4px;
}
.metric-delta { font-size: 0.85rem; font-weight: 600; margin-top: 6px; }
.delta-up   { color: #4ade80; }
.delta-down { color: #f87171; }
.delta-zero { color: #8888aa; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 📊 Refund Analytics")
st.markdown("---")

# Block 2 — MONTH_NAMES, PALETTE, funções

MONTH_NAMES = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
               7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

PALETTE = ["#7c6af7","#06b6d4","#f472b6","#4ade80","#fb923c",
           "#a78bfa","#38bdf8","#e879f9","#86efac","#fbbf24"]

def parse_list_col(series):
    def _clean(v):
        try:
            if v is None: return ""
            if pd.isna(v): return ""
        except Exception:
            pass
        return str(v).strip().strip("[]")
    return series.apply(_clean)

def parse_date_col(series):
    def _clean(v):
        try:
            if v is None: return pd.NaT
            if pd.isna(v): return pd.NaT
        except Exception:
            pass
        s = str(v).strip()
        s = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", s)
        s = re.sub(r"\s[+-]\d{2}:\d{2}$", "", s)
        try:
            return pd.to_datetime(s, dayfirst=False)
        except Exception:
            return pd.NaT
    result = series.apply(_clean)
    return pd.to_datetime(result, errors="coerce")

@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()
    col_map = {
        "Date Created":                  "date_created",
        "Purchase date (date)":          "purchase_date",
        "Refund type (drop down)":       "refund_type",
        "Refund resolution (drop down)": "refund_resolution",
        "Refund reasons (labels)":       "refund_reasons",
        "Course name (drop down)":       "course",
        "Country (drop down)":           "country",
        "Assignee":                      "assignee",
        "Task Name":                     "task_name",
        "Student Email (short text)":    "email",
        "Task ID":                       "task_id",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    df["date_created"]  = parse_date_col(df.get("date_created",  pd.Series(dtype=str)))
    df["purchase_date"] = parse_date_col(df.get("purchase_date", pd.Series(dtype=str)))
    if "refund_reasons" in df.columns:
        df["refund_reasons"] = parse_list_col(df["refund_reasons"])
    df["year"]  = df["date_created"].dt.year
    df["month"] = df["date_created"].dt.month
    df["day"]   = df["date_created"].dt.day
    for c in ["country","course","refund_type","refund_resolution"]:
        if c in df.columns:
            df[c] = df[c].fillna("Unknown").replace("", "Unknown")
    return df

def mom_cutoff_filter(df, ref_date):
    day_cutoff = ref_date.day
    cur_m, cur_y = ref_date.month, ref_date.year
    prev_m = cur_m - 1 if cur_m > 1 else 12
    prev_y = cur_y    if cur_m > 1 else cur_y - 1
    cur  = df[(df["year"]==cur_y)  & (df["month"]==cur_m)  & (df["day"]<=day_cutoff)]
    prev = df[(df["year"]==prev_y) & (df["month"]==prev_m) & (df["day"]<=day_cutoff)]
    return cur, prev

def delta_html(cur_val, prev_val):
    if prev_val == 0:
        return '<span class="delta-zero">— no prior data</span>'
    chg = (cur_val - prev_val) / prev_val * 100
    cls = "delta-up" if chg >= 0 else "delta-down"
    arrow = "▲" if chg >= 0 else "▼"
    return f'<span class="{cls}">{arrow} {abs(chg):.1f}% vs prev month</span>'


# Block 4 — metrics + charts
with st.sidebar:
    st.markdown("### 📂 Upload CSV")
    uploaded = st.file_uploader("Drop your refunds CSV", type=["csv"])
    st.markdown("---")
    st.markdown("### 📅 Reference date")
    ref_date = st.date_input("Compare up to this day", value=date.today())

if uploaded is None:
    st.info("👈  Upload your CSV in the sidebar to get started.")
    st.stop()

df_raw = load_data(uploaded)

with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔽 Filters")
    countries = sorted(df_raw["country"].dropna().unique().tolist())
    sel_countries = st.multiselect("Country", countries, default=countries)
    courses = sorted(df_raw["course"].dropna().unique().tolist())
    sel_courses = st.multiselect("Course track", courses, default=courses)

df = df_raw[
    df_raw["country"].isin(sel_countries) &
    df_raw["course"].isin(sel_courses)
]

cur_df, prev_df = mom_cutoff_filter(df, ref_date)

cur_label  = f"{MONTH_NAMES[ref_date.month]} {ref_date.year} (1–{ref_date.day})"
prev_m     = ref_date.month - 1 if ref_date.month > 1 else 12
prev_y     = ref_date.year     if ref_date.month > 1 else ref_date.year - 1
prev_label = f"{MONTH_NAMES[prev_m]} {prev_y} (1–{ref_date.day})"

st.markdown(f"##### Showing {cur_label} vs {prev_label}")
st.markdown("---")

# ── KPI Cards ──
def kpi(col, title, cur, prev):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{cur}</div>
            <div class="metric-label">{title}</div>
            <div class="metric-delta">{delta_html(cur, prev)}</div>
        </div>""", unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)

kpi(k1, "Total Refunds", len(cur_df), len(prev_df))

confirmed_cur  = (cur_df["refund_resolution"] == "Confirmed").sum() if "refund_resolution" in cur_df.columns else 0
confirmed_prev = (prev_df["refund_resolution"] == "Confirmed").sum() if "refund_resolution" in prev_df.columns else 0
kpi(k2, "Confirmed Refunds", confirmed_cur, confirmed_prev)

denied_cur  = (cur_df["refund_resolution"] == "Prevented").sum() if "refund_resolution" in cur_df.columns else 0
denied_prev = (prev_df["refund_resolution"] == "Prevented").sum() if "refund_resolution" in prev_df.columns else 0
kpi(k3, "Prevented Refunds", denied_cur, denied_prev)

n_courses_cur  = cur_df["course"].nunique() if "course" in cur_df.columns else 0
n_courses_prev = prev_df["course"].nunique() if "course" in prev_df.columns else 0
kpi(k4, "Courses Affected", n_courses_cur, n_courses_prev)

st.markdown("---")

# Block 5 — Refund Type MoM
st.markdown("## Refund Type — Month over Month")
st.caption(f"Comparing **{cur_label}** vs **{prev_label}**")

if "refund_type" in df.columns:
    rt_cur  = cur_df["refund_type"].value_counts().rename("current")
    rt_prev = prev_df["refund_type"].value_counts().rename("previous")
    rt_df   = pd.concat([rt_cur, rt_prev], axis=1).fillna(0).reset_index()
    rt_df.columns = ["refund_type", "current", "previous"]
    rt_df = rt_df.sort_values("current", ascending=False)

    fig_rt = go.Figure()
    fig_rt.add_bar(x=rt_df["refund_type"], y=rt_df["previous"],
               name=prev_label, marker_color="#2a2a4a",
               text=rt_df["previous"].astype(int), textposition="outside",
               textfont_color="#000000")
    fig_rt.add_bar(x=rt_df["refund_type"], y=rt_df["current"],
               name=cur_label, marker_color="#7c6af7",
               text=rt_df["current"].astype(int), textposition="outside",
               textfont_color="#000000")
    fig_rt.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e8e8f0", font_family="DM Sans",
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="#1a1a2e"),
        yaxis=dict(gridcolor="#1a1a2e"),
        margin=dict(l=0, r=0, t=10, b=0), height=340,
    )
    st.plotly_chart(fig_rt, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**By Country**")
        rt_country = (
            pd.concat([
                cur_df.assign(period=cur_label),
                prev_df.assign(period=prev_label)
            ])
            .groupby(["country", "refund_type", "period"])
            .size().reset_index(name="count")
        )
        fig_c = px.bar(rt_country, x="country", y="count", color="refund_type",
                       facet_col="period", barmode="stack",
                       color_discrete_sequence=PALETTE, height=320)
        fig_c.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e8e8f0", margin=dict(l=0, r=0, t=30, b=0))
        fig_c.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        st.plotly_chart(fig_c, use_container_width=True)

    with c2:
        st.markdown("**By Course Track**")
        rt_course = (
            pd.concat([
                cur_df.assign(period=cur_label),
                prev_df.assign(period=prev_label)
            ])
            .groupby(["course", "refund_type", "period"])
            .size().reset_index(name="count")
        )
        fig_crs = px.bar(rt_course, x="course", y="count", color="refund_type",
                         facet_col="period", barmode="stack",
                         color_discrete_sequence=PALETTE, height=320)
        fig_crs.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e8e8f0", margin=dict(l=0, r=0, t=30, b=0))
        fig_crs.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        st.plotly_chart(fig_crs, use_container_width=True)

else:
    st.warning("Column `Refund type` not found in your CSV.")

st.markdown("---")

# Block 6 — Refund Resolution MoM
st.markdown("## Refund Resolution — Month over Month")
st.caption(f"Comparing **{cur_label}** vs **{prev_label}**")

if "refund_resolution" in df.columns:
    rr_cur  = cur_df["refund_resolution"].value_counts().rename("current")
    rr_prev = prev_df["refund_resolution"].value_counts().rename("previous")
    rr_df   = pd.concat([rr_cur, rr_prev], axis=1).fillna(0).reset_index()
    rr_df.columns = ["resolution", "current", "previous"]

    col_a, col_b = st.columns([1, 1])

    with col_a:
        fig_rr = go.Figure()
        fig_rr.add_bar(x=rr_df["resolution"], y=rr_df["previous"],
               name=prev_label, marker_color="#2a2a4a",
               text=rr_df["previous"].astype(int), textposition="outside",
               textfont_color="#000000")
        fig_rr.add_bar(x=rr_df["resolution"], y=rr_df["current"],
               name=cur_label, marker_color="#06b6d4",
               text=rr_df["current"].astype(int), textposition="outside",
               textfont_color="#000000")
        fig_rr.update_layout(
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e8e8f0", font_family="DM Sans",
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(gridcolor="#1a1a2e"),
            yaxis=dict(gridcolor="#1a1a2e"),
            margin=dict(l=0, r=0, t=10, b=0), height=300,
        )
        st.plotly_chart(fig_rr, use_container_width=True)

    with col_b:
        fig_pie = px.pie(rr_df, names="resolution", values="current",
                         title=f"Resolution mix — {cur_label}",
                         color_discrete_sequence=PALETTE, hole=0.45)
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font_color="#000000",
            margin=dict(l=0, r=0, t=40, b=0), height=300)
        st.plotly_chart(fig_pie, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Resolution by Country**")
        rr_country = (
            pd.concat([
                cur_df.assign(period=cur_label),
                prev_df.assign(period=prev_label)
            ])
            .groupby(["country", "refund_resolution", "period"])
            .size().reset_index(name="count")
        )
        fig_rrc = px.bar(rr_country, x="country", y="count",
                         color="refund_resolution", facet_col="period",
                         barmode="stack", color_discrete_sequence=PALETTE, height=320)
        fig_rrc.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e8e8f0", margin=dict(l=0, r=0, t=30, b=0))
        fig_rrc.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        st.plotly_chart(fig_rrc, use_container_width=True)

    with c2:
        st.markdown("**Resolution by Course Track**")
        rr_course = (
            pd.concat([
                cur_df.assign(period=cur_label),
                prev_df.assign(period=prev_label)
            ])
            .groupby(["course", "refund_resolution", "period"])
            .size().reset_index(name="count")
        )
        fig_rrs = px.bar(rr_course, x="course", y="count",
                         color="refund_resolution", facet_col="period",
                         barmode="stack", color_discrete_sequence=PALETTE, height=320)
        fig_rrs.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e8e8f0", margin=dict(l=0, r=0, t=30, b=0))
        fig_rrs.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        st.plotly_chart(fig_rrs, use_container_width=True)

else:
    st.warning("Column `Refund resolution` not found in your CSV.")

st.markdown("---")

# Block 7 — Daily Volume Trend
st.markdown("## Daily Volume — Current vs Previous Month")
st.caption(f"Comparing **{cur_label}** vs **{prev_label}**")

daily_cur  = cur_df.groupby("day").size().rename("current")
daily_prev = prev_df.groupby("day").size().rename("previous")
daily_df   = pd.concat([daily_cur, daily_prev], axis=1).fillna(0).reset_index()
daily_df.columns = ["day", "current", "previous"]

fig_daily = go.Figure()
fig_daily.add_scatter(x=daily_df["day"], y=daily_df["previous"],
                      mode="lines", name=prev_label,
                      line=dict(color="#2a2a5a", width=2, dash="dot"))
fig_daily.add_scatter(x=daily_df["day"], y=daily_df["current"],
                      mode="lines+markers", name=cur_label,
                      line=dict(color="#7c6af7", width=2.5),
                      marker=dict(size=6))
fig_daily.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font_color="#000000", font_family="DM Sans",
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    xaxis=dict(title="Day of month", gridcolor="#1a1a2e"),
    yaxis=dict(title="# Refunds", gridcolor="#1a1a2e"),
    margin=dict(l=0, r=0, t=10, b=0), height=300,
)
st.plotly_chart(fig_daily, use_container_width=True)

st.markdown("---")

# Block 8 — Top Refund Reasons + Raw Data
st.markdown("## Top Refund Reasons")
st.caption(f"Comparing **{cur_label}** vs **{prev_label}**")

if "refund_reasons" in df.columns:
    def explode_reasons(frame):
        rows = []
        for _, row in frame.iterrows():
            reasons = [r.strip() for r in str(row["refund_reasons"]).split(",") if r.strip()]
            for r in reasons:
                rows.append(r)
        return pd.Series(rows).value_counts()

    rr_cur_exp  = explode_reasons(cur_df).rename("current")
    rr_prev_exp = explode_reasons(prev_df).rename("previous")
    reasons_df  = pd.concat([rr_cur_exp, rr_prev_exp], axis=1).fillna(0).reset_index()
    reasons_df.columns = ["reason", "current", "previous"]
    reasons_df = reasons_df.sort_values("current", ascending=True).tail(12)

    fig_reasons = go.Figure()
    fig_reasons.add_bar(y=reasons_df["reason"], x=reasons_df["previous"],
                    orientation="h", name=prev_label, marker_color="#2a2a4a",
                    text=reasons_df["previous"].astype(int), textposition="outside",
                    textfont_color="#000000")
    fig_reasons.add_bar(y=reasons_df["reason"], x=reasons_df["current"],
                    orientation="h", name=cur_label, marker_color="#f472b6",
                    text=reasons_df["current"].astype(int), textposition="outside",
                    textfont_color="#000000")
    fig_reasons.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e8e8f0", font_family="DM Sans",
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="#1a1a2e"),
        yaxis=dict(gridcolor="#1a1a2e"),
        margin=dict(l=0, r=0, t=10, b=0),
        height=max(300, len(reasons_df) * 36),
    )
    st.plotly_chart(fig_reasons, use_container_width=True)

else:
    st.warning("Column `Refund reasons` not found in your CSV.")

st.markdown("---")

# Raw data table
with st.expander("🔍 View raw data"):
    show_cols = [c for c in ["date_created", "task_name", "refund_type", "refund_resolution",
                              "refund_reasons", "course", "country", "email"] if c in df.columns]
    st.dataframe(
        pd.concat([
            cur_df[show_cols].assign(period=cur_label),
            prev_df[show_cols].assign(period=prev_label)
        ]),
        use_container_width=True, height=360
    )


