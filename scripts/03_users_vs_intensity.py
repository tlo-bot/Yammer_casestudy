"""
Yammer engagement drop case study — Step 3: users vs. per-user contribution.

 For each event's average drop during the dip weeks, determine how much of drop is from
fewer distinct users vs. lower per-user activity. Generate plots:
  1. Raw pct_change components stacked (users + per-user = ~ total drop)
  2. Each component's share of the total drop, normalized to 100%
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

CORE_EVENTS = ["home_page", "login", "like_message", "send_message", "view_inbox"]
DIP_WEEKS = ["2014-08-04", "2014-08-11", "2014-08-18", "2014-08-25"]

# --- Load data from Step 2 ---
df = pd.read_csv("data/yammer_events_per_user.csv", parse_dates=["week"])

# --- Recreate the dip-week summary ---
pct_cols = ["pct_change_events", "pct_change_distinct_users", "pct_change_events_per_user"]
dip = df[df["event_name"].isin(CORE_EVENTS) & df["week"].isin(pd.to_datetime(DIP_WEEKS))]
summary = dip.groupby("event_name")[pct_cols].mean().round(1)

# Order events by total drop size, largest first, for readability in plots
summary = summary.sort_values("pct_change_events")

# --- Compute each component's share of the total drop ---
# Use log-growth for exact 100% split instead of percent change
# Percent changes only approximately additive (users% + per_user% =
# approx total%) --> won't sum exactly 100%. But 
# events = distinct_users * events_per_user so logs of growth add exactly:
#   log(events_growth) = log(users_growth) + log(per_user_growth)

# Log-growth scoped to a throwaway frame (log_growth) for plotting 
# and summary calculation  below
log_cols = ["events", "distinct_users", "events_per_user"]
log_growth = pd.DataFrame(
    {c: np.log(df[c] / df[f"prev_{c}"]) for c in log_cols},
    index=df.index,
)
log_growth["week"] = df["week"]
log_growth["event_name"] = df["event_name"]

dip_log = log_growth[
    log_growth["event_name"].isin(CORE_EVENTS) & log_growth["week"].isin(pd.to_datetime(DIP_WEEKS))
]
log_summary = dip_log.groupby("event_name")[log_cols].mean()

summary["share_users"] = log_summary["distinct_users"] / log_summary["events"] * 100
summary["share_per_user"] = log_summary["events_per_user"] / log_summary["events"] * 100
summary[["share_users", "share_per_user"]] = summary[["share_users", "share_per_user"]].round(1)

print("Average percent change and contribution shares, per event:\n")
print(summary.to_string())

# --- Plot 1: show users and per-user percent change, stacked ---
fig, ax = plt.subplots(figsize=(8, 5))
y_pos = range(len(summary))
ax.barh(y_pos, summary["pct_change_distinct_users"], color="steelblue", label="distinct_users")
ax.barh(
    y_pos,
    summary["pct_change_events_per_user"],
    left=summary["pct_change_distinct_users"],
    color="indianred",
    label="events_per_user",
)
ax.set_yticks(list(y_pos))
ax.set_yticklabels(summary.index)
ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("Average % change during dip weeks")
ax.set_title("Users vs. per-user activity for each event's drop")
ax.legend()
fig.tight_layout()
fig.savefig("figures/users_vs_per_user_contribution.png", dpi=150)
plt.close(fig)
print("\nSaved plot to figures/users_vs_per_user_contribution.png")

# --- Plot 2: share of total drop, normalized to 100% using log-growth ---
fig, ax = plt.subplots(figsize=(8, 5))
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
ax.set_title("Share of each event's drop attributable to users vs. per-user activity")
ax.legend()
fig.tight_layout()
fig.savefig("figures/share_of_drop.png", dpi=150)
plt.close(fig)
print("Saved plot to figures/share_of_drop.png")
