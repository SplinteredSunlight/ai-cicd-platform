"""
ML-based error classification models for the Self-Healing Debugger.
"""

from typing import List, Dict, Optional, Tuple, Union, Any
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
import joblib
import os
import json
from datetime import datetime
import logging
import re
from collections import Counter

from models.pipeline_debug import ErrorCategory, PipelineStage, ErrorSeverity, PipelineError

# Configure logging
logger = logging.getLogger(__name__)

class ErrorFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Custom feature extractor for error messages that extracts additional features
    beyond just the text content.
    
    This extractor analyzes error messages and their context to extract meaningful
    features for classification, including:
    - Text-based features using TF-IDF
    - Structural features (message length, line count)
    - Semantic features (error types, keywords)
    - Stack trace features (frame count, library mentions)
    - Context features (line numbers, surrounding code)
    """
    
    # Common error patterns to detect
    ERROR_PATTERNS = {
        'syntax_error': r'syntax\s+error|invalid\s+syntax',
        'import_error': r'import\s+error|no\s+module\s+named|cannot\s+import|module\s+not\s+found',
        'type_error': r'type\s+error|typeerror|cannot\s+(convert|cast)',
        'value_error': r'value\s+error|valueerror|invalid\s+value',
        'key_error': r'key\s+error|keyerror|key\s+not\s+found',
        'index_error': r'index\s+error|indexerror|list\s+index\s+out\s+of\s+range',
        'attribute_error': r'attribute\s+error|attributeerror|has\s+no\s+attribute',
        'io_error': r'io\s+error|ioerror|file\s+not\s+found|no\s+such\s+file',
        'permission_error': r'permission\s+denied|permissionerror|access\s+denied',
        'connection_error': r'connection\s+error|connectionerror|failed\s+to\s+connect',
        'timeout_error': r'timeout|timed\s+out',
        'memory_error': r'memory\s+error|memoryerror|out\s+of\s+memory',
        'assertion_error': r'assertion\s+error|assertionerror|assertion\s+failed',
        'runtime_error': r'runtime\s+error|runtimeerror',
        'null_pointer': r'null\s+pointer|nullpointerexception|none\s+type',
        'undefined_reference': r'undefined\s+reference|not\s+defined',
        'segmentation_fault': r'segmentation\s+fault|segfault|access\s+violation',
        'stack_overflow': r'stack\s+overflow|stackoverflowerror',
        'dependency_conflict': r'dependency\s+conflict|version\s+conflict|incompatible',
        'configuration_error': r'configuration\s+error|config\s+error|misconfigured',
    }
    
    # Common libraries and frameworks to detect
    LIBRARIES = [
        'numpy', 'pandas', 'sklearn', 'tensorflow', 'pytorch', 'torch',
        'django', 'flask', 'fastapi', 'express', 'react', 'angular', 'vue',
        'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'github',
        'npm', 'pip', 'yarn', 'gradle', 'maven', 'cargo', 'go',
        'aws', 'azure', 'gcp', 'firebase', 'mongodb', 'postgresql', 'mysql',
        'redis', 'kafka', 'rabbitmq', 'elasticsearch', 'prometheus', 'grafana'
    ]
    
    def __init__(self, text_column='message', max_features=5000):
        self.text_column = text_column
        self.max_features = max_features
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
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
            n_features = 30  # Increased number of additional features
            features = np.zeros((n_samples, n_features))
            
            for i, (_, row) in enumerate(X.iterrows()):
                message = str(row.get(self.text_column, ''))
                message_lower = message.lower()
                
                # Basic structural features
                # Feature 1: Message length
                features[i, 0] = len(message)
                
                # Feature 2: Number of lines
                features[i, 1] = message.count('\n') + 1
                
                # Feature 3: Average line length
                lines = message.split('\n')
                features[i, 2] = sum(len(line) for line in lines) / max(1, len(lines))
                
                # Feature 4: Maximum line length
                features[i, 3] = max(len(line) for line in lines) if lines else 0
                
                # Error type features
                # Features 5-9: Presence of common error indicators
                features[i, 4] = 1 if 'error' in message_lower else 0
                features[i, 5] = 1 if 'warning' in message_lower else 0
                features[i, 6] = 1 if 'exception' in message_lower else 0
                features[i, 7] = 1 if 'failed' in message_lower else 0
                features[i, 8] = 1 if 'traceback' in message_lower else 0
                
                # Feature 10: Count of error mentions
                features[i, 9] = message_lower.count('error') + message_lower.count('exception')
                
                # Stack trace features
                # Feature 11: Has stack trace
                has_stack_trace = ('traceback' in message_lower or 
                                  'stack trace' in message_lower or 
                                  ('at ' in message and '.java:' in message) or  # Java stack trace
                                  ('   at ' in message and '(' in message and ')' in message))  # .NET stack trace
                features[i, 10] = 1 if has_stack_trace else 0
                
                # Feature 12: Stack depth (number of frames)
                stack_depth = 0
                if has_stack_trace:
                    # Python-style stack traces
                    stack_depth += message.count('File "')
                    # Java-style stack traces
                    stack_depth += message.count('at ')
                    # JavaScript-style stack traces
                    stack_depth += message.count('    at ')
                features[i, 11] = stack_depth
                
                # Feature 13-14: Has line number and column number
                has_line_number = bool(re.search(r'line\s+\d+|:\d+:', message))
                has_column_number = bool(re.search(r'column\s+\d+|:\d+:\d+', message))
                features[i, 12] = 1 if has_line_number else 0
                features[i, 13] = 1 if has_column_number else 0
                
                # Error pattern features
                # Features 15-19: Specific error patterns
                for j, (pattern_name, pattern) in enumerate(list(self.ERROR_PATTERNS.items())[:5]):
                    features[i, 14 + j] = 1 if re.search(pattern, message_lower) else 0
                
                # Feature 20: Count of distinct error patterns
                pattern_count = sum(1 for pattern in self.ERROR_PATTERNS.values() 
                                   if re.search(pattern, message_lower))
                features[i, 19] = pattern_count
                
                # Library/framework features
                # Feature 21: Count of library mentions
                lib_count = sum(1 for lib in self.LIBRARIES if lib.lower() in message_lower)
                features[i, 20] = lib_count
                
                # Features 22-24: Specific library categories
                web_frameworks = ['django', 'flask', 'fastapi', 'express', 'react', 'angular', 'vue']
                data_science = ['numpy', 'pandas', 'sklearn', 'tensorflow', 'pytorch', 'torch']
                devops = ['docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'github']
                
                features[i, 21] = 1 if any(lib in message_lower for lib in web_frameworks) else 0
                features[i, 22] = 1 if any(lib in message_lower for lib in data_science) else 0
                features[i, 23] = 1 if any(lib in message_lower for lib in devops) else 0
                
                # Context features
                context = row.get('context', {})
                if isinstance(context, dict):
                    # Feature 25: Has line number in context
                    features[i, 24] = 1 if 'line_number' in context else 0
                    
                    # Feature 26: Has surrounding context
                    has_surrounding = 'surrounding_context' in context and context['surrounding_context']
                    features[i, 25] = 1 if has_surrounding else 0
                    
                    # Feature 27: Context length
                    surrounding_context = str(context.get('surrounding_context', ''))
                    features[i, 26] = len(surrounding_context)
                    
                    # Feature 28: Context line count
                    context_lines = surrounding_context.count('\n') + 1 if surrounding_context else 0
                    features[i, 27] = context_lines
                    
                    # Feature 29: Has code snippet
                    has_code = bool(re.search(r'def\s+\w+|function\s+\w+|class\s+\w+|import\s+\w+|require\s*\(', 
                                             surrounding_context))
                    features[i, 28] = 1 if has_code else 0
                    
                    # Feature 30: Has variable assignment
                    has_assignment = bool(re.search(r'\w+\s*=\s*\w+|\w+\s*:\s*\w+|var\s+\w+|let\s+\w+|const\s+\w+', 
                                                  surrounding_context))
                    features[i, 29] = 1 if has_assignment else 0
            
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
        random_state: int = 42,
        hyperparameter_tuning: bool = False,
        class_weights: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Train a model to classify errors.
        
        Args:
            errors: List of error dictionaries with message, category, etc.
            target: Classification target ('category', 'severity', or 'stage')
            model_type: Type of model to train ('random_forest', 'naive_bayes', 'logistic_regression', 
                                               'gradient_boosting', 'svm')
            test_size: Proportion of data to use for testing
            random_state: Random seed for reproducibility
            hyperparameter_tuning: Whether to perform hyperparameter tuning using GridSearchCV
            class_weights: Optional dictionary mapping class labels to weights for handling imbalanced data
            
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
        
        # Log class distribution
        class_distribution = df[target].value_counts().to_dict()
        logger.info(f"Class distribution for {target}: {class_distribution}")
        
        # Handle imbalanced classes if no explicit weights provided
        if class_weights is None and len(class_distribution) > 1:
            # Calculate class weights inversely proportional to class frequencies
            n_samples = len(df)
            n_classes = len(class_distribution)
            class_weights = {
                cls: n_samples / (n_classes * count) 
                for cls, count in class_distribution.items()
            }
            logger.info(f"Calculated class weights: {class_weights}")
        
        # Split data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(
            df, df[target], test_size=test_size, random_state=random_state, stratify=df[target] if len(df[target].unique()) > 1 else None
        )
        
        # Create feature extractor
        feature_extractor = ErrorFeatureExtractor(text_column='message')
        
        # Create model based on model_type
        if model_type == 'random_forest':
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=None,
                min_samples_split=2,
                class_weight=class_weights,
                random_state=random_state
            )
            
            # Define hyperparameter grid for tuning
            param_grid = {
                'classifier__n_estimators': [50, 100, 200],
                'classifier__max_depth': [None, 10, 20, 30],
                'classifier__min_samples_split': [2, 5, 10]
            }
            
        elif model_type == 'gradient_boosting':
            model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=3,
                random_state=random_state
            )
            
            # Define hyperparameter grid for tuning
            param_grid = {
                'classifier__n_estimators': [50, 100, 200],
                'classifier__learning_rate': [0.01, 0.1, 0.2],
                'classifier__max_depth': [3, 5, 7]
            }
            
        elif model_type == 'naive_bayes':
            model = MultinomialNB(alpha=0.1)
            
            # Define hyperparameter grid for tuning
            param_grid = {
                'classifier__alpha': [0.01, 0.1, 0.5, 1.0]
            }
            
        elif model_type == 'logistic_regression':
            model = LogisticRegression(
                C=1.0,
                max_iter=1000,
                class_weight=class_weights,
                random_state=random_state
            )
            
            # Define hyperparameter grid for tuning
            param_grid = {
                'classifier__C': [0.1, 1.0, 10.0],
                'classifier__solver': ['liblinear', 'saga'],
                'classifier__penalty': ['l1', 'l2']
            }
            
        elif model_type == 'svm':
            model = SVC(
                C=1.0,
                kernel='linear',
                probability=True,  # Required for confidence scores
                class_weight=class_weights,
                random_state=random_state
            )
            
            # Define hyperparameter grid for tuning
            param_grid = {
                'classifier__C': [0.1, 1.0, 10.0],
                'classifier__kernel': ['linear', 'rbf'],
                'classifier__gamma': ['scale', 'auto', 0.1, 0.01]
            }
            
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # Create pipeline
        pipeline = Pipeline([
            ('features', feature_extractor),
            ('classifier', model)
        ])
        
        # Perform hyperparameter tuning if requested
        if hyperparameter_tuning:
            logger.info(f"Performing hyperparameter tuning for {model_type} model")
            grid_search = GridSearchCV(
                pipeline,
                param_grid=param_grid,
                cv=5,
                scoring='f1_weighted',
                n_jobs=-1
            )
            grid_search.fit(X_train, y_train)
            
            # Use best model from grid search
            pipeline = grid_search.best_estimator_
            logger.info(f"Best parameters: {grid_search.best_params_}")
            logger.info(f"Best cross-validation score: {grid_search.best_score_:.4f}")
        else:
            # Train model without hyperparameter tuning
            pipeline.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = pipeline.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Calculate precision, recall, and F1 score
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='weighted'
        )
        
        # Generate detailed classification report
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # Generate confusion matrix
        conf_matrix = confusion_matrix(y_test, y_pred).tolist()
        
        # Cross-validation
        cv_scores = cross_val_score(pipeline, df, df[target], cv=5, scoring='f1_weighted')
        
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
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'cv_scores': [float(score) for score in cv_scores],
            'cv_mean': float(cv_scores.mean()),
            'cv_std': float(cv_scores.std()),
            'report': report,
            'confusion_matrix': conf_matrix,
            'class_distribution': class_distribution,
            'class_weights': class_weights,
            'hyperparameter_tuning': hyperparameter_tuning,
            'training_date': datetime.utcnow().isoformat(),
            'num_samples': len(df),
            'model_path': model_path
        }
        
        # Add best parameters if hyperparameter tuning was performed
        if hyperparameter_tuning and hasattr(grid_search, 'best_params_'):
            training_result['best_params'] = grid_search.best_params_
        
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
        model_type: str = 'random_forest',
        return_all_probs: bool = False,
        confidence_threshold: float = 0.0
    ) -> Union[Tuple[str, float], Dict[str, Any]]:
        """
        Predict the classification of an error message.
        
        Args:
            error_message: The error message text
            context: Additional context for the error
            target: Classification target ('category', 'severity', or 'stage')
            model_type: Type of model to use ('random_forest', 'naive_bayes', 'logistic_regression', etc.)
            return_all_probs: If True, return all class probabilities instead of just the top prediction
            confidence_threshold: Minimum confidence threshold for a valid prediction
            
        Returns:
            If return_all_probs is False:
                Tuple of (predicted_class, confidence_score)
            If return_all_probs is True:
                Dictionary with prediction details including all class probabilities
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
        
        # Get confidence scores
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(df)[0]
            confidence = max(probabilities)
            
            # Get class labels
            if hasattr(model, 'classes_'):
                classes = model.classes_
            else:
                # Try to get classes from the pipeline's classifier
                try:
                    classes = model.named_steps['classifier'].classes_
                except (AttributeError, KeyError):
                    # If we can't get the classes, use indices
                    classes = [f"class_{i}" for i in range(len(probabilities))]
            
            # Create probability dictionary
            prob_dict = {str(cls): float(prob) for cls, prob in zip(classes, probabilities)}
            
            # Sort by probability (descending)
            sorted_probs = sorted(prob_dict.items(), key=lambda x: x[1], reverse=True)
            
            # Check if confidence meets threshold
            if confidence < confidence_threshold:
                prediction = None
        else:
            # If model doesn't support probabilities, use a default confidence
            confidence = 1.0
            prob_dict = {str(prediction): 1.0}
            sorted_probs = [(str(prediction), 1.0)]
        
        if return_all_probs:
            # Return detailed prediction information
            return {
                'prediction': prediction,
                'confidence': float(confidence),
                'probabilities': prob_dict,
                'sorted_probabilities': sorted_probs,
                'meets_threshold': confidence >= confidence_threshold,
                'model_key': model_key
            }
        else:
            # Return simple prediction and confidence
            return prediction, float(confidence)
    
    def classify_error(
        self,
        error: Union[PipelineError, Dict, str],
        model_types: Optional[Dict[str, str]] = None,
        confidence_threshold: float = 0.0,
        detailed: bool = False
    ) -> Dict[str, Any]:
        """
        Classify an error using all available models.
        
        Args:
            error: The error to classify (PipelineError object, dictionary, or string)
            model_types: Dictionary mapping targets to model types to use
                         (defaults to {'category': 'random_forest', 'severity': 'random_forest', 'stage': 'random_forest'})
            confidence_threshold: Minimum confidence threshold for a valid prediction
            detailed: Whether to return detailed classification information including all probabilities
                         
        Returns:
            Dictionary with classification results for each target
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
            error_id = error.error_id
        elif isinstance(error, dict):
            error_message = error.get('message', '')
            context = error.get('context', {})
            error_id = error.get('error_id', f"err_{datetime.utcnow().timestamp()}")
        else:
            error_message = str(error)
            context = {}
            error_id = f"err_{datetime.utcnow().timestamp()}"
        
        # Make predictions for each target
        results = {
            'error_id': error_id,
            'timestamp': datetime.utcnow().isoformat(),
            'classifications': {}
        }
        
        for target, model_type in model_types.items():
            try:
                if detailed:
                    # Get detailed prediction information
                    prediction_info = self.predict(
                        error_message, 
                        context, 
                        target, 
                        model_type,
                        return_all_probs=True,
                        confidence_threshold=confidence_threshold
                    )
                    
                    results['classifications'][target] = prediction_info
                else:
                    # Get simple prediction and confidence
                    prediction, confidence = self.predict(
                        error_message, 
                        context, 
                        target, 
                        model_type,
                        confidence_threshold=confidence_threshold
                    )
                    
                    results['classifications'][target] = {
                        'prediction': prediction,
                        'confidence': confidence,
                        'meets_threshold': confidence >= confidence_threshold
                    }
                    
            except Exception as e:
                logger.error(f"Error predicting {target} with {model_type}: {str(e)}")
                results['classifications'][target] = {
                    'prediction': None,
                    'confidence': 0.0,
                    'error': str(e),
                    'meets_threshold': False
                }
        
        # Calculate overall confidence score (average of all target confidences)
        confidences = [
            cls_info.get('confidence', 0.0) 
            for cls_info in results['classifications'].values()
        ]
        results['overall_confidence'] = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Determine if all predictions meet threshold
        results['all_meet_threshold'] = all(
            cls_info.get('meets_threshold', False)
            for cls_info in results['classifications'].values()
        )
        
        return results
    
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
