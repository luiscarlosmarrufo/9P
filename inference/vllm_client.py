"""
vLLM client for Stage 2 classification with grammar-constrained JSON output
"""

import json
import requests
from typing import Dict, Any, Optional, List
import openai
from openai import OpenAI

from control.core.config import settings


class VLLMClient:
    """Client for vLLM inference server with grammar-constrained JSON"""
    
    def __init__(self, api_base: Optional[str] = None, model_name: Optional[str] = None):
        """Initialize vLLM client"""
        self.api_base = api_base or settings.VLLM_API_BASE
        self.model_name = model_name or settings.VLLM_MODEL_NAME
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI-compatible client for vLLM"""
        try:
            self.client = OpenAI(
                api_key="EMPTY",  # vLLM doesn't require API key
                base_url=self.api_base
            )
        except Exception as e:
            print(f"Warning: Could not initialize vLLM client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if vLLM server is available"""
        if not self.client:
            return False
        
        try:
            # Try to make a simple request to check availability
            response = requests.get(f"{self.api_base}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def classify_post(
        self,
        text: str,
        platform: str,
        brand_context: Optional[str] = None,
        max_retries: int = 2
    ) -> Optional[Dict[str, Any]]:
        """
        Classify a social media post using vLLM with grammar-constrained JSON
        
        Args:
            text: Text to classify
            platform: Platform (twitter/reddit)
            brand_context: Optional brand context
            max_retries: Maximum number of retries
            
        Returns:
            Classification result or None if failed
        """
        if not self.is_available():
            return None
        
        # Build prompt
        prompt = self._build_classification_prompt(text, platform, brand_context)
        
        # Define JSON schema for grammar constraint
        json_schema = self._get_classification_schema()
        
        for attempt in range(max_retries + 1):
            try:
                # Make request with grammar constraint
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert social media analyst specializing in marketing mix (9P) classification and sentiment analysis. Always respond with valid JSON matching the required schema."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=1000,
                    response_format={"type": "json_object"},
                    extra_body={
                        "guided_json": json_schema,
                        "guided_decoding_backend": "outlines"
                    }
                )
                
                # Parse response
                content = response.choices[0].message.content
                result = json.loads(content)
                
                # Validate and return
                if self._validate_classification_result(result):
                    return {
                        'success': True,
                        'classification': result,
                        'confidence': result.get('confidence', 0.8),
                        'reasoning': result.get('reasoning', ''),
                        'model': self.model_name,
                        'attempt': attempt + 1
                    }
                else:
                    print(f"Invalid classification result on attempt {attempt + 1}")
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error on attempt {attempt + 1}: {e}")
                if attempt == max_retries:
                    return {
                        'success': False,
                        'error': f'JSON decode error: {e}',
                        'raw_response': content if 'content' in locals() else None
                    }
                    
            except Exception as e:
                print(f"vLLM request error on attempt {attempt + 1}: {e}")
                if attempt == max_retries:
                    return {
                        'success': False,
                        'error': str(e)
                    }
        
        return None
    
    def _build_classification_prompt(
        self,
        text: str,
        platform: str,
        brand_context: Optional[str] = None
    ) -> str:
        """Build classification prompt"""
        
        context_section = ""
        if brand_context:
            context_section = f"\n\nBrand Context: {brand_context}"
        
        prompt = f"""
Analyze the following {platform} post and classify it according to the 9P marketing mix framework and sentiment.

Text to analyze: "{text}"{context_section}

Please provide a classification with scores from 0.0 to 1.0 for each dimension:

9P Marketing Mix:
- Product: Features, quality, functionality, design
- Place: Distribution, availability, location, channels
- Price: Cost, value, pricing strategy, affordability
- Publicity: Marketing, advertising, promotion, campaigns
- Post-consumption: Reviews, feedback, experience, satisfaction
- Purpose: Brand mission, values, social impact, CSR
- Partnerships: Collaborations, endorsements, sponsorships
- People: Customer service, community, staff, relationships
- Planet: Sustainability, environmental impact, eco-friendliness

Sentiment Analysis:
- Positive: Favorable, happy, satisfied emotions
- Neutral: Factual, balanced, objective tone
- Negative: Unfavorable, disappointed, critical emotions

Provide your analysis in the following JSON format:
{{
    "product": 0.0,
    "place": 0.0,
    "price": 0.0,
    "publicity": 0.0,
    "postconsumption": 0.0,
    "purpose": 0.0,
    "partnerships": 0.0,
    "people": 0.0,
    "planet": 0.0,
    "sentiment": {{
        "positive": 0.0,
        "neutral": 0.0,
        "negative": 0.0,
        "label": "neu"
    }},
    "confidence": 0.8,
    "reasoning": "Brief explanation of the classification"
}}
"""
        return prompt
    
    def _get_classification_schema(self) -> Dict[str, Any]:
        """Get JSON schema for classification response"""
        return {
            "type": "object",
            "properties": {
                "product": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "place": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "price": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "publicity": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "postconsumption": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "purpose": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "partnerships": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "people": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "planet": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "sentiment": {
                    "type": "object",
                    "properties": {
                        "positive": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "neutral": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "negative": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "label": {"type": "string", "enum": ["pos", "neu", "neg"]}
                    },
                    "required": ["positive", "neutral", "negative", "label"]
                },
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "reasoning": {"type": "string"}
            },
            "required": [
                "product", "place", "price", "publicity", "postconsumption",
                "purpose", "partnerships", "people", "planet", "sentiment",
                "confidence", "reasoning"
            ]
        }
    
    def _validate_classification_result(self, result: Dict[str, Any]) -> bool:
        """Validate classification result structure"""
        required_9p_fields = [
            'product', 'place', 'price', 'publicity', 'postconsumption',
            'purpose', 'partnerships', 'people', 'planet'
        ]
        
        # Check 9P fields
        for field in required_9p_fields:
            if field not in result:
                return False
            if not isinstance(result[field], (int, float)):
                return False
            if not (0.0 <= result[field] <= 1.0):
                return False
        
        # Check sentiment
        if 'sentiment' not in result:
            return False
        
        sentiment = result['sentiment']
        if not isinstance(sentiment, dict):
            return False
        
        required_sentiment_fields = ['positive', 'neutral', 'negative', 'label']
        for field in required_sentiment_fields:
            if field not in sentiment:
                return False
        
        # Validate sentiment scores
        for field in ['positive', 'neutral', 'negative']:
            if not isinstance(sentiment[field], (int, float)):
                return False
            if not (0.0 <= sentiment[field] <= 1.0):
                return False
        
        # Validate sentiment label
        if sentiment['label'] not in ['pos', 'neu', 'neg']:
            return False
        
        return True
    
    def batch_classify(
        self,
        texts: List[str],
        platform: str,
        brand_context: Optional[str] = None,
        batch_size: int = 5
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Classify multiple posts in batches
        
        Args:
            texts: List of texts to classify
            platform: Platform name
            brand_context: Optional brand context
            batch_size: Number of texts to process in parallel
            
        Returns:
            List of classification results
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = []
            
            for text in batch:
                result = self.classify_post(text, platform, brand_context)
                batch_results.append(result)
            
            results.extend(batch_results)
        
        return results
    
    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the loaded model"""
        if not self.is_available():
            return None
        
        try:
            response = requests.get(f"{self.api_base}/v1/models", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting model info: {e}")
        
        return None


class MockVLLMClient(VLLMClient):
    """Mock vLLM client for testing and development"""
    
    def __init__(self):
        """Initialize mock client"""
        self.api_base = "mock://localhost:8000"
        self.model_name = "mock-model"
        self.client = None
    
    def is_available(self) -> bool:
        """Mock is always available"""
        return True
    
    def classify_post(
        self,
        text: str,
        platform: str,
        brand_context: Optional[str] = None,
        max_retries: int = 2
    ) -> Optional[Dict[str, Any]]:
        """
        Mock classification that returns reasonable fake results
        """
        import random
        import hashlib
        
        # Use text hash for consistent results
        text_hash = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        random.seed(text_hash)
        
        # Generate mock scores
        nine_p_scores = {}
        for dimension in ['product', 'place', 'price', 'publicity', 'postconsumption',
                         'purpose', 'partnerships', 'people', 'planet']:
            nine_p_scores[dimension] = round(random.uniform(0.1, 0.9), 2)
        
        # Generate mock sentiment
        sentiment_scores = [random.uniform(0.1, 0.8) for _ in range(3)]
        sentiment_scores = [s / sum(sentiment_scores) for s in sentiment_scores]  # Normalize
        
        sentiment_labels = ['neg', 'neu', 'pos']
        predicted_sentiment = sentiment_labels[sentiment_scores.index(max(sentiment_scores))]
        
        return {
            'success': True,
            'classification': {
                **nine_p_scores,
                'sentiment': {
                    'negative': round(sentiment_scores[0], 2),
                    'neutral': round(sentiment_scores[1], 2),
                    'positive': round(sentiment_scores[2], 2),
                    'label': predicted_sentiment
                },
                'confidence': round(random.uniform(0.6, 0.9), 2),
                'reasoning': f"Mock analysis of {platform} post about {text[:50]}..."
            },
            'confidence': round(random.uniform(0.6, 0.9), 2),
            'reasoning': f"Mock analysis of {platform} post",
            'model': 'mock-model',
            'attempt': 1
        }


# Global client instance
_vllm_client = None

def get_vllm_client() -> VLLMClient:
    """Get global vLLM client instance"""
    global _vllm_client
    if _vllm_client is None:
        if settings.DEBUG:
            _vllm_client = MockVLLMClient()
        else:
            _vllm_client = VLLMClient()
    return _vllm_client
