-- dbt singular test: returns one aggregate metric only when policy fails.
-- It never projects a person-level row or quasi-identifier value.
WITH equivalence_classes AS (
    SELECT
        zip5, gender_category,
        COUNT(*) AS class_size
    FROM {{ ref('research_export_clean_privacy_safe') }}
    GROUP BY zip5, gender_category
),
privacy_summary AS (
    SELECT MIN(class_size) AS minimum_k
    FROM equivalence_classes
)
SELECT minimum_k
FROM privacy_summary
WHERE minimum_k < 5
