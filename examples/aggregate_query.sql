SELECT zip5, birth_date, gender_category, COUNT(*) AS equivalence_class_size
FROM research_export_clean
GROUP BY zip5, birth_date, gender_category;
