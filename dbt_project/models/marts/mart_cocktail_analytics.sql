{{ config(materialized='table') }}

-- Analytics mart for cocktail data
-- Provides aggregated insights and KPIs for the cocktail dataset

WITH cocktail_metrics AS (
    SELECT
        -- Cocktail dimensions
        spirit_type,
        category,
        glass,
        is_alcoholic,

        -- Metrics
        COUNT(*) as cocktail_count,
        AVG(complexity_score) as avg_complexity,
        AVG(ingredient_count) as avg_ingredients,
        AVG(estimated_prep_time) as avg_prep_time,
        AVG(estimated_calories) as avg_calories,
        SUM(estimated_calories) as total_calories,

        -- Complexity distribution
        COUNT(CASE WHEN complexity_score < 3 THEN 1 END) as simple_count,
        COUNT(CASE WHEN complexity_score BETWEEN 3 AND 6 THEN 1 END) as intermediate_count,
        COUNT(CASE WHEN complexity_score > 6 THEN 1 END) as complex_count

    FROM {{ ref('stg_cocktails') }}
    GROUP BY spirit_type, category, glass, is_alcoholic
),

cocktail_rankings AS (
    SELECT
        *,
        ROW_NUMBER() OVER (ORDER BY cocktail_count DESC) as popularity_rank,
        ROW_NUMBER() OVER (ORDER BY avg_complexity DESC) as complexity_rank,
        ROW_NUMBER() OVER (ORDER BY avg_calories DESC) as calorie_rank
    FROM cocktail_metrics
)

SELECT
    -- Dimensions
    spirit_type,
    category,
    glass,
    is_alcoholic,

    -- Metrics
    cocktail_count,
    ROUND(avg_complexity, 2) as avg_complexity,
    ROUND(avg_ingredients, 1) as avg_ingredients,
    ROUND(avg_prep_time, 1) as avg_prep_time,
    ROUND(avg_calories, 0) as avg_calories,
    total_calories,

    -- Complexity breakdown
    simple_count,
    intermediate_count,
    complex_count,

    -- Rankings
    popularity_rank,
    complexity_rank,
    calorie_rank,

    -- Calculated fields
    ROUND((simple_count * 100.0 / cocktail_count), 1) as simple_percentage,
    ROUND((intermediate_count * 100.0 / cocktail_count), 1) as intermediate_percentage,
    ROUND((complex_count * 100.0 / cocktail_count), 1) as complex_percentage,

    -- Audit
    CURRENT_TIMESTAMP as created_at

FROM cocktail_rankings

ORDER BY cocktail_count DESC
