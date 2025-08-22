"""
9P Multi-label Classification using embeddings and One-vs-Rest LogisticRegression
"""

import numpy as np
import pickle
import joblib
from typing import List, Dict, Any, Optional, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, multilabel_confusion_matrix
from sklearn.calibration import CalibratedClassifierCV
import pandas as pd

from ml.embeddings.text_embedder import get_embedder
from control.core.config import settings


class NinePClassifier:
    """Multi-label 9P classifier using embeddings and LogisticRegression"""
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the 9P classifier"""
        self.embedder = get_embedder()
        self.model = None
        self.calibrated_model = None
        self.label_names = [
            'product', 'place', 'price', 'publicity', 'postconsumption',
            'purpose', 'partnerships', 'people', 'planet'
        ]
        self.thresholds = {label: 0.5 for label in self.label_names}
        self.model_path = model_path
        
        if model_path:
            self.load_model(model_path)
        else:
            self._initialize_default_model()
    
    def _initialize_default_model(self):
        """Initialize a default model for inference"""
        # Create a basic multi-output classifier
        base_classifier = LogisticRegression(
            random_state=42,
            max_iter=1000,
            class_weight='balanced'
        )
        
        self.model = MultiOutputClassifier(base_classifier)
        
        # Set default thresholds based on domain knowledge
        self.thresholds = {
            'product': 0.6,      # Higher threshold for product mentions
            'place': 0.5,        # Moderate threshold for place
            'price': 0.7,        # Higher threshold for price discussions
            'publicity': 0.5,    # Moderate threshold for publicity
            'postconsumption': 0.6,  # Higher threshold for reviews/feedback
            'purpose': 0.4,      # Lower threshold for brand purpose
            'partnerships': 0.7, # Higher threshold for partnerships
            'people': 0.5,       # Moderate threshold for people mentions
            'planet': 0.6        # Higher threshold for sustainability
        }
    
    def train(
        self, 
        texts: List[str], 
        labels: List[List[int]], 
        validation_split: float = 0.2,
        calibrate: bool = True
    ) -> Dict[str, Any]:
        """
        Train the 9P classifier
        
        Args:
            texts: List of training texts
            labels: List of multi-label arrays (9 dimensions, 0/1 values)
            validation_split: Fraction of data for validation
            calibrate: Whether to calibrate probabilities
            
        Returns:
            Training metrics and results
        """
        if len(texts) != len(labels):
            raise ValueError("Texts and labels must have the same length")
        
        # Generate embeddings
        print("Generating embeddings...")
        embeddings = self.embedder.encode(texts, batch_size=settings.BATCH_SIZE)
        
        # Convert labels to numpy array
        y = np.array(labels)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            embeddings, y, test_size=validation_split, random_state=42
        )
        
        # Train base model
        print("Training base classifier...")
        base_classifier = LogisticRegression(
            random_state=42,
            max_iter=1000,
            class_weight='balanced'
        )
        
        self.model = MultiOutputClassifier(base_classifier)
        self.model.fit(X_train, y_train)
        
        # Calibrate probabilities if requested
        if calibrate:
            print("Calibrating probabilities...")
            self.calibrated_model = CalibratedClassifierCV(
                self.model, method='isotonic', cv=3
            )
            self.calibrated_model.fit(X_train, y_train)
        
        # Evaluate on validation set
        val_predictions = self.predict_batch([texts[i] for i in range(len(texts)) if i in range(len(X_val))])
        val_probabilities = self.predict_proba_batch([texts[i] for i in range(len(texts)) if i in range(len(X_val))])
        
        # Optimize thresholds
        self._optimize_thresholds(y_val, val_probabilities)
        
        # Calculate metrics
        metrics = self._calculate_metrics(y_val, val_predictions, val_probabilities)
        
        return {
            'training_samples': len(X_train),
            'validation_samples': len(X_val),
            'metrics': metrics,
            'thresholds': self.thresholds
        }
    
    def predict_batch(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        Predict 9P labels for a batch of texts
        
        Args:
            texts: List of texts to classify
            
        Returns:
            List of dictionaries with 9P scores
        """
        if not texts:
            return []
        
        # Generate embeddings
        embeddings = self.embedder.encode(texts, batch_size=settings.BATCH_SIZE)
        
        # Get probabilities
        if self.calibrated_model:
            probabilities = self.calibrated_model.predict_proba(embeddings)
        else:
            probabilities = self.model.predict_proba(embeddings)
        
        # Convert to list of dictionaries
        results = []
        for i in range(len(texts)):
            result = {}
            for j, label in enumerate(self.label_names):
                # Get probability for positive class
                if hasattr(probabilities[j][i], '__len__') and len(probabilities[j][i]) > 1:
                    result[label] = float(probabilities[j][i][1])  # Positive class probability
                else:
                    result[label] = float(probabilities[j][i])
            results.append(result)
        
        return results
    
    def predict_proba_batch(self, texts: List[str]) -> np.ndarray:
        """Get raw probabilities for batch prediction"""
        if not texts:
            return np.array([])
        
        embeddings = self.embedder.encode(texts, batch_size=settings.BATCH_SIZE)
        
        if self.calibrated_model:
            return self.calibrated_model.predict_proba(embeddings)
        else:
            return self.model.predict_proba(embeddings)
    
    def predict_single(self, text: str) -> Dict[str, float]:
        """Predict 9P labels for a single text"""
        return self.predict_batch([text])[0]
    
    def calculate_confidence(self, predictions: Dict[str, float]) -> float:
        """
        Calculate overall confidence score for predictions
        
        Args:
            predictions: Dictionary of 9P predictions
            
        Returns:
            Confidence score between 0 and 1
        """
        scores = list(predictions.values())
        
        # Calculate confidence based on prediction certainty
        # Higher confidence when predictions are closer to 0 or 1
        certainties = [abs(score - 0.5) * 2 for score in scores]
        confidence = np.mean(certainties)
        
        return float(confidence)
    
    def apply_thresholds(self, predictions: Dict[str, float]) -> Dict[str, int]:
        """
        Apply learned thresholds to convert probabilities to binary predictions
        
        Args:
            predictions: Dictionary of 9P probability scores
            
        Returns:
            Dictionary of binary 9P predictions
        """
        binary_predictions = {}
        for label, score in predictions.items():
            threshold = self.thresholds.get(label, 0.5)
            binary_predictions[label] = 1 if score >= threshold else 0
        
        return binary_predictions
    
    def _optimize_thresholds(self, y_true: np.ndarray, y_proba: np.ndarray):
        """Optimize classification thresholds using validation data"""
        from sklearn.metrics import f1_score
        
        for i, label in enumerate(self.label_names):
            best_threshold = 0.5
            best_f1 = 0.0
            
            # Try different thresholds
            for threshold in np.arange(0.1, 0.9, 0.05):
                y_pred = (y_proba[:, i] >= threshold).astype(int)
                f1 = f1_score(y_true[:, i], y_pred, average='binary', zero_division=0)
                
                if f1 > best_f1:
                    best_f1 = f1
                    best_threshold = threshold
            
            self.thresholds[label] = best_threshold
    
    def _calculate_metrics(
        self, 
        y_true: np.ndarray, 
        predictions: List[Dict[str, float]], 
        probabilities: np.ndarray
    ) -> Dict[str, Any]:
        """Calculate comprehensive metrics"""
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support
        
        # Convert predictions to binary format
        y_pred = np.zeros_like(y_true)
        for i, pred_dict in enumerate(predictions):
            binary_pred = self.apply_thresholds(pred_dict)
            for j, label in enumerate(self.label_names):
                y_pred[i, j] = binary_pred[label]
        
        metrics = {}
        
        # Overall metrics
        metrics['accuracy'] = float(accuracy_score(y_true, y_pred))
        
        # Per-label metrics
        label_metrics = {}
        for i, label in enumerate(self.label_names):
            precision, recall, f1, support = precision_recall_fscore_support(
                y_true[:, i], y_pred[:, i], average='binary', zero_division=0
            )
            
            label_metrics[label] = {
                'precision': float(precision),
                'recall': float(recall),
                'f1': float(f1),
                'support': int(support),
                'threshold': self.thresholds[label]
            }
        
        metrics['labels'] = label_metrics
        
        return metrics
    
    def add_rules_features(self, texts: List[str]) -> np.ndarray:
        """
        Add rule-based features to enhance classification
        
        Args:
            texts: List of texts
            
        Returns:
            Feature matrix with rule-based features
        """
        features = []
        
        for text in texts:
            text_lower = text.lower()
            
            # Rule-based features for each 9P
            rule_features = []
            
            # Product features
            product_keywords = ['product', 'quality', 'feature', 'design', 'functionality']
            rule_features.append(sum(1 for kw in product_keywords if kw in text_lower))
            
            # Place features
            place_keywords = ['store', 'location', 'available', 'shop', 'online', 'website']
            rule_features.append(sum(1 for kw in place_keywords if kw in text_lower))
            
            # Price features
            price_keywords = ['price', 'cost', 'expensive', 'cheap', 'value', '$', 'dollar']
            rule_features.append(sum(1 for kw in price_keywords if kw in text_lower))
            
            # Publicity features
            publicity_keywords = ['ad', 'advertisement', 'marketing', 'promotion', 'campaign']
            rule_features.append(sum(1 for kw in publicity_keywords if kw in text_lower))
            
            # Post-consumption features
            postconsumption_keywords = ['review', 'experience', 'feedback', 'satisfied', 'disappointed']
            rule_features.append(sum(1 for kw in postconsumption_keywords if kw in text_lower))
            
            # Purpose features
            purpose_keywords = ['mission', 'values', 'purpose', 'cause', 'social', 'impact']
            rule_features.append(sum(1 for kw in purpose_keywords if kw in text_lower))
            
            # Partnerships features
            partnerships_keywords = ['partnership', 'collaboration', 'sponsor', 'endorsement']
            rule_features.append(sum(1 for kw in partnerships_keywords if kw in text_lower))
            
            # People features
            people_keywords = ['customer service', 'staff', 'employee', 'team', 'support']
            rule_features.append(sum(1 for kw in people_keywords if kw in text_lower))
            
            # Planet features
            planet_keywords = ['sustainable', 'environment', 'eco', 'green', 'climate', 'carbon']
            rule_features.append(sum(1 for kw in planet_keywords if kw in text_lower))
            
            features.append(rule_features)
        
        return np.array(features)
    
    def save_model(self, path: str):
        """Save the trained model"""
        model_data = {
            'model': self.model,
            'calibrated_model': self.calibrated_model,
            'thresholds': self.thresholds,
            'label_names': self.label_names,
            'embedder_model_name': self.embedder.model_name
        }
        
        joblib.dump(model_data, path)
        print(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load a trained model"""
        try:
            model_data = joblib.load(path)
            
            self.model = model_data['model']
            self.calibrated_model = model_data.get('calibrated_model')
            self.thresholds = model_data['thresholds']
            self.label_names = model_data['label_names']
            
            print(f"Model loaded from {path}")
        except Exception as e:
            print(f"Error loading model from {path}: {e}")
            self._initialize_default_model()


# Global classifier instance
_classifier = None

def get_nine_p_classifier() -> NinePClassifier:
    """Get global 9P classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = NinePClassifier()
    return _classifier
