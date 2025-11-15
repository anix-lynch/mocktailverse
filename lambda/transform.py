"""
AWS Lambda Function for Mocktailverse Data Transformation
=========================================================

This Lambda function performs serverless data transformation as part of the AWS ETL pipeline.
It enriches cocktail data with additional metadata and performs lightweight transformations.

Features:
- Serverless execution (AWS Lambda free tier: 1M requests/month)
- Automatic scaling
- Cost-effective for sporadic workloads
- Integrates with S3 and DynamoDB

Input: S3 location of transformed cocktail data
Output: Enriched data written back to S3

Free Tier Compliant: Uses Lambda's generous free tier allocation.
"""

import json
import boto3
import logging
from datetime import datetime
from typing import Dict, List, Any
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for cocktail data enrichment.

    Args:
        event: Lambda event containing S3 bucket and key information
        context: Lambda context object

    Returns:
        Dict containing processing results
    """
    try:
        logger.info("Starting Lambda transformation for Mocktailverse")

        # Extract parameters from event
        input_bucket = event.get('input_bucket', 'mocktailverse-processed-data')
        output_bucket = event.get('output_bucket', 'mocktailverse-processed-data')
        date_partition = event.get('date_partition', datetime.now().strftime('%Y/%m/%d'))

        # Process data
        enriched_data = enrich_cocktail_data(input_bucket, date_partition)

        # Write enriched data back to S3
        output_key = f'enriched/{date_partition}/enriched_cocktail_data.json'
        write_to_s3(enriched_data, output_bucket, output_key)

        # Optional: Write summary to DynamoDB
        write_processing_summary(enriched_data, date_partition)

        logger.info(f"Successfully processed {len(enriched_data)} cocktail recipes")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data enrichment completed successfully',
                'records_processed': len(enriched_data),
                'output_location': f's3://{output_bucket}/{output_key}'
            })
        }

    except Exception as e:
        logger.error(f"Error in Lambda transformation: {str(e)}")
        raise

def enrich_cocktail_data(input_bucket: str, date_partition: str) -> List[Dict[str, Any]]:
    """
    Enrich cocktail data with additional metadata and transformations.

    Args:
        input_bucket: S3 bucket containing input data
        date_partition: Date partition for data lookup

    Returns:
        List of enriched cocktail recipes
    """
    # Read data from S3
    input_key = f'transformed/{date_partition}/transformed_cocktail_data.json'
    cocktail_data = read_from_s3(input_bucket, input_key)

    enriched_recipes = []

    for cocktail in cocktail_data:
        enriched_cocktail = enrich_single_cocktail(cocktail)
        enriched_recipes.append(enriched_cocktail)

    return enriched_recipes

def enrich_single_cocktail(cocktail: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich a single cocktail recipe with additional metadata.

    Args:
        cocktail: Original cocktail data

    Returns:
        Enriched cocktail data
    """
    # Create a copy to avoid modifying original
    enriched = cocktail.copy()

    # Add enrichment timestamp
    enriched['enriched_at'] = datetime.now().isoformat()

    # Calculate ingredient complexity score
    ingredients = enriched.get('ingredients', [])
    enriched['ingredient_count'] = len(ingredients)
    enriched['complexity_score'] = calculate_complexity_score(ingredients)

    # Add preparation metadata
    instructions = enriched.get('instructions', '')
    enriched['instruction_word_count'] = len(instructions.split())
    enriched['estimated_prep_time'] = estimate_prep_time(ingredients, instructions)

    # Add category metadata
    enriched['is_alcoholic'] = 'rum' in ' '.join([ing.get('name', '').lower() for ing in ingredients])
    enriched['spirit_type'] = identify_spirit_type(ingredients)

    # Add nutritional estimates (simplified)
    enriched['estimated_calories'] = estimate_calories(ingredients)

    # Add tags for searchability
    enriched['tags'] = generate_tags(cocktail)

    return enriched

def calculate_complexity_score(ingredients: List[Dict[str, Any]]) -> float:
    """
    Calculate a complexity score based on ingredients.

    Args:
        ingredients: List of ingredient dictionaries

    Returns:
        Complexity score (0.0 to 10.0)
    """
    score = 0.0

    # Base score from ingredient count
    score += min(len(ingredients) * 0.5, 3.0)

    # Bonus for specialty ingredients
    specialty_ingredients = ['elderflower', 'orgeat', 'falernum', 'amaro', 'chartreuse']
    for ingredient in ingredients:
        name = ingredient.get('name', '').lower()
        if any(specialty in name for specialty in specialty_ingredients):
            score += 1.0

    # Bonus for fresh ingredients
    fresh_indicators = ['juice', 'mint', 'lemon', 'lime', 'orange']
    for ingredient in ingredients:
        name = ingredient.get('name', '').lower()
        if any(fresh in name for fresh in fresh_indicators):
            score += 0.5

    return min(score, 10.0)

def estimate_prep_time(ingredients: List[Dict[str, Any]], instructions: str) -> int:
    """
    Estimate preparation time in minutes.

    Args:
        ingredients: List of ingredients
        instructions: Preparation instructions

    Returns:
        Estimated preparation time in minutes
    """
    base_time = 3  # Base mixing time

    # Add time for muddling
    if 'muddle' in instructions.lower():
        base_time += 2

    # Add time for shaking
    if 'shake' in instructions.lower():
        base_time += 1

    # Add time for multiple steps
    steps = instructions.count('.') + instructions.count(';')
    base_time += max(0, steps - 2)

    return min(base_time, 15)  # Cap at 15 minutes

def identify_spirit_type(ingredients: List[Dict[str, Any]]) -> str:
    """
    Identify the primary spirit type in the cocktail.

    Args:
        ingredients: List of ingredients

    Returns:
        Primary spirit type or 'non-alcoholic'
    """
    spirit_map = {
        'vodka': ['vodka', 'absolut', 'smirnoff'],
        'gin': ['gin', 'hendrick', 'tanqueray'],
        'rum': ['rum', 'bacardi', 'havana club'],
        'tequila': ['tequila', 'patron', 'reposado'],
        'whiskey': ['whiskey', 'bourbon', 'scotch', 'rye'],
        'brandy': ['brandy', 'cognac', 'armagnac']
    }

    for spirit, keywords in spirit_map.items():
        for ingredient in ingredients:
            name = ingredient.get('name', '').lower()
            if any(keyword in name for keyword in keywords):
                return spirit

    return 'non-alcoholic'

def estimate_calories(ingredients: List[Dict[str, Any]]) -> int:
    """
    Estimate calories based on ingredients (simplified calculation).

    Args:
        ingredients: List of ingredients

    Returns:
        Estimated calories
    """
    total_calories = 0

    # Rough calorie estimates per ingredient type
    calorie_map = {
        'rum': 97,      # per oz
        'vodka': 64,    # per oz
        'gin': 70,      # per oz
        'tequila': 69,  # per oz
        'whiskey': 70,  # per oz
        'brandy': 65,   # per oz
        'triple sec': 75,  # per oz
        'lime juice': 8,   # per oz
        'simple syrup': 53, # per oz
        'soda': 0,      # per oz
    }

    for ingredient in ingredients:
        name = ingredient.get('name', '').lower()
        amount = float(ingredient.get('amount', 0))

        # Find matching ingredient
        for key, calories_per_oz in calorie_map.items():
            if key in name:
                total_calories += int(calories_per_oz * amount)
                break

    return total_calories

def generate_tags(cocktail: Dict[str, Any]) -> List[str]:
    """
    Generate search tags for the cocktail.

    Args:
        cocktail: Cocktail data

    Returns:
        List of tags
    """
    tags = []

    # Add category
    category = cocktail.get('category', '').lower()
    if category:
        tags.append(category)

    # Add glass type
    glass = cocktail.get('glass', '').lower()
    if glass:
        tags.append(glass)

    # Add spirit type
    ingredients = cocktail.get('ingredients', [])
    spirit = identify_spirit_type(ingredients)
    if spirit != 'non-alcoholic':
        tags.append(spirit)

    # Add preparation style
    instructions = cocktail.get('instructions', '').lower()
    if 'shake' in instructions:
        tags.append('shaken')
    if 'stir' in instructions:
        tags.append('stirred')
    if 'muddle' in instructions:
        tags.append('muddled')

    # Add complexity level
    complexity = calculate_complexity_score(ingredients)
    if complexity < 3:
        tags.append('simple')
    elif complexity < 6:
        tags.append('intermediate')
    else:
        tags.append('complex')

    return list(set(tags))  # Remove duplicates

def read_from_s3(bucket: str, key: str) -> List[Dict[str, Any]]:
    """
    Read JSON data from S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        Parsed JSON data
    """
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        return data if isinstance(data, list) else [data]
    except ClientError as e:
        logger.error(f"Error reading from S3: {e}")
        raise

def write_to_s3(data: List[Dict[str, Any]], bucket: str, key: str) -> None:
    """
    Write JSON data to S3.

    Args:
        data: Data to write
        bucket: S3 bucket name
        key: S3 object key
    """
    try:
        json_data = json.dumps(data, indent=2, default=str)
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json_data,
            ContentType='application/json'
        )
        logger.info(f"Successfully wrote data to s3://{bucket}/{key}")
    except ClientError as e:
        logger.error(f"Error writing to S3: {e}")
        raise

def write_processing_summary(data: List[Dict[str, Any]], date_partition: str) -> None:
    """
    Write processing summary to DynamoDB.

    Args:
        data: Processed data
        date_partition: Date partition
    """
    try:
        summary = {
            'date_partition': {'S': date_partition},
            'processed_at': {'S': datetime.now().isoformat()},
            'record_count': {'N': str(len(data))},
            'total_ingredients': {'N': str(sum(c.get('ingredient_count', 0) for c in data))},
            'avg_complexity': {'N': str(sum(c.get('complexity_score', 0) for c in data) / len(data))},
        }

        dynamodb_client.put_item(
            TableName='mocktailverse-processing-summary',
            Item=summary
        )
    except ClientError as e:
        logger.warning(f"Could not write processing summary: {e}")

# For local testing
if __name__ == '__main__':
    # Test the function locally
    test_event = {
        'input_bucket': 'mocktailverse-processed-data',
        'output_bucket': 'mocktailverse-processed-data',
        'date_partition': datetime.now().strftime('%Y/%m/%d')
    }

    result = lambda_handler(test_event, None)
    print("Lambda test result:", result)
