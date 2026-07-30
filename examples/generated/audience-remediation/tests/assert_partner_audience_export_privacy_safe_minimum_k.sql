-- dbt singular test: returns one aggregate metric only when policy fails.
-- It never projects a person-level row or quasi-identifier value.
WITH equivalence_classes AS (
    SELECT
        region, age_band,
        COUNT(*) AS class_size
    FROM {{ ref('partner_audience_export_privacy_safe') }}
    GROUP BY region, age_band
),
privacy_summary AS (
    SELECT MIN(class_size) AS minimum_k
    FROM equivalence_classes
)
SELECT minimum_k
FROM privacy_summary
WHERE minimum_k < 5
