"""
Yammer engagement drop case study — load & validate SQL.

Step 1:
Loads the CSV exported from Mode (week, event_name, events, distinct_users)
and checks it by recreating percent_change in Pandas, comparing
against SQL output.
"""

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# --- Load truncated data from Mode as CSV ---
df = pd.read_csv("data/yammer_weekly_engagement.csv", parse_dates=["week"])

print("Shape:", df.shape)
print("\nDtypes:\n", df.dtypes)
print("\nEvent names:", sorted(df["event_name"].unique()))
print("\nDate range:", df["week"].min(), "to", df["week"].max())

# --- Structural check: every event should have one row per week ---
n_weeks = df["week"].nunique()
rows_per_event = df.groupby("event_name")["week"].nunique()
missing = rows_per_event[rows_per_event != n_weeks]
if len(missing):
    print("\nEvents with missing weeks:\n", missing)
else:
    print(f"\nAll {df['event_name'].nunique()} events have all {n_weeks} weeks.")

# --- Recreate percent_change (float division, no truncation) ---
df = df.sort_values(["event_name", "week"]).reset_index(drop=True)
df["prev_events"] = df.groupby("event_name")["events"].shift(1)
df["percent_change"] = (df["events"] - df["prev_events"]) / df["prev_events"] * 100

# --- Spot-check against SQL output ---
# SQL (ROUND(100*(events-prev_events)/NULLIF(prev_events,0),1)) reported
# whole numbers for every row  — e.g. home_page 2014-08-04 -> -13.
#  true value is -13.676%. SQL query truncated toward zero 
#   instead of rounding (likely integer division before ROUND()).
# checks = [
#     ("home_page", "2014-08-04", -13),
#     ("home_page", "2014-08-11", -9),
#     ("search_click_result_10", "2014-05-05", 73),
# ]
# print("\nSQL vs. Pandas percent_change comparison:")
# for event, week, sql_value in checks:
#     row = df[(df["event_name"] == event) & (df["week"] == week)]
#     if row.empty:
#         print(f"  {event} {week}: not found in CSV — check event name/date format")
#         continue
#     exact = row["percent_change"].iloc[0]
#     print(f"  {event} {week}: SQL reported {sql_value}, exact value is {exact:.2f}")

# --- Save the cleaned version ---
if not os.path.isfile("data/yammer_weekly_engagement_clean.csv"):
    df.to_csv("data/yammer_weekly_engagement_clean.csv", index=False)
    print("\nSaved cleaned data to data/yammer_weekly_engagement_clean.csv")

# --- Plot 1: raw event counts over time ---
ALL_EVENTS = df["event_name"].unique()
DIP_START = pd.Timestamp("2014-08-04")

fig, ax = plt.subplots(figsize=(10, 6))
for event in ALL_EVENTS:
    subset = df[df["event_name"] == event]
    ax.plot(subset["week"], subset["events"], marker="o", label=event)
ax.axvline(DIP_START, color="red", linestyle="--", alpha=0.6, label="Dip starts (2014-08-04)")
ax.set_xlabel("Week")
ax.set_ylabel("Events")
ax.set_title("Weekly engagement events")
ax.legend()
fig.autofmt_xdate()
fig.tight_layout()
if not os.path.isfile("figures/events_trend.png"):
    fig.savefig("figures/events_trend.png", dpi=150)
    print("\nSaved plot to figures/events_trend.png")
plt.close(fig)

 
# --- Plot 2: percent_change, one subplot per core event ---
# Skip first two weeks: week 1 has no prior week (NaN), and week 2's
# near 100% change is artifact of comparing to partial first week

CORE_EVENTS = ["home_page", "login", "like_message", "send_message", "view_inbox"]
DIP_WEEKS = ["2014-08-04", "2014-08-11", "2014-08-18", "2014-08-25"]

weeks_sorted = sorted(df["week"].unique())
plot_start = weeks_sorted[2] if len(weeks_sorted) > 2 else weeks_sorted[0]

fig, axes = plt.subplots(len(CORE_EVENTS), 1, figsize=(9, 12), sharex=True)
for ax, event in zip(axes, CORE_EVENTS):
    subset = df[(df["event_name"] == event) & (df["week"] >= plot_start)]
    ax.bar(subset["week"], subset["percent_change"], width=5, color="steelblue")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(DIP_START, color="red", linestyle="--", alpha=0.6)
    ax.set_title(event, loc="left", fontsize=10)
    ax.set_ylabel("% change")
axes[-1].set_xlabel("Week")
fig.suptitle("Week-over-week percent change — core events", y=1.0)
fig.autofmt_xdate()
fig.tight_layout()
if not os.path.isfile("figures/core_events_pct_change.png"):
    fig.savefig("figures/core_events_pct_change.png", dpi=150)
    print("Saved plot to figures/core_events_pct_change.png")
plt.close(fig)


"""
Step 2: find events per user.

Investigate if drop happened because fewer distinct users showed up,
or because the same users engaged less. Compares three values side by
side as percent change week-over-week: events, distinct_users, and
events_per_user (events / distinct_users).
"""

df = pd.read_csv("data/yammer_weekly_engagement_clean.csv", parse_dates=["week"])
df = df.sort_values(["event_name", "week"]).reset_index(drop=True)

# --- Calculate events per user ---
df["events_per_user"] = df["events"] / df["distinct_users"]

# --- Week-over-week % change for all three columns ---
for col in ["events", "distinct_users", "events_per_user"]:
    prev_col = f"prev_{col}"
    pct_col = f"pct_change_{col}"
    df[prev_col] = df.groupby("event_name")[col].shift(1)
    df[pct_col] = (df[col] - df[prev_col]) / df[prev_col] * 100

# --- Save for events per user ---
if not os.path.isfile("data/yammer_events_per_user.csv"):
    df.to_csv("data/yammer_events_per_user.csv", index=False)
    print("\nSaved as data/yammer_events_per_user.csv")

# --- Compare three pct changes for core events during dip as copy ---
pct_cols = ["pct_change_events", "pct_change_distinct_users", "pct_change_events_per_user"]
comparison = df[
    df["event_name"].isin(CORE_EVENTS) & df["week"].isin(pd.to_datetime(DIP_WEEKS))
][["week", "event_name"] + pct_cols].copy()
comparison[pct_cols] = comparison[pct_cols].round(1)

comparison = comparison.sort_values(["event_name", "week"])
print("Percent change during the dip weeks — events vs. distinct_users vs. events_per_user:\n")
print(comparison.to_string(index=False))

# --- Summary: average pct_change across the 4 dip weeks, per event ---
summary = (
    comparison.groupby("event_name")[
        ["pct_change_events", "pct_change_distinct_users", "pct_change_events_per_user"]
    ]
    .mean()
    .round(1)
)
print("\nAverage percent change across the 4 dip weeks (per event):\n")
print(summary.to_string())

# --- Order events by total drop size, largest first, for plots ---
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

"""
Step 3: users vs. per-user contribution.

 For each event's average drop during the dip weeks, determine how much of drop is from
fewer distinct users vs. lower per-user activity. Generate plots:
  1. Raw pct_change components stacked (users + per-user = ~ total drop)
  2. Each component's share of the total drop, normalized to 100%
"""

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
if not os.path.isfile("figures/users_vs_per_user_contribution.png"):
    fig.savefig("figures/users_vs_per_user_contribution.png", dpi=150)
    print("\nSaved plot to figures/users_vs_per_user_contribution.png")
plt.close(fig)


# --- Plot 2: share of total drop, normalized to 100% using log pct change ---
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
if os.path.isfile("figures/share_of_drop.png"):
    fig.savefig("figures/share_of_drop.png", dpi=150)
    print("\nSaved plot to figures/share_of_drop.png")
plt.close(fig)