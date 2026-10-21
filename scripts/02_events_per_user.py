"""
Yammer engagement drop case study — Step 2: events per user.

Investigate if drop happened because fewer distinct users showed up,
or because the same users engaged less. Compares three values side by
side as percent change week-over-week: events, distinct_users, and
events_per_user (events / distinct_users).
"""

import pandas as pd

CORE_EVENTS = ["home_page", "login", "like_message", "send_message", "view_inbox"]
DIP_WEEKS = ["2014-08-04", "2014-08-11", "2014-08-18", "2014-08-25"]

# --- Load the cleaned data from Step 1 ---
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

# --- Save for Step 3 ---
df.to_csv("data/yammer_events_per_user.csv", index=False)
print("Saved data/yammer_events_per_user.csv")

# --- Compare the three pct changes for core events during the dip weeks ---
pct_cols = ["pct_change_events", "pct_change_distinct_users", "pct_change_events_per_user"]
comparison = df[
    df["event_name"].isin(CORE_EVENTS) & df["week"].isin(pd.to_datetime(DIP_WEEKS))
][["week", "event_name"] + pct_cols].copy()
comparison[pct_cols] = comparison[pct_cols].round(1)

comparison = comparison.sort_values(["event_name", "week"])
print("\nPercent change during the dip weeks — events vs. distinct_users vs. events_per_user:\n")
print(comparison.to_string(index=False))

# --- Summary: average pct_change across the 4 dip weeks, per event ---
summary = (
    comparison.groupby("event_name")[
        ["pct_change_events", "pct_change_distinct_users", "pct_change_events_per_user"]
    ]
    .mean()
    .round(1)
)
print("\nAverage week-over-week percent change across the 4 dip weeks (per event):\n")
print(summary.to_string())
