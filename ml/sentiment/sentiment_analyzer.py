"""
Sentiment Analysis using embeddings and classification
"""

import numpy as np
import joblib
from typing import List, Dict, Any, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.calibration import CalibratedClassifierCV

from ml.embeddings.text_embedder import get_embedder
from control.core.config import settings


class SentimentAnalyzer:
    """Sentiment analyzer using embeddings and LogisticRegression"""
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the sentiment analyzer"""
        self.embedder = get_embedder()
        self.model = None
        self.calibrated_model = None
        self.label_names = ['negative', 'neutral', 'positive']
        self.label_mapping = {'neg': 0, 'neu': 1, 'pos': 2}
        self.reverse_mapping = {0: 'neg', 1: 'neu', 2: 'pos'}
        self.model_path = model_path
        
        if model_path:
            self.load_model(model_path)
        else:
            self._initialize_default_model()
    
    def _initialize_default_model(self):
        """Initialize a default model for inference"""
        self.model = LogisticRegression(
            random_state=42,
            max_iter=1000,
            class_weight='balanced',
            multi_class='ovr'
        )
    
    def train(
        self, 
        texts: List[str], 
        labels: List[str], 
        validation_split: float = 0.2,
        calibrate: bool = True
    ) -> Dict[str, Any]:
        """
        Train the sentiment analyzer
        
        Args:
            texts: List of training texts
            labels: List of sentiment labels ('pos', 'neu', 'neg')
            validation_split: Fraction of data for validation
            calibrate: Whether to calibrate probabilities
            
        Returns:
            Training metrics and results
        """
        if len(texts) != len(labels):
            raise ValueError("Texts and labels must have the same length")
        
        # Generate embeddings
        print("Generating embeddings for sentiment analysis...")
        embeddings = self.embedder.encode(texts, batch_size=settings.BATCH_SIZE)
        
        # Convert labels to numeric
        y = np.array([self.label_mapping[label] for label in labels])
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            embeddings, y, test_size=validation_split, random_state=42, stratify=y
        )
        
        # Train base model
        print("Training sentiment classifier...")
        self.model = LogisticRegression(
            random_state=42,
            max_iter=1000,
            class_weight='balanced',
            multi_class='ovr'
        )
        
        self.model.fit(X_train, y_train)
        
        # Calibrate probabilities if requested
        if calibrate:
            print("Calibrating sentiment probabilities...")
            self.calibrated_model = CalibratedClassifierCV(
                self.model, method='isotonic', cv=3
            )
            self.calibrated_model.fit(X_train, y_train)
        
        # Evaluate on validation set
        if self.calibrated_model:
            val_predictions = self.calibrated_model.predict(X_val)
            val_probabilities = self.calibrated_model.predict_proba(X_val)
        else:
            val_predictions = self.model.predict(X_val)
            val_probabilities = self.model.predict_proba(X_val)
        
        # Calculate metrics
        accuracy = accuracy_score(y_val, val_predictions)
        report = classification_report(
            y_val, val_predictions, 
            target_names=self.label_names,
            output_dict=True,
            zero_division=0
        )
        
        return {
            'training_samples': len(X_train),
            'validation_samples': len(X_val),
            'accuracy': accuracy,
            'classification_report': report
        }
    
    def predict_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Predict sentiment for a batch of texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of dictionaries with sentiment scores and labels
        """
        if not texts:
            return []
        
        # Generate embeddings
        embeddings = self.embedder.encode(texts, batch_size=settings.BATCH_SIZE)
        
        # Get predictions and probabilities
        if self.calibrated_model:
            probabilities = self.calibrated_model.predict_proba(embeddings)
            predictions = self.calibrated_model.predict(embeddings)
        else:
            probabilities = self.model.predict_proba(embeddings)
            predictions = self.model.predict(embeddings)
        
        # Convert to list of dictionaries
        results = []
        for i in range(len(texts)):
            # Get probabilities for each class
            neg_prob = float(probabilities[i][0])  # negative
            neu_prob = float(probabilities[i][1])  # neutral
            pos_prob = float(probabilities[i][2])  # positive
            
            # Get predicted label
            predicted_label = self.reverse_mapping[predictions[i]]
            
            result = {
                'negative': neg_prob,
                'neutral': neu_prob,
                'positive': pos_prob,
                'label': predicted_label
            }
            
            results.append(result)
        
        return results
    
    def predict_single(self, text: str) -> Dict[str, Any]:
        """Predict sentiment for a single text"""
        return self.predict_batch([text])[0]
    
    def calculate_confidence(self, predictions: Dict[str, Any]) -> float:
        """
        Calculate confidence score for sentiment predictions
        
        Args:
            predictions: Dictionary with sentiment scores
            
        Returns:
            Confidence score between 0 and 1
        """
        scores = [predictions['negative'], predictions['neutral'], predictions['positive']]
        
        # Confidence is the maximum probability
        max_prob = max(scores)
        
        # Alternative: entropy-based confidence
        # Lower entropy = higher confidence
        entropy = -sum(p * np.log(p + 1e-10) for p in scores if p > 0)
        max_entropy = np.log(3)  # Maximum entropy for 3 classes
        entropy_confidence = 1 - (entropy / max_entropy)
        
        # Combine both measures
        confidence = (max_prob + entropy_confidence) / 2
        
        return float(confidence)
    
    def analyze_sentiment_trends(self, texts: List[str], timestamps: List[str]) -> Dict[str, Any]:
        """
        Analyze sentiment trends over time
        
        Args:
            texts: List of texts
            timestamps: List of timestamp strings
            
        Returns:
            Dictionary with trend analysis
        """
        if len(texts) != len(timestamps):
            raise ValueError("Texts and timestamps must have the same length")
        
        # Get sentiment predictions
        predictions = self.predict_batch(texts)
        
        # Group by time periods (could be enhanced with proper time parsing)
        sentiment_counts = {'pos': 0, 'neu': 0, 'neg': 0}
        sentiment_scores = {'positive': [], 'neutral': [], 'negative': []}
        
        for pred in predictions:
            sentiment_counts[pred['label']] += 1
            sentiment_scores['positive'].append(pred['positive'])
            sentiment_scores['neutral'].append(pred['neutral'])
            sentiment_scores['negative'].append(pred['negative'])
        
        # Calculate statistics
        total = len(predictions)
        
        return {
            'total_texts': total,
            'sentiment_distribution': {
                'positive': sentiment_counts['pos'],
                'neutral': sentiment_counts['neu'],
                'negative': sentiment_counts['neg']
            },
            'sentiment_percentages': {
                'positive': (sentiment_counts['pos'] / total) * 100 if total > 0 else 0,
                'neutral': (sentiment_counts['neu'] / total) * 100 if total > 0 else 0,
                'negative': (sentiment_counts['neg'] / total) * 100 if total > 0 else 0
            },
            'average_scores': {
                'positive': np.mean(sentiment_scores['positive']) if sentiment_scores['positive'] else 0,
                'neutral': np.mean(sentiment_scores['neutral']) if sentiment_scores['neutral'] else 0,
                'negative': np.mean(sentiment_scores['negative']) if sentiment_scores['negative'] else 0
            },
            'overall_sentiment': max(sentiment_counts, key=sentiment_counts.get)
        }
    
    def get_sentiment_keywords(self, texts: List[str], sentiments: List[str]) -> Dict[str, List[str]]:
        """
        Extract keywords associated with different sentiments
        
        Args:
            texts: List of texts
            sentiments: List of corresponding sentiment labels
            
        Returns:
            Dictionary mapping sentiments to common keywords
        """
        from collections import Counter
        import re
        
        sentiment_texts = {'pos': [], 'neu': [], 'neg': []}
        
        # Group texts by sentiment
        for text, sentiment in zip(texts, sentiments):
            sentiment_texts[sentiment].append(text.lower())
        
        # Extract keywords for each sentiment
        sentiment_keywords = {}
        
        for sentiment, text_list in sentiment_texts.items():
            if not text_list:
                sentiment_keywords[sentiment] = []
                continue
            
            # Simple keyword extraction (could be enhanced with NLP)
            all_words = []
            for text in text_list:
                # Extract words (basic tokenization)
                words = re.findall(r'\b\w+\b', text)
                # Filter out common stop words and short words
                words = [w for w in words if len(w) > 3 and w not in {
                    'this', 'that', 'with', 'have', 'will', 'from', 'they', 
                    'been', 'were', 'said', 'each', 'which', 'their', 'time'
                }]
                all_words.extend(words)
            
            # Get most common words
            word_counts = Counter(all_words)
            sentiment_keywords[sentiment] = [word for word, count in word_counts.most_common(20)]
        
        return sentiment_keywords
    
    def save_model(self, path: str):
        """Save the trained model"""
        model_data = {
            'model': self.model,
            'calibrated_model': self.calibrated_model,
            'label_names': self.label_names,
            'label_mapping': self.label_mapping,
            'reverse_mapping': self.reverse_mapping,
            'embedder_model_name': self.embedder.model_name
        }
        
        joblib.dump(model_data, path)
        print(f"Sentiment model saved to {path}")
    
    def load_model(self, path: str):
        """Load a trained model"""
        try:
            model_data = joblib.load(path)
            
            self.model = model_data['model']
            self.calibrated_model = model_data.get('calibrated_model')
            self.label_names = model_data['label_names']
            self.label_mapping = model_data['label_mapping']
            self.reverse_mapping = model_data['reverse_mapping']
            
            print(f"Sentiment model loaded from {path}")
        except Exception as e:
            print(f"Error loading sentiment model from {path}: {e}")
            self._initialize_default_model()


class RuleBased SentimentAnalyzer:
    """Rule-based sentiment analyzer as fallback"""
    
    def __init__(self):
        """Initialize rule-based analyzer"""
        self.positive_words = {
            'good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic', 
            'wonderful', 'perfect', 'love', 'like', 'best', 'happy', 'satisfied',
            'impressed', 'recommend', 'quality', 'beautiful', 'brilliant'
        }
        
        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'worst',
            'disappointed', 'frustrated', 'angry', 'annoyed', 'poor', 'cheap',
            'broken', 'useless', 'waste', 'regret', 'problem', 'issue'
        }
        
        self.intensifiers = {
            'very', 'extremely', 'really', 'quite', 'absolutely', 'totally',
            'completely', 'highly', 'super', 'incredibly'
        }
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using rule-based approach
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores and label
        """
        words = text.lower().split()
        
        positive_score = 0
        negative_score = 0
        
        for i, word in enumerate(words):
            # Check for intensifiers
            intensifier = 1.0
            if i > 0 and words[i-1] in self.intensifiers:
                intensifier = 1.5
            
            # Check for negation
            negation = 1.0
            if i > 0 and words[i-1] in {'not', 'no', 'never', 'nothing', 'nobody'}:
                negation = -1.0
            
            # Score words
            if word in self.positive_words:
                positive_score += intensifier * negation
            elif word in self.negative_words:
                negative_score += intensifier * negation
        
        # Normalize scores
        total_score = positive_score + abs(negative_score)
        if total_score > 0:
            pos_prob = positive_score / total_score
            neg_prob = abs(negative_score) / total_score
            neu_prob = max(0, 1 - pos_prob - neg_prob)
        else:
            pos_prob = neg_prob = 0.0
            neu_prob = 1.0
        
        # Determine label
        if pos_prob > neg_prob and pos_prob > neu_prob:
            label = 'pos'
        elif neg_prob > pos_prob and neg_prob > neu_prob:
            label = 'neg'
        else:
            label = 'neu'
        
        return {
            'positive': pos_prob,
            'neutral': neu_prob,
            'negative': neg_prob,
            'label': label
        }


# Global analyzer instance
_analyzer = None

def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get global sentiment analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer
