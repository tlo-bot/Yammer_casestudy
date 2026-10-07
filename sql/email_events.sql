-- investigate email events
-- result: no email sending-related count dips noticed around 8/4 to cause engagement dip, however clickthrough events dropped
SELECT
  DATE_TRUNC('week', occurred_at) AS week,
  action,
  COUNT(*) AS email_events
FROM tutorial.yammer_emails
GROUP BY 1, 2
ORDER BY 2, 1