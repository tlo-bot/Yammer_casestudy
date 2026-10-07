-- investigate for holidays by checking events of each country per week
SELECT
  DATE_TRUNC('week', occurred_at) AS week,
  location,
  COUNT(*) AS events
FROM tutorial.yammer_events
WHERE event_type = 'engagement'
  AND event_name = 'login'
GROUP BY 1, 2
ORDER BY 2, 1