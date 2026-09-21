"""
Yammer engagement drop case study — load & validate SQL.

Step 1:
Loads the CSV exported from Mode (week, event_name, events, distinct_users)
and checks it by recreating percent_change in Pandas, comparing
against SQL output.
"""

import pandas as pd
import os
import matplotlib.pyplot as plt

# --- Load truncated data from Mode as CSV ---
df = pd.read_csv("yammer_weekly_engagement.csv", parse_dates=["week"])

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

# --- Save the cleaned/reshaped version ---
if not os.path.isfile("yammer_weekly_engagement_clean.csv"):
    df.to_csv("yammer_weekly_engagement_clean.csv", index=False)
    print("\nSaved cleaned data to yammer_weekly_engagement_clean.csv")

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
if not os.path.isfile("events_trend.png"):
    fig.savefig("events_trend.png", dpi=150)
    print("\nSaved plot to events_trend.png")
plt.close(fig)

 
# --- Plot 2: percent_change, one subplot per core event ---
# Skip first two weeks: week 1 has no prior week (NaN), and week 2's
# ~100% change is an artifact of comparing to a partial first week

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
fig.savefig("core_events_pct_change.png", dpi=150)
plt.close(fig)
print("Saved plot to core_events_pct_change.png")



"""
Step 2: find events per user.

Answers: did the drop happen because fewer distinct users showed up,
or because the same users engaged less? Compares three series side by
side, each as % change week-over-week: events, distinct_users, and
events_per_user (events / distinct_users).
"""

# --- Load data from Step 1 ---
df = pd.read_csv("yammer_weekly_engagement_clean.csv", parse_dates=["week"])
df = df.sort_values(["event_name", "week"]).reset_index(drop=True)

# --- Core metric: events per user -----------------------------------------
df["events_per_user"] = df["events"] / df["distinct_users"]

# --- Week-over-week % change for all three series -------------------------
for col in ["events", "distinct_users", "events_per_user"]:
    prev_col = f"prev_{col}"
    pct_col = f"pct_change_{col}"
    df[prev_col] = df.groupby("event_name")[col].shift(1)
    df[pct_col] = (df[col] - df[prev_col]) / df[prev_col] * 100

# --- Compare the three % changes for the core events during the dip -------
pct_cols = ["pct_change_events", "pct_change_distinct_users", "pct_change_events_per_user"]
comparison = df[
    df["event_name"].isin(CORE_EVENTS) & df["week"].isin(pd.to_datetime(DIP_WEEKS))
][["week", "event_name"] + pct_cols].copy()
comparison[pct_cols] = comparison[pct_cols].round(1)

comparison = comparison.sort_values(["event_name", "week"])
print("Percent change during the dip weeks — events vs. distinct_users vs. events_per_user:\n")
print(comparison.to_string(index=False))

# --- Summary: average pct_change across the 4 dip weeks, per event --------
summary = (
    comparison.groupby("event_name")[
        ["pct_change_events", "pct_change_distinct_users", "pct_change_events_per_user"]
    ]
    .mean()
    .round(1)
)
print("\nAverage percent change across the 4 dip weeks (per event):\n")
print(summary.to_string())

# --- Save for plotting / further analysis ----------------------------------
df.to_csv("yammer_events_per_user.csv", index=False)
print("\nSaved yammer_events_per_user.csv")