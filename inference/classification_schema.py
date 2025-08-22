"""
JSON Schema for 9P classification output validation
"""

CLASSIFICATION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "9P Classification Result",
    "description": "Schema for validating 9P marketing mix classification results",
    "type": "object",
    "properties": {
        "nine_p": {
            "type": "object",
            "description": "9P marketing mix scores",
            "properties": {
                "product": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Product dimension score"
                },
                "place": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Place dimension score"
                },
                "price": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Price dimension score"
                },
                "publicity": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Publicity dimension score"
                },
                "postconsumption": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Post-consumption dimension score"
                },
                "purpose": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Purpose dimension score"
                },
                "partnerships": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Partnerships dimension score"
                },
                "people": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "People dimension score"
                },
                "planet": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Planet dimension score"
                }
            },
            "required": [
                "product", "place", "price", "publicity", "postconsumption",
                "purpose", "partnerships", "people", "planet"
            ],
            "additionalProperties": false
        },
        "sentiment": {
            "type": "object",
            "description": "Sentiment analysis results",
            "properties": {
                "label": {
                    "type": "string",
                    "enum": ["positive", "neutral", "negative"],
                    "description": "Primary sentiment label"
                },
                "positive": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Positive sentiment probability"
                },
                "neutral": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Neutral sentiment probability"
                },
                "negative": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Negative sentiment probability"
                }
            },
            "required": ["label", "positive", "neutral", "negative"],
            "additionalProperties": false
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Overall confidence score for the classification"
        }
    },
    "required": ["nine_p", "sentiment", "confidence"],
    "additionalProperties": false
}

# Grammar file content for vLLM constrained generation
VLLM_GRAMMAR = """
root ::= classification

classification ::= "{" ws "\"nine_p\"" ws ":" ws nine_p_object ws "," ws "\"sentiment\"" ws ":" ws sentiment_object ws "," ws "\"confidence\"" ws ":" ws number ws "}"

nine_p_object ::= "{" ws nine_p_fields ws "}"

nine_p_fields ::= nine_p_field (ws "," ws nine_p_field)*

nine_p_field ::= ("\"product\"" | "\"place\"" | "\"price\"" | "\"publicity\"" | "\"postconsumption\"" | "\"purpose\"" | "\"partnerships\"" | "\"people\"" | "\"planet\"") ws ":" ws number

sentiment_object ::= "{" ws sentiment_fields ws "}"

sentiment_fields ::= sentiment_field (ws "," ws sentiment_field)*

sentiment_field ::= ("\"label\"" ws ":" ws sentiment_label) | ("\"positive\"" ws ":" ws number) | ("\"neutral\"" ws ":" ws number) | ("\"negative\"" ws ":" ws number)

sentiment_label ::= "\"positive\"" | "\"neutral\"" | "\"negative\""

number ::= [0-9]+ ("." [0-9]+)?

ws ::= [ \t\n\r]*
"""

def validate_classification_result(result: dict) -> bool:
    """
    Validate a classification result against the schema
    
    Args:
        result: Dictionary containing classification results
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        import jsonschema
        jsonschema.validate(result, CLASSIFICATION_SCHEMA)
        return True
    except (jsonschema.ValidationError, ImportError):
        return False

def get_classification_template() -> dict:
    """
    Get a template for classification results
    
    Returns:
        dict: Template with default values
    """
    return {
        "nine_p": {
            "product": 0.0,
            "place": 0.0,
            "price": 0.0,
            "publicity": 0.0,
            "postconsumption": 0.0,
            "purpose": 0.0,
            "partnerships": 0.0,
            "people": 0.0,
            "planet": 0.0
        },
        "sentiment": {
            "label": "neutral",
            "positive": 0.0,
            "neutral": 1.0,
            "negative": 0.0
        },
        "confidence": 0.0
    }

def normalize_classification_scores(result: dict) -> dict:
    """
    Normalize classification scores to ensure they sum to reasonable values
    
    Args:
        result: Classification result dictionary
        
    Returns:
        dict: Normalized result
    """
    normalized = result.copy()
    
    # Normalize sentiment probabilities to sum to 1.0
    if "sentiment" in normalized:
        sentiment = normalized["sentiment"]
        total = sentiment.get("positive", 0) + sentiment.get("neutral", 0) + sentiment.get("negative", 0)
        if total > 0:
            sentiment["positive"] = sentiment.get("positive", 0) / total
            sentiment["neutral"] = sentiment.get("neutral", 0) / total
            sentiment["negative"] = sentiment.get("negative", 0) / total
    
    # Ensure 9P scores are within bounds
    if "nine_p" in normalized:
        for key, value in normalized["nine_p"].items():
            normalized["nine_p"][key] = max(0.0, min(1.0, value))
    
    # Ensure confidence is within bounds
    if "confidence" in normalized:
        normalized["confidence"] = max(0.0, min(1.0, normalized["confidence"]))
    
    return normalized
