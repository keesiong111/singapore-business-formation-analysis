"""
Singapore Business Formation Dashboard
Built with Streamlit + Pandas + Matplotlib
Data: data.gov.sg (1990–2026)
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings
warnings.filterwarnings("ignore")

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SG Business Formation Dashboard",
    page_icon="🇸🇬",
    layout="wide",
)

# ── Style ────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.25,
    "grid.linestyle":    "--",
    "figure.dpi":        130,
})

PALETTE = {
    "Information & Communications":                   "#2563EB",
    "Finance & Insurance":                            "#7C3AED",
    "Professional Services":                          "#059669",
    "Transportation & Storage":                       "#DC2626",
    "Retail Trade":                                   "#D97706",
    "Food & Beverage Services":                       "#DB2777",
    "Construction":                                   "#0891B2",
    "Manufacturing":                                  "#65A30D",
    "Wholesale Trade":                                "#0D9488",
    "Education, Health & Social Services":            "#8B5CF6",
    "Administrative & Support Services":              "#F59E0B",
    "Real Estate":                                    "#6366F1",
    "Arts, Entertainment, Recreation & Other Services": "#EC4899",
    "Accommodation":                                  "#94A3B8",
}

EXCLUDE = ["Total", "Others"]

# ── Load data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_business_entity_formations_long.csv")
    df["date"]  = pd.to_datetime(df["date"])
    df["year"]  = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df[~df["DataSeries"].isin(EXCLUDE)].copy()

df = load_data()
all_industries = sorted(df["DataSeries"].unique().tolist())

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🇸🇬 Singapore Business Formation Dashboard")
st.markdown(
    "Explore 36 years of business registration data across 14 industries. "
    "**Data source:** [data.gov.sg](https://data.gov.sg) · Period: 1990–2026"
)
st.divider()

# ── KPI Row ──────────────────────────────────────────────────────────────────
latest   = df[df["date"] >= "2025-01-01"]
baseline = df[df["year"].isin([2017, 2018, 2019])]
recovery = df[df["date"] >= "2022-01-01"]

total_latest   = int(latest.groupby("DataSeries")["value"].mean().sum())
top_industry   = latest.groupby("DataSeries")["value"].mean().idxmax()
top_value      = int(latest.groupby("DataSeries")["value"].mean().max())

baseline_avg   = baseline.groupby("DataSeries")["value"].mean()
recovery_avg   = recovery.groupby("DataSeries")["value"].mean()
recovery_pct   = ((recovery_avg - baseline_avg) / baseline_avg * 100).dropna()
best_recovery  = recovery_pct.idxmax()
best_pct       = recovery_pct.max()
worst_recovery = recovery_pct.idxmin()
worst_pct      = recovery_pct.min()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total formations/month (2025–26)", f"{total_latest:,}")
c2.metric("Top sector 2025–26", top_industry.split(" ")[0] + "...", f"{top_value:,}/mo")
c3.metric("Best post-COVID recovery", best_recovery.split(" ")[0] + "...", f"+{best_pct:.1f}%")
c4.metric("Most declined sector", worst_recovery.split(" ")[0] + "...", f"{worst_pct:.1f}%")

st.divider()

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Trend Explorer",
    "🏆 Post-COVID Recovery",
    "😷 COVID Impact",
    "🚀 2025–2026 Momentum",
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Trend Explorer
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Industry Trend Explorer")
    st.caption("Select industries and a time range to compare formation trends.")

    col_l, col_r = st.columns([1, 3])
    with col_l:
        selected = st.multiselect(
            "Industries",
            options=all_industries,
            default=["Information & Communications", "Finance & Insurance",
                     "Professional Services", "Transportation & Storage"],
        )
        year_min, year_max = st.slider(
            "Year range",
            min_value=int(df["year"].min()),
            max_value=int(df["year"].max()),
            value=(2000, int(df["year"].max())),
        )
        freq = st.radio("Frequency", ["Monthly", "Annual"], index=1)

    with col_r:
        if not selected:
            st.info("Select at least one industry from the left.")
        else:
            df_sel = df[df["DataSeries"].isin(selected) &
                        df["year"].between(year_min, year_max)]

            if freq == "Annual":
                df_plot = df_sel.groupby(["DataSeries", "year"])["value"].sum().reset_index()
                x_col = "year"
            else:
                df_plot = df_sel.copy()
                x_col = "date"

            fig, ax = plt.subplots(figsize=(10, 5))
            for ind in selected:
                d = df_plot[df_plot["DataSeries"] == ind]
                color = PALETTE.get(ind, "#888888")
                ax.plot(d[x_col], d["value"], label=ind, color=color,
                        linewidth=2, alpha=0.9)

            for year, label in [(2003, "SARS"), (2009, "GFC"), (2020, "COVID")]:
                if year_min <= year <= year_max:
                    ax.axvline(pd.Timestamp(f"{year}-01-01") if freq == "Monthly" else year,
                               color="gray", linewidth=0.8, linestyle=":", alpha=0.6)
                    ax.text(pd.Timestamp(f"{year}-03-01") if freq == "Monthly" else year + 0.2,
                            ax.get_ylim()[1] * 0.93, label, fontsize=8, color="gray")

            ax.set_ylabel("Business Formations", fontsize=10)
            ax.set_title(f"{'Monthly' if freq == 'Monthly' else 'Annual'} Business Formations "
                         f"({year_min}–{year_max})", fontsize=12, fontweight="bold")
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
            ax.legend(fontsize=8, loc="upper left")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Post-COVID Recovery
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Post-COVID Recovery by Industry")
    st.caption("2022–2026 monthly average vs 2017–2019 pre-COVID baseline.")

    col_l, col_r = st.columns([1, 3])
    with col_l:
        baseline_years = st.multiselect(
            "Baseline years",
            options=list(range(2015, 2020)),
            default=[2017, 2018, 2019],
        )
        recovery_start = st.selectbox(
            "Recovery period start",
            options=[2021, 2022, 2023],
            index=1,
        )

    with col_r:
        if not baseline_years:
            st.info("Select at least one baseline year.")
        else:
            b_avg = df[df["year"].isin(baseline_years)].groupby("DataSeries")["value"].mean()
            r_avg = df[df["year"] >= recovery_start].groupby("DataSeries")["value"].mean()
            rec   = pd.DataFrame({"baseline": b_avg, "recovery": r_avg}).dropna()
            rec["pct"] = ((rec["recovery"] - rec["baseline"]) / rec["baseline"] * 100).round(1)
            rec = rec.sort_values("pct", ascending=True)

            colors = ["#DC2626" if x < 0 else "#2563EB" for x in rec["pct"]]

            fig, ax = plt.subplots(figsize=(10, 7))
            bars = ax.barh(rec.index, rec["pct"], color=colors,
                           height=0.6, edgecolor="white", linewidth=0.5)
            for bar, val in zip(bars, rec["pct"]):
                xp = val + 0.5 if val >= 0 else val - 0.5
                ha = "left" if val >= 0 else "right"
                ax.text(xp, bar.get_y() + bar.get_height() / 2,
                        f"{val:+.1f}%", va="center", ha=ha, fontsize=9,
                        fontweight="bold", color="#DC2626" if val < 0 else "#2563EB")
            ax.axvline(0, color="black", linewidth=0.8, alpha=0.4)
            ax.set_xlabel(f"Change vs {baseline_years} baseline (%)", fontsize=10)
            ax.set_title(f"Post-COVID Recovery (from {recovery_start})", fontsize=12, fontweight="bold")
            ax.tick_params(axis="y", labelsize=9)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            # Insight callout
            top3 = rec.nlargest(3, "pct")
            bot1 = rec.nsmallest(1, "pct")
            st.info(
                f"**Top 3 recoveries:** "
                f"{top3.index[0].split(' ')[0]} ({top3['pct'].iloc[0]:+.1f}%), "
                f"{top3.index[1].split(' ')[0]} ({top3['pct'].iloc[1]:+.1f}%), "
                f"{top3.index[2].split(' ')[0]} ({top3['pct'].iloc[2]:+.1f}%)  \n"
                f"**Biggest decline:** {bot1.index[0]} ({bot1['pct'].iloc[0]:+.1f}%)"
            )

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — COVID Impact
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("COVID-19 Impact by Industry")
    st.caption("Compare any two years to see how formations changed.")

    col_l, col_r = st.columns([1, 3])
    with col_l:
        year_a = st.selectbox("Before year", options=list(range(2015, 2023)), index=4)
        year_b = st.selectbox("After year",  options=list(range(2015, 2027)), index=6)

    with col_r:
        if year_a == year_b:
            st.warning("Select two different years.")
        else:
            pre = df[df["year"] == year_a].groupby("DataSeries")["value"].mean()
            dur = df[df["year"] == year_b].groupby("DataSeries")["value"].mean()
            cov = pd.DataFrame({"before": pre, "after": dur}).dropna()
            cov["pct"] = ((cov["after"] - cov["before"]) / cov["before"] * 100).round(1)
            cov = cov.sort_values("pct", ascending=True)

            colors_c = ["#DC2626" if x < 0 else "#059669" for x in cov["pct"]]

            fig, ax = plt.subplots(figsize=(10, 7))
            bars = ax.barh(cov.index, cov["pct"], color=colors_c,
                           height=0.6, edgecolor="white", linewidth=0.5)
            for bar, val in zip(bars, cov["pct"]):
                xp = val + 0.5 if val >= 0 else val - 0.5
                ha = "left" if val >= 0 else "right"
                ax.text(xp, bar.get_y() + bar.get_height() / 2,
                        f"{val:+.1f}%", va="center", ha=ha, fontsize=9,
                        fontweight="bold", color="#059669" if val >= 0 else "#DC2626")
            ax.axvline(0, color="black", linewidth=0.8, alpha=0.4)
            ax.set_xlabel(f"Change: {year_b} vs {year_a} (%)", fontsize=10)
            ax.set_title(f"Business Formation Change: {year_a} → {year_b}",
                         fontsize=12, fontweight="bold")
            ax.tick_params(axis="y", labelsize=9)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            winners = cov[cov["pct"] > 0].shape[0]
            losers  = cov[cov["pct"] < 0].shape[0]
            st.info(f"**{winners} industries grew**, {losers} declined between {year_a} and {year_b}.")

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — 2025–2026 Momentum
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("2025–2026 Current Momentum")
    st.caption("Average monthly business formations — where Singapore's economy is heading now.")

    col_l, col_r = st.columns([1, 3])
    with col_l:
        momentum_start = st.selectbox(
            "Period start",
            options=["2024-01-01", "2025-01-01", "2023-01-01"],
            index=1,
        )

    with col_r:
        lat  = df[df["date"] >= momentum_start]
        lavg = lat.groupby("DataSeries")["value"].mean().sort_values(ascending=True)

        bar_colors = []
        for ind in lavg.index:
            if ind in ["Information & Communications", "Finance & Insurance", "Professional Services"]:
                bar_colors.append("#2563EB")
            elif ind == "Transportation & Storage":
                bar_colors.append("#DC2626")
            else:
                bar_colors.append("#94A3B8")

        fig, ax = plt.subplots(figsize=(10, 7))
        bars = ax.barh(lavg.index, lavg.values, color=bar_colors,
                       height=0.6, edgecolor="white", linewidth=0.5)
        for bar, val in zip(bars, lavg.values):
            ax.text(val + 8, bar.get_y() + bar.get_height() / 2,
                    f"{int(val):,}/mo", va="center", fontsize=9,
                    fontweight="bold", color="#374151")
        ax.set_xlabel("Avg Monthly Business Formations", fontsize=10)
        ax.set_title(f"Industry Momentum (from {momentum_start[:7]})",
                     fontsize=12, fontweight="bold")
        ax.tick_params(axis="y", labelsize=9)

        from matplotlib.patches import Patch
        ax.legend(handles=[
            Patch(facecolor="#2563EB", label="High-growth sectors"),
            Patch(facecolor="#DC2626", label="Declining sector"),
            Patch(facecolor="#94A3B8", label="Stable sectors"),
        ], loc="lower right", fontsize=8)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        top3 = lavg.nlargest(3)
        total = int(lavg.sum())
        top3_pct = int(top3.sum() / lavg.sum() * 100)
        st.info(
            f"**Top 3 sectors account for {top3_pct}% of all formations:**  \n"
            f"{top3.index[0]} ({int(top3.iloc[0]):,}/mo), "
            f"{top3.index[1]} ({int(top3.iloc[1]):,}/mo), "
            f"{top3.index[2]} ({int(top3.iloc[2]):,}/mo)  \n"
            f"**Total across all industries:** {total:,} new businesses/month"
        )

# ── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Data: Singapore Department of Statistics via data.gov.sg · "
    "Built by Wong Kee Siong · "
    "[GitHub](https://github.com/keesiong111/singapore-business-formation-analysis)"
)
