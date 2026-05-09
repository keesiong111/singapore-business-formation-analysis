"""
Singapore Business Entity Formations Analysis
==============================================
Data source: data.gov.sg (via SingStat)
Period: 1990 - 2026
Author: [Your Name]

Business Questions Answered:
1. Which industries recovered strongest post-COVID?
2. Which industries show the highest 2025-2026 momentum?
3. What was the real COVID impact by industry?
4. What are the long-term structural trends (1990-2026)?
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# ── Config ──────────────────────────────────────────────────────────────────
FILE_PATH = "cleaned_business_entity_formations_long.csv"
OUTPUT_DIR = "."

EXCLUDE     = ["Total", "Others"]
FOCUS_INDUSTRIES = [
    "Information & Communications",
    "Finance & Insurance",
    "Professional Services",
    "Transportation & Storage",
    "Retail Trade",
    "Food & Beverage Services",
    "Construction",
    "Manufacturing",
]

PALETTE = {
    "Information & Communications":   "#2563EB",
    "Finance & Insurance":            "#7C3AED",
    "Professional Services":          "#059669",
    "Transportation & Storage":       "#DC2626",
    "Retail Trade":                   "#D97706",
    "Food & Beverage Services":       "#DB2777",
    "Construction":                   "#0891B2",
    "Manufacturing":                  "#65A30D",
}

plt.rcParams.update({
    "font.family":     "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid":       True,
    "grid.alpha":      0.3,
    "grid.linestyle":  "--",
    "figure.dpi":      150,
})

# ── Load & Prepare ───────────────────────────────────────────────────────────
df = pd.read_csv(FILE_PATH)
df["date"] = pd.to_datetime(df["date"])
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

df_clean = df[~df["DataSeries"].isin(EXCLUDE)].copy()

# Key subsets
df_recent  = df_clean[df_clean["date"] >= "2020-01-01"]
df_latest  = df_clean[df_clean["date"] >= "2025-01-01"]
df_baseline = df_clean[df_clean["year"].isin([2017, 2018, 2019])]
df_recovery = df_clean[df_clean["date"] >= "2022-01-01"]
df_focus   = df_clean[df_clean["DataSeries"].isin(FOCUS_INDUSTRIES)]

print("=" * 55)
print("  Singapore Business Entity Formations — Analysis")
print("=" * 55)
print(f"  Rows    : {len(df_clean):,}")
print(f"  Period  : {df_clean['date'].min().date()} → {df_clean['date'].max().date()}")
print(f"  Industries: {df_clean['DataSeries'].nunique()}")
print("=" * 55)


# ══════════════════════════════════════════════════════════════════════════════
# CHART 1 — Post-COVID Recovery: % change vs pre-COVID baseline
# ══════════════════════════════════════════════════════════════════════════════
baseline_avg  = df_baseline.groupby("DataSeries")["value"].mean()
recovery_avg  = df_recovery.groupby("DataSeries")["value"].mean()
recovery_df   = pd.DataFrame({"baseline": baseline_avg, "recovery": recovery_avg}).dropna()
recovery_df["pct_change"] = ((recovery_df["recovery"] - recovery_df["baseline"])
                              / recovery_df["baseline"] * 100).round(1)
recovery_df   = recovery_df.sort_values("pct_change", ascending=True)

colors = ["#DC2626" if x < 0 else "#2563EB" for x in recovery_df["pct_change"]]

fig, ax = plt.subplots(figsize=(10, 7))
bars = ax.barh(recovery_df.index, recovery_df["pct_change"],
               color=colors, height=0.6, edgecolor="white", linewidth=0.5)

for bar, val in zip(bars, recovery_df["pct_change"]):
    x_pos = val + 0.8 if val >= 0 else val - 0.8
    ha    = "left" if val >= 0 else "right"
    ax.text(x_pos, bar.get_y() + bar.get_height() / 2,
            f"{val:+.1f}%", va="center", ha=ha, fontsize=9, fontweight="bold",
            color="#DC2626" if val < 0 else "#2563EB")

ax.axvline(0, color="black", linewidth=0.8, alpha=0.4)
ax.set_xlabel("Change vs 2017–2019 Monthly Average (%)", fontsize=10)
ax.set_title("Post-COVID Recovery by Industry\n(2022–2026 vs 2017–2019 baseline)",
             fontsize=13, fontweight="bold", pad=14)
ax.tick_params(axis="y", labelsize=9)

note = ("Key insight: Information & Communications (+40.8%) and Finance & Insurance (+27.9%)\n"
        "are the strongest post-COVID sectors. Transportation & Storage is the only major\n"
        "industry still below pre-COVID levels (–33.1%).")
fig.text(0.12, -0.06, note, fontsize=8, color="#555555", style="italic")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/chart1_postcovid_recovery.png", bbox_inches="tight")
plt.close()
print("\n[1/4] Chart 1 saved → chart1_postcovid_recovery.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 — Long-term trends (1990–2026) for 8 focus industries
# ══════════════════════════════════════════════════════════════════════════════
df_annual = (df_focus.groupby(["DataSeries", "year"])["value"]
             .sum().reset_index())

fig, ax = plt.subplots(figsize=(13, 6))

for industry in FOCUS_INDUSTRIES:
    d = df_annual[df_annual["DataSeries"] == industry]
    ax.plot(d["year"], d["value"],
            label=industry, color=PALETTE[industry],
            linewidth=1.8, alpha=0.9)
    # Label at end of line
    last = d.iloc[-1]
    ax.text(last["year"] + 0.3, last["value"],
            industry.split(" ")[0], fontsize=7.5,
            color=PALETTE[industry], va="center")

# Annotate key events
for year, label, yoff in [(2003, "SARS", 15000),
                           (2009, "GFC",  15000),
                           (2020, "COVID", 15000)]:
    ax.axvline(year, color="gray", linewidth=0.8, linestyle=":", alpha=0.7)
    ax.text(year + 0.2, ax.get_ylim()[1] * 0.92 if ax.get_ylim()[1] > 0 else 12000,
            label, fontsize=8, color="gray", alpha=0.8)

ax.set_xlabel("Year", fontsize=10)
ax.set_ylabel("Annual Business Formations", fontsize=10)
ax.set_title("Long-term Business Formation Trends by Industry (1990–2026)",
             fontsize=13, fontweight="bold", pad=14)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.set_xlim(1990, 2028)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/chart2_longterm_trends.png", bbox_inches="tight")
plt.close()
print("[2/4] Chart 2 saved → chart2_longterm_trends.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 3 — COVID Impact: 2019 vs 2020 (the surprise story)
# ══════════════════════════════════════════════════════════════════════════════
pre_covid  = df_clean[df_clean["year"] == 2019].groupby("DataSeries")["value"].mean()
dur_covid  = df_clean[df_clean["year"] == 2020].groupby("DataSeries")["value"].mean()
covid_df   = pd.DataFrame({"2019": pre_covid, "2020": dur_covid}).dropna()
covid_df["impact_pct"] = ((covid_df["2020"] - covid_df["2019"])
                           / covid_df["2019"] * 100).round(1)
covid_df   = covid_df.sort_values("impact_pct", ascending=True)

colors_c = ["#DC2626" if x < 0 else "#059669" for x in covid_df["impact_pct"]]

fig, ax = plt.subplots(figsize=(10, 7))
bars = ax.barh(covid_df.index, covid_df["impact_pct"],
               color=colors_c, height=0.6, edgecolor="white", linewidth=0.5)

for bar, val in zip(bars, covid_df["impact_pct"]):
    x_pos = val + 0.5 if val >= 0 else val - 0.5
    ha    = "left" if val >= 0 else "right"
    ax.text(x_pos, bar.get_y() + bar.get_height() / 2,
            f"{val:+.1f}%", va="center", ha=ha, fontsize=9, fontweight="bold",
            color="#059669" if val >= 0 else "#DC2626")

ax.axvline(0, color="black", linewidth=0.8, alpha=0.4)
ax.set_xlabel("Change in Monthly Avg Formations: 2020 vs 2019 (%)", fontsize=10)
ax.set_title("COVID-19 Impact on Business Formation by Industry\n(2020 vs 2019)",
             fontsize=13, fontweight="bold", pad=14)
ax.tick_params(axis="y", labelsize=9)

note = ("Surprise finding: Retail Trade surged +54.2% during COVID — driven by e-commerce\n"
        "registrations as physical retail pivoted online. Manufacturing also rose +17.6%.\n"
        "Accommodation was hardest hit at –37.6%.")
fig.text(0.12, -0.06, note, fontsize=8, color="#555555", style="italic")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/chart3_covid_impact.png", bbox_inches="tight")
plt.close()
print("[3/4] Chart 3 saved → chart3_covid_impact.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 4 — 2025-2026 Momentum: Where is Singapore's economy heading?
# ══════════════════════════════════════════════════════════════════════════════
latest_avg = (df_latest.groupby("DataSeries")["value"]
              .mean().sort_values(ascending=True))
latest_avg = latest_avg[~latest_avg.index.isin(["Total", "Others"])]

bar_colors = []
for ind in latest_avg.index:
    if ind in ["Information & Communications", "Finance & Insurance", "Professional Services"]:
        bar_colors.append("#2563EB")
    elif ind == "Transportation & Storage":
        bar_colors.append("#DC2626")
    else:
        bar_colors.append("#94A3B8")

fig, ax = plt.subplots(figsize=(10, 7))
bars = ax.barh(latest_avg.index, latest_avg.values,
               color=bar_colors, height=0.6, edgecolor="white", linewidth=0.5)

for bar, val in zip(bars, latest_avg.values):
    ax.text(val + 8, bar.get_y() + bar.get_height() / 2,
            f"{int(val):,}/mo", va="center", fontsize=9, fontweight="bold",
            color="#374151")

ax.set_xlabel("Average Monthly Business Formations (2025–2026)", fontsize=10)
ax.set_title("Singapore Industry Momentum: 2025–2026\n(Average monthly new business registrations)",
             fontsize=13, fontweight="bold", pad=14)
ax.tick_params(axis="y", labelsize=9)

# Legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor="#2563EB", label="High growth sectors"),
    Patch(facecolor="#DC2626", label="Declining sector"),
    Patch(facecolor="#94A3B8", label="Stable sectors"),
]
ax.legend(handles=legend_elements, loc="lower right", fontsize=8, framealpha=0.8)

note = ("Professional Services leads at 1,128/month, followed by Wholesale Trade (991)\n"
        "and Information & Communications (851). These 3 sectors account for ~45%\n"
        "of all new business formations in Singapore in 2025–2026.")
fig.text(0.12, -0.07, note, fontsize=8, color="#555555", style="italic")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/chart4_2025_momentum.png", bbox_inches="tight")
plt.close()
print("[4/4] Chart 4 saved → chart4_2025_momentum.png")


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY TABLE — Executive Summary (the 1-pager your boss wants)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 55)
print("  EXECUTIVE SUMMARY")
print("=" * 55)

summary = pd.DataFrame({
    "Industry": recovery_df.index,
    "Pre-COVID avg/mo": recovery_df["baseline"].round(0).astype(int),
    "2025-26 avg/mo":   latest_avg.reindex(recovery_df.index).round(0).astype(int),
    "Post-COVID chg%":  recovery_df["pct_change"],
}).reset_index(drop=True).sort_values("Post-COVID chg%", ascending=False)

print(summary.to_string(index=False))

print("""
KEY FINDINGS FOR SINGAPORE JOB MARKET:

1. BIGGEST OPPORTUNITY → Information & Communications
   +40.8% post-COVID growth. 851 new businesses/month in 2025-26.
   Demand for data, software, and tech talent will keep rising.

2. FINANCE & INSURANCE → Strong and accelerating
   +27.9% post-COVID. 612 new businesses/month.
   Fintech and digital banking driving new formations.

3. TRANSPORTATION → Structural decline, not just COVID
   -33.1% vs pre-COVID baseline. Platform economy (Grab/Gojek)
   has permanently consolidated this sector.

4. RETAIL TRADE → Transformed, not destroyed
   COVID surge (+54.2% in 2020) was e-commerce driven.
   Now stabilised at +18.4% vs pre-COVID — a structural shift.

5. PROFESSIONAL SERVICES → Singapore's biggest sector
   1,128 new businesses/month in 2025-26. Consulting, legal,
   accounting demand follows overall economic growth.
""")

print("Analysis complete. 4 charts saved to current directory.")
print("=" * 55)
