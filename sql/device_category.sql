-- consolidate device categories into desktop/laptop, phone, tablet, other
-- also check distinct users per device category to distinguish between device category usage and user count
WITH categorized AS (
  SELECT
    occurred_at,
    user_id,
    CASE
      WHEN device IN (
        'acer aspire desktop', 'acer aspire notebook', 'asus chromebook',
        'dell inspiron desktop', 'dell inspiron notebook', 'hp pavilion desktop',
        'lenovo thinkpad', 'macbook air', 'macbook pro', 'mac mini', 'windows surface'
      ) THEN 'desktop/laptop'
      WHEN device IN (
        'amazon fire phone', 'htc one', 'iphone 4s', 'iphone 5', 'iphone 5s',
        'nexus 5', 'nokia lumia 635', 'samsung galaxy note', 'samsung galaxy s4'
      ) THEN 'phone'
      WHEN device IN (
        'ipad air', 'ipad mini', 'kindle fire', 'nexus 10', 'nexus 7', 'samsumg galaxy tablet'
      ) THEN 'tablet'
      -- typo for samsung in database
      ELSE 'other'
    END AS device_category
  FROM tutorial.yammer_events
  WHERE event_type = 'engagement'
)
SELECT
  DATE_TRUNC('week', occurred_at) AS week,
  device_category,
  COUNT(*) AS events,
  COUNT(DISTINCT user_id) AS distinct_users
FROM categorized
GROUP BY 1, 2
ORDER BY 2, 1