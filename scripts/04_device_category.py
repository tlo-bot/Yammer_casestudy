"""
Yammer engagement drop case study — Step 4: device category breakdown.

Checks whether drop is concentrated in specific device categories
(phone, tablet, desktop/laptop), and for each category, how much of its drop is
from fewer distinct users vs. lower per-user activity. Use same log method as
Step 3, applied to device_category instead of event_name.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASELINE_WEEKS = ["2014-06-30", "2014-07-07", "2014-07-14", "2014-07-21", "2014-07-28"]
DIP_WEEKS = ["2014-08-04", "2014-08-11", "2014-08-18", "2014-08-25"]

# --- Load data (output of device_categories SQL query) ---
df = pd.read_csv("data/yammer_device_category.csv", parse_dates=["week"])
df = df.sort_values(["device_category", "week"]).reset_index(drop=True)
df["events_per_user"] = df["events"] / df["distinct_users"]

# --- Week-over-week pct change for all three series ---
for col in ["events", "distinct_users", "events_per_user"]:
    df[f"prev_{col}"] = df.groupby("device_category")[col].shift(1)
    df[f"pct_change_{col}"] = (df[col] - df[f"prev_{col}"]) / df[f"prev_{col}"] * 100

# --- Baseline (pre-dip) vs. dip averages, per device category ---
cols = ["events", "distinct_users", "events_per_user"]
baseline = (
    df[df["week"].isin(pd.to_datetime(BASELINE_WEEKS))]
    .groupby("device_category")[cols]
    .mean()
)
dip = df[df["week"].isin(pd.to_datetime(DIP_WEEKS))].groupby("device_category")[cols].mean()

pct_change = ((dip - baseline) / baseline * 100).round(1)
pct_change.columns = [f"pct_change_{c}" for c in pct_change.columns]
print("Percent change, baseline (06-30 to 07-28) vs. dip (08-04 to 08-25):\n")
print(pct_change.to_string())

# --- Share of each category's drop: users vs. per-user, via log-growth ---
log_growth = pd.DataFrame(
    {c: np.log(df[c] / df[f"prev_{c}"]) for c in cols},
    index=df.index,
)
log_growth["week"] = df["week"]
log_growth["device_category"] = df["device_category"]

dip_log = log_growth[log_growth["week"].isin(pd.to_datetime(DIP_WEEKS))]
log_summary = dip_log.groupby("device_category")[cols].mean()

shares = pd.DataFrame(index=log_summary.index)
shares["share_users"] = (log_summary["distinct_users"] / log_summary["events"] * 100).round(1)
shares["share_per_user"] = (log_summary["events_per_user"] / log_summary["events"] * 100).round(1)

summary = pct_change.join(shares)
summary = summary.sort_values("pct_change_events")
print("\nShare of each category's drop — users vs. per-user activity:\n")
print(summary[["pct_change_events", "share_users", "share_per_user"]].to_string())

# --- Plot: share of drop, normalized to 100%, one bar per device category ---
fig, ax = plt.subplots(figsize=(8, 4))
y_pos = range(len(summary))
ax.barh(y_pos, summary["share_users"], color="steelblue", label="distinct_users")
ax.barh(
    y_pos,
    summary["share_per_user"],
    left=summary["share_users"],
    color="indianred",
    label="events_per_user",
)
ax.set_yticks(list(y_pos))
ax.set_yticklabels(summary.index)
ax.axvline(100, color="black", linewidth=0.8)
ax.set_xlabel("Share of total drop (%)")
ax.set_title("Share of each device category's drop: users vs. per-user activity")
ax.legend()
fig.tight_layout()
fig.savefig("figures/device_category_share_of_drop.png", dpi=150)
plt.close(fig)
print("\nSaved plot to figures/device_category_share_of_drop.png")

# --- Save for reference -----------------------------------------------------
df.to_csv("data/yammer_device_category_clean.csv", index=False)
print("Saved data/yammer_device_category_clean.csv")