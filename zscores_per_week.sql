-- Check for sudden drops in engagement; Find percent change of event counts compared to previous week
-- count number of events per week
WITH weekly AS (SELECT
    DATE_TRUNC('week', occurred_at) as week, 
    event_name,
    COUNT(*) as events, 
    COUNT(DISTINCT user_id) AS distinct_users
FROM tutorial.yammer_events
WHERE event_type = 'engagement'
GROUP BY 1, 2
ORDER BY 1),
-- create table with previous week's events
offset_events AS (
  SELECT week,
  event_name,
  events,
  LAG(events) OVER (PARTITION BY event_name ORDER BY week) as prev_events
  FROM weekly
),
-- calculate percent change; shows that dip starts around 08-04
pct_change AS (
  SELECT 
  week,
  event_name,
  events,
  prev_events,
  ROUND(100*(events - prev_events)/NULLIF(prev_events,0),1) AS percent_change
FROM offset_events
ORDER BY event_name, week),
-- Calculate zscores of the dip weeks.
-- determine baseline average and std
baseline AS (
  SELECT
    event_name,
    AVG(events) AS avg_events,
    STDDEV(events) AS std_events
    FROM weekly
    WHERE week IN ('2014-06-23', '2014-06-30', '2014-07-07', '2014-07-14', '2014-07-21', '2014-07-28')
    GROUP BY event_name
),
-- get events for dip weeks
dip_week AS (
  SELECT week, event_name, events
  FROM weekly
  WHERE week IN ('2014-08-04', '2014-08-11', '2014-08-18', '2014-08-25')
) 
-- calculate zscores of dip weeks against baseline events; shows steady decline for home_page, like_message, login, send_message, view_inbox
SELECT 
  d.week,
  d.event_name,
  d.events,
  b.avg_events,
  b.std_events,
  ROUND((d.events - b.avg_events) / NULLIF(b.std_events,0), 1) AS z_score
FROM dip_week d
JOIN baseline b 
ON d.event_name = b.event_name
ORDER BY event_name,week
