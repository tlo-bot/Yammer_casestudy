WITH cohorts AS (
  SELECT
    user_id,
    CASE
      WHEN ('2014-06-30'::date - created_at::date) < 30  THEN '0-1 month'
      WHEN ('2014-06-30'::date - created_at::date) < 90  THEN '1-3 months'
      WHEN ('2014-06-30'::date - created_at::date) < 180 THEN '3-6 months'
      WHEN ('2014-06-30'::date - created_at::date) < 365 THEN '6-12 months'
      ELSE '12+ months'
    END AS cohort
  FROM tutorial.yammer_users
  WHERE created_at < '2014-06-30'
),
cohort_sizes AS (
  SELECT cohort, COUNT(*) AS cohort_size FROM cohorts GROUP BY 1
)
SELECT
  DATE_TRUNC('week', e.occurred_at) AS week,
  c.cohort,
  s.cohort_size,
  COUNT(*) AS events,
  COUNT(DISTINCT e.user_id) AS distinct_users
FROM tutorial.yammer_events e
JOIN cohorts c ON e.user_id = c.user_id
JOIN cohort_sizes s ON c.cohort = s.cohort
WHERE e.event_type = 'engagement'
GROUP BY 1, 2, 3
ORDER BY 2, 1