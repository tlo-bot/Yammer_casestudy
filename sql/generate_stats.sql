-- select weekly engagement events, counts of events, and distinct users
SELECT
    DATE_TRUNC('week', occurred_at) as week, 
    event_name,
    COUNT(*) as events, 
    COUNT(DISTINCT user_id) AS distinct_users
FROM tutorial.yammer_events
WHERE event_type = 'engagement'
GROUP BY 1, 2
ORDER BY 1