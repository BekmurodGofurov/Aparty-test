-- Premium first listing feed
SELECT *
FROM listings
WHERE is_active = TRUE
ORDER BY is_premium DESC, created_at DESC;

-- Count listings by source
SELECT source, COUNT(*) AS total
FROM listings
GROUP BY source;
