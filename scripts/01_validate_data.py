"""
Yammer engagement drop case study — load & validate SQL.

Step 1:
Loads the CSV exported from Mode (week, event_name, events, distinct_users)
and checks it by recreating percent_change in Pandas, comparing
against SQL output.
"""

import pandas as pd
import matplotlib.pyplot as plt

CORE_EVENTS = ["home_page", "login", "like_message", "send_message", "view_inbox"]
DIP_WEEKS = ["2014-08-04", "2014-08-11", "2014-08-18", "2014-08-25"]
DIP_START = pd.Timestamp("2014-08-04")

# --- Load raw data from Mode as CSV ---
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

# --- Save the cleaned version ---
df.to_csv("data/yammer_weekly_engagement_clean.csv", index=False)
print("\nSaved cleaned data to data/yammer_weekly_engagement_clean.csv")

# --- Plot 1: raw event counts over time, all events ---
ALL_EVENTS = df["event_name"].unique()

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
fig.savefig("figures/events_trend.png", dpi=150)
plt.close(fig)
print("Saved plot to figures/events_trend.png")

# --- Plot 2: percent_change, one subplot per core event ---
# Skip first two weeks: week 1 has no prior week (NaN), and week 2's
# near 100% change is artifact of comparing to partial first week
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
fig.savefig("figures/core_events_pct_change.png", dpi=150)
plt.close(fig)
print("Saved plot to figures/core_events_pct_change.png")
