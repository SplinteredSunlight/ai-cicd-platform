"""
ML-based error classification models for the Self-Healing Debugger.
"""

from typing import List, Dict, Optional, Tuple, Union, Any
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
import joblib
import os
import json
from datetime import datetime
import logging

from models.pipeline_debug import ErrorCategory, PipelineStage, ErrorSeverity, PipelineError

# Configure logging
logger = logging.getLogger(__name__)

class ErrorFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Custom feature extractor for error messages that extracts additional features
    beyond just the text content.
    """
    
    def __init__(self, text_column='message'):
        self.text_column = text_column
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            min_df=2,
            max_df=0.8,
            ngram_range=(1, 3),
            stop_words='english'
        )
        
    def fit(self, X, y=None):
        """Fit the feature extractor to the data."""
        # Extract text features
        text_data = X[self.text_column].fillna('')
        self.vectorizer.fit(text_data)
        return self
        
    def transform(self, X):
        """Transform the data into feature vectors."""
        # Extract text features
        text_data = X[self.text_column].fillna('')
        text_features = self.vectorizer.transform(text_data)
        
        # Extract additional features
        additional_features = self._extract_additional_features(X)
        
        # Combine text features with additional features
        if additional_features is not None:
            # Convert sparse matrix to dense array for concatenation
            combined_features = np.hstack((text_features.toarray(), additional_features))
            return combined_features
        else:
            return text_features
    
    def _extract_additional_features(self, X):
        """Extract additional features from the error data."""
        try:
            # Initialize features array
            n_samples = X.shape[0]
            n_features = 10  # Number of additional features
            features = np.zeros((n_samples, n_features))
            
            for i, (_, row) in enumerate(X.iterrows()):
                # Feature 1: Message length
                features[i, 0] = len(str(row.get(self.text_column, '')))
                
                # Feature 2: Number of lines
                features[i, 1] = str(row.get(self.text_column, '')).count('\n') + 1
                
                # Feature 3-7: Presence of specific keywords
                message = str(row.get(self.text_column, '')).lower()
                features[i, 2] = 1 if 'error' in message else 0
                features[i, 3] = 1 if 'warning' in message else 0
                features[i, 4] = 1 if 'exception' in message else 0
                features[i, 5] = 1 if 'failed' in message else 0
                features[i, 6] = 1 if 'traceback' in message else 0
                
                # Feature 8-10: Context features if available
                context = row.get('context', {})
                if isinstance(context, dict):
                    # Feature 8: Has line number
                    features[i, 7] = 1 if 'line_number' in context else 0
                    
                    # Feature 9: Has surrounding context
                    features[i, 8] = 1 if 'surrounding_context' in context else 0
                    
                    # Feature 10: Context length
                    surrounding_context = context.get('surrounding_context', '')
                    features[i, 9] = len(str(surrounding_context))
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting additional features: {str(e)}")
            return None


class MLErrorClassifier:
    """
    ML-based error classifier for pipeline errors.
    
    This classifier uses machine learning to categorize errors based on their
    content and context. It supports multiple classification targets:
    - Error category (dependency, permission, etc.)
    - Error severity (critical, high, etc.)
    - Pipeline stage (checkout, build, etc.)
    """
    
    def __init__(self, model_dir: str = 'models/trained'):
        """
        Initialize the ML error classifier.
        
        Args:
            model_dir: Directory to store trained models
        """
        self.model_dir = model_dir
        self.models = {}
        self.feature_extractors = {}
        self.training_history = {}
        
        # Ensure model directory exists
        os.makedirs(model_dir, exist_ok=True)
    
    def train(
        self,
        errors: List[Dict],
        target: str = 'category',
        model_type: str = 'random_forest',
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict:
        """
        Train a model to classify errors.
        
        Args:
            errors: List of error dictionaries with message, category, etc.
            target: Classification target ('category', 'severity', or 'stage')
            model_type: Type of model to train ('random_forest', 'naive_bayes', or 'logistic_regression')
            test_size: Proportion of data to use for testing
            random_state: Random seed for reproducibility
            
        Returns:
            Dictionary with training results
        """
        # Convert errors to DataFrame
        df = pd.DataFrame(errors)
        
        # Ensure required columns exist
        required_columns = ['message', target]
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            raise ValueError(f"Missing required columns: {missing}")
        
        # Split data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(
            df, df[target], test_size=test_size, random_state=random_state
        )
        
        # Create feature extractor
        feature_extractor = ErrorFeatureExtractor(text_column='message')
        
        # Create model based on model_type
        if model_type == 'random_forest':
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=None,
                min_samples_split=2,
                random_state=random_state
            )
        elif model_type == 'naive_bayes':
            model = MultinomialNB(alpha=0.1)
        elif model_type == 'logistic_regression':
            model = LogisticRegression(
                C=1.0,
                max_iter=1000,
                random_state=random_state
            )
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # Create pipeline
        pipeline = Pipeline([
            ('features', feature_extractor),
            ('classifier', model)
        ])
        
        # Train model
        pipeline.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = pipeline.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # Cross-validation
        cv_scores = cross_val_score(pipeline, df, df[target], cv=5)
        
        # Save model
        model_path = os.path.join(self.model_dir, f"{target}_{model_type}.joblib")
        joblib.dump(pipeline, model_path)
        
        # Store model in memory
        model_key = f"{target}_{model_type}"
        self.models[model_key] = pipeline
        
        # Record training history
        training_result = {
            'target': target,
            'model_type': model_type,
            'accuracy': accuracy,
            'cv_scores': cv_scores.tolist(),
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'report': report,
            'training_date': datetime.utcnow().isoformat(),
            'num_samples': len(df),
            'model_path': model_path
        }
        
        self.training_history[model_key] = training_result
        
        # Save training history
        history_path = os.path.join(self.model_dir, 'training_history.json')
        with open(history_path, 'w') as f:
            json.dump(self.training_history, f, indent=2)
        
        return training_result
    
    def load_model(self, target: str = 'category', model_type: str = 'random_forest') -> bool:
        """
        Load a trained model from disk.
        
        Args:
            target: Classification target ('category', 'severity', or 'stage')
            model_type: Type of model to load ('random_forest', 'naive_bayes', or 'logistic_regression')
            
        Returns:
            True if model was loaded successfully, False otherwise
        """
        model_key = f"{target}_{model_type}"
        model_path = os.path.join(self.model_dir, f"{model_key}.joblib")
        
        if os.path.exists(model_path):
            try:
                self.models[model_key] = joblib.load(model_path)
                
                # Load training history if available
                history_path = os.path.join(self.model_dir, 'training_history.json')
                if os.path.exists(history_path):
                    with open(history_path, 'r') as f:
                        self.training_history = json.load(f)
                
                return True
            except Exception as e:
                logger.error(f"Error loading model {model_key}: {str(e)}")
                return False
        else:
            logger.warning(f"Model file not found: {model_path}")
            return False
    
    def predict(
        self,
        error_message: str,
        context: Optional[Dict] = None,
        target: str = 'category',
        model_type: str = 'random_forest'
    ) -> Tuple[str, float]:
        """
        Predict the classification of an error message.
        
        Args:
            error_message: The error message text
            context: Additional context for the error
            target: Classification target ('category', 'severity', or 'stage')
            model_type: Type of model to use ('random_forest', 'naive_bayes', or 'logistic_regression')
            
        Returns:
            Tuple of (predicted_class, confidence_score)
        """
        model_key = f"{target}_{model_type}"
        
        # Load model if not already loaded
        if model_key not in self.models:
            if not self.load_model(target, model_type):
                raise ValueError(f"Model {model_key} not found and could not be loaded")
        
        # Create DataFrame with single error
        error_data = {
            'message': error_message,
            'context': context or {}
        }
        df = pd.DataFrame([error_data])
        
        # Get model
        model = self.models[model_key]
        
        # Make prediction
        prediction = model.predict(df)[0]
        
        # Get confidence score if model supports predict_proba
        confidence = 0.0
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(df)[0]
            confidence = max(probabilities)
        
        return prediction, confidence
    
    def classify_error(
        self,
        error: Union[PipelineError, Dict, str],
        model_types: Optional[Dict[str, str]] = None
    ) -> Dict[str, Tuple[str, float]]:
        """
        Classify an error using all available models.
        
        Args:
            error: The error to classify (PipelineError object, dictionary, or string)
            model_types: Dictionary mapping targets to model types to use
                         (defaults to {'category': 'random_forest', 'severity': 'random_forest', 'stage': 'random_forest'})
                         
        Returns:
            Dictionary mapping targets to (prediction, confidence) tuples
        """
        # Set default model types if not provided
        if model_types is None:
            model_types = {
                'category': 'random_forest',
                'severity': 'random_forest',
                'stage': 'random_forest'
            }
        
        # Extract error message and context
        if isinstance(error, PipelineError):
            error_message = error.message
            context = error.context
        elif isinstance(error, dict):
            error_message = error.get('message', '')
            context = error.get('context', {})
        else:
            error_message = str(error)
            context = {}
        
        # Make predictions for each target
        predictions = {}
        for target, model_type in model_types.items():
            try:
                prediction, confidence = self.predict(
                    error_message, context, target, model_type
                )
                predictions[target] = (prediction, confidence)
            except Exception as e:
                logger.error(f"Error predicting {target} with {model_type}: {str(e)}")
                predictions[target] = (None, 0.0)
        
        return predictions
    
    def get_training_history(self) -> Dict:
        """
        Get the training history for all models.
        
        Returns:
            Dictionary with training history
        """
        return self.training_history
    
    def get_model_info(self, target: str = 'category', model_type: str = 'random_forest') -> Dict:
        """
        Get information about a specific model.
        
        Args:
            target: Classification target ('category', 'severity', or 'stage')
            model_type: Type of model ('random_forest', 'naive_bayes', or 'logistic_regression')
            
        Returns:
            Dictionary with model information
        """
        model_key = f"{target}_{model_type}"
        
        if model_key in self.training_history:
            return self.training_history[model_key]
        else:
            return {
                'target': target,
                'model_type': model_type,
                'status': 'not_trained',
                'model_path': os.path.join(self.model_dir, f"{model_key}.joblib")
            }
