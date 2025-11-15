{{ config(materialized='view') }}

-- Staging model for raw cocktail data from DynamoDB
-- This model cleans and standardizes the raw cocktail data

SELECT
    -- Primary key
    id,

    -- Basic cocktail information
    name,
    category,
    glass,

    -- Ingredients (parsed from JSON array)
    ingredients,

    -- Instructions
    instructions,

    -- Metadata
    extracted_at,
    enriched_at,

    -- Enrichment fields
    ingredient_count,
    complexity_score,
    instruction_word_count,
    estimated_prep_time,
    is_alcoholic,
    spirit_type,
    estimated_calories,
    tags,

    -- Audit fields
    CURRENT_TIMESTAMP as loaded_at

FROM {{ source('dynamodb', 'cocktails') }}

-- Only include valid records
WHERE id IS NOT NULL
  AND name IS NOT NULL
  AND ingredients IS NOT NULL
