SELECT DATE_TRUNC('week', created_at) AS week, COUNT(*) AS signups
FROM tutorial.yammer_users
GROUP BY 1
ORDER BY 1