WITH cohorts AS (
  SELECT
    user_id,
    CASE
      WHEN ('2014-06-30'::date - created_at::date) < 30 THEN '0-1 month'
      WHEN ('2014-06-30'::date - created_at::date) < 90 THEN '1-3 months'
      ELSE '3+ months'
    END AS cohort
  FROM tutorial.yammer_users
  WHERE created_at < '2014-06-30'
)
SELECT
  DATE_TRUNC('week', e.occurred_at) AS week,
  c.cohort,
  CASE
    WHEN e.device IN ('amazon fire phone','htc one','iphone 4s','iphone 5','iphone 5s',
                      'nexus 5','nokia lumia 635','samsung galaxy note','samsung galaxy s4',
                      'ipad air','ipad mini','kindle fire','nexus 10','nexus 7',
                      'samsumg galaxy tablet') THEN 'mobile'
    ELSE 'desktop/laptop'
  END AS device_group,
  COUNT(*) AS events,
  COUNT(DISTINCT e.user_id) AS distinct_users
FROM tutorial.yammer_events e
JOIN cohorts c ON e.user_id = c.user_id
WHERE e.event_type = 'engagement'
GROUP BY 1, 2, 3
ORDER BY 2, 3, 1