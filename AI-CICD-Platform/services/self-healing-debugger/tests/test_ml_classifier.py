"""
Unit tests for the ML classifier model.
"""

import os
import sys
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import joblib

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.ml_classifier import MLErrorClassifier, ErrorFeatureExtractor
from models.pipeline_debug import ErrorCategory, PipelineStage, ErrorSeverity

class TestMLErrorClassifier(unittest.TestCase):
    """Test cases for the MLErrorClassifier class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for model storage
        self.temp_dir = tempfile.TemporaryDirectory()
        self.model_dir = self.temp_dir.name
        
        # Create classifier instance
        self.classifier = MLErrorClassifier(model_dir=self.model_dir)
        
        # Sample error data for testing
        self.sample_errors = [
            {
                "message": "ImportError: No module named 'tensorflow'",
                "category": "DEPENDENCY",
                "severity": "HIGH",
                "stage": "BUILD"
            },
            {
                "message": "PermissionError: [Errno 13] Permission denied: '/var/log/app.log'",
                "category": "PERMISSION",
                "severity": "CRITICAL",
                "stage": "DEPLOY"
            },
            {
                "message": "ConfigurationError: Missing required configuration parameter 'API_KEY'",
                "category": "CONFIGURATION",
                "severity": "HIGH",
                "stage": "BUILD"
            },
            {
                "message": "ConnectionError: Failed to connect to database at 'db.example.com:5432'",
                "category": "NETWORK",
                "severity": "CRITICAL",
                "stage": "TEST"
            },
            {
                "message": "MemoryError: Out of memory when trying to allocate 1.5GB",
                "category": "RESOURCE",
                "severity": "CRITICAL",
                "stage": "BUILD"
            },
            {
                "message": "AssertionError: Expected status code 200, got 500",
                "category": "TEST",
                "severity": "MEDIUM",
                "stage": "TEST"
            },
            {
                "message": "SecurityVulnerability: CVE-2023-1234 found in package 'vulnerable-lib'",
                "category": "SECURITY",
                "severity": "HIGH",
                "stage": "SECURITY_SCAN"
            },
            {
                "message": "SyntaxError: invalid syntax at line 42",
                "category": "BUILD",
                "severity": "HIGH",
                "stage": "BUILD"
            },
            {
                "message": "TypeError: cannot concatenate 'str' and 'int' objects",
                "category": "BUILD",
                "severity": "MEDIUM",
                "stage": "BUILD"
            },
            {
                "message": "ValueError: Invalid value for parameter 'timeout': must be positive",
                "category": "CONFIGURATION",
                "severity": "MEDIUM",
                "stage": "BUILD"
            }
        ]
    
    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()
    
    def test_init(self):
        """Test initialization of MLErrorClassifier."""
        self.assertEqual(self.classifier.model_dir, self.model_dir)
        self.assertIsInstance(self.classifier.models, dict)
        self.assertIsInstance(self.classifier.training_history, dict)
        
        # Check if model directory was created
        self.assertTrue(os.path.exists(self.model_dir))
    
    def test_train_random_forest(self):
        """Test training a random forest model."""
        # Train model
        result = self.classifier.train(
            self.sample_errors,
            target='category',
            model_type='random_forest'
        )
        
        # Check result
        self.assertIn('accuracy', result)
        self.assertIn('precision', result)
        self.assertIn('recall', result)
        self.assertIn('f1_score', result)
        self.assertIn('cv_scores', result)
        self.assertIn('cv_mean', result)
        self.assertIn('cv_std', result)
        self.assertIn('report', result)
        self.assertIn('confusion_matrix', result)
        self.assertIn('class_distribution', result)
        self.assertIn('training_date', result)
        
        # Check if model was saved
        model_key = 'category_random_forest'
        self.assertIn(model_key, self.classifier.models)
        self.assertIn(model_key, self.classifier.training_history)
        
        # Check if model file was created
        model_path = os.path.join(self.model_dir, f"{model_key}.joblib")
        self.assertTrue(os.path.exists(model_path))
        
        # Check if training history was saved
        history_path = os.path.join(self.model_dir, 'training_history.json')
        self.assertTrue(os.path.exists(history_path))
        
        # Load training history
        with open(history_path, 'r') as f:
            history = json.load(f)
        
        # Check if history contains the model
        self.assertIn(model_key, history)
    
    def test_train_with_hyperparameter_tuning(self):
        """Test training with hyperparameter tuning."""
        # Train model with hyperparameter tuning
        result = self.classifier.train(
            self.sample_errors,
            target='category',
            model_type='random_forest',
            hyperparameter_tuning=True
        )
        
        # Check if best parameters are included
        self.assertIn('best_params', result)
    
    def test_train_with_class_weights(self):
        """Test training with class weights."""
        # Define class weights
        class_weights = {
            'DEPENDENCY': 2.0,
            'PERMISSION': 1.5,
            'CONFIGURATION': 1.0,
            'NETWORK': 1.0,
            'RESOURCE': 1.0,
            'TEST': 1.0,
            'SECURITY': 2.0,
            'BUILD': 0.5
        }
        
        # Train model with class weights
        result = self.classifier.train(
            self.sample_errors,
            target='category',
            model_type='random_forest',
            class_weights=class_weights
        )
        
        # Check if class weights are included
        self.assertEqual(result['class_weights'], class_weights)
    
    def test_train_multiple_models(self):
        """Test training multiple models for different targets."""
        targets = ['category', 'severity', 'stage']
        model_types = ['random_forest', 'naive_bayes']
        
        for target in targets:
            for model_type in model_types:
                # Train model
                result = self.classifier.train(
                    self.sample_errors,
                    target=target,
                    model_type=model_type
                )
                
                # Check if model was saved
                model_key = f"{target}_{model_type}"
                self.assertIn(model_key, self.classifier.models)
                self.assertIn(model_key, self.classifier.training_history)
                
                # Check if model file was created
                model_path = os.path.join(self.model_dir, f"{model_key}.joblib")
                self.assertTrue(os.path.exists(model_path))
    
    def test_load_model(self):
        """Test loading a trained model."""
        # Train and save a model
        self.classifier.train(
            self.sample_errors,
            target='category',
            model_type='random_forest'
        )
        
        # Create a new classifier instance
        new_classifier = MLErrorClassifier(model_dir=self.model_dir)
        
        # Load the model
        result = new_classifier.load_model('category', 'random_forest')
        
        # Check if model was loaded
        self.assertTrue(result)
        self.assertIn('category_random_forest', new_classifier.models)
        
        # Check if training history was loaded
        self.assertIn('category_random_forest', new_classifier.training_history)
    
    def test_predict_with_confidence(self):
        """Test predicting with confidence scores."""
        # Train a model
        self.classifier.train(
            self.sample_errors,
            target='category',
            model_type='random_forest'
        )
        
        # Test error message
        error_message = "ImportError: No module named 'pandas'"
        
        # Predict without detailed results
        prediction, confidence = self.classifier.predict(
            error_message,
            target='category',
            model_type='random_forest'
        )
        
        # Check prediction
        self.assertIsInstance(prediction, str)
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        
        # Predict with detailed results
        detailed_result = self.classifier.predict(
            error_message,
            target='category',
            model_type='random_forest',
            return_all_probs=True
        )
        
        # Check detailed result
        self.assertIsInstance(detailed_result, dict)
        self.assertIn('prediction', detailed_result)
        self.assertIn('confidence', detailed_result)
        self.assertIn('probabilities', detailed_result)
        self.assertIn('sorted_probabilities', detailed_result)
        self.assertIn('meets_threshold', detailed_result)
        self.assertIn('model_key', detailed_result)
    
    def test_predict_with_confidence_threshold(self):
        """Test predicting with confidence threshold."""
        # Train a model
        self.classifier.train(
            self.sample_errors,
            target='category',
            model_type='random_forest'
        )
        
        # Test error message
        error_message = "Some unknown error that doesn't match any category"
        
        # Predict with high confidence threshold
        detailed_result = self.classifier.predict(
            error_message,
            target='category',
            model_type='random_forest',
            return_all_probs=True,
            confidence_threshold=0.9
        )
        
        # If confidence is below threshold, prediction should be None
        if detailed_result['confidence'] < 0.9:
            self.assertFalse(detailed_result['meets_threshold'])
            if not detailed_result['meets_threshold']:
                self.assertIsNone(detailed_result['prediction'])
    
    def test_classify_error(self):
        """Test classifying an error with multiple models."""
        # Train models for different targets
        targets = ['category', 'severity', 'stage']
        for target in targets:
            self.classifier.train(
                self.sample_errors,
                target=target,
                model_type='random_forest'
            )
        
        # Test error message
        error_message = "PermissionError: [Errno 13] Permission denied: '/var/log/app.log'"
        
        # Classify error
        result = self.classifier.classify_error(
            error_message,
            model_types={
                'category': 'random_forest',
                'severity': 'random_forest',
                'stage': 'random_forest'
            },
            confidence_threshold=0.5,
            detailed=False
        )
        
        # Check result
        self.assertIsInstance(result, dict)
        self.assertIn('error_id', result)
        self.assertIn('timestamp', result)
        self.assertIn('classifications', result)
        self.assertIn('overall_confidence', result)
        self.assertIn('all_meet_threshold', result)
        
        # Check classifications
        classifications = result['classifications']
        self.assertIn('category', classifications)
        self.assertIn('severity', classifications)
        self.assertIn('stage', classifications)
        
        # Check category classification
        category_result = classifications['category']
        self.assertIn('prediction', category_result)
        self.assertIn('confidence', category_result)
        self.assertIn('meets_threshold', category_result)
    
    def test_classify_error_detailed(self):
        """Test classifying an error with detailed results."""
        # Train models for different targets
        targets = ['category', 'severity', 'stage']
        for target in targets:
            self.classifier.train(
                self.sample_errors,
                target=target,
                model_type='random_forest'
            )
        
        # Test error message
        error_message = "PermissionError: [Errno 13] Permission denied: '/var/log/app.log'"
        
        # Classify error with detailed results
        result = self.classifier.classify_error(
            error_message,
            model_types={
                'category': 'random_forest',
                'severity': 'random_forest',
                'stage': 'random_forest'
            },
            confidence_threshold=0.5,
            detailed=True
        )
        
        # Check detailed classifications
        classifications = result['classifications']
        for target in targets:
            target_result = classifications[target]
            self.assertIn('probabilities', target_result)
            self.assertIn('sorted_probabilities', target_result)
            self.assertIsInstance(target_result['sorted_probabilities'], list)
            self.assertGreater(len(target_result['sorted_probabilities']), 0)
    
    def test_get_model_info(self):
        """Test getting model information."""
        # Train a model
        self.classifier.train(
            self.sample_errors,
            target='category',
            model_type='random_forest'
        )
        
        # Get model info
        model_info = self.classifier.get_model_info('category', 'random_forest')
        
        # Check model info
        self.assertIsInstance(model_info, dict)
        self.assertEqual(model_info['target'], 'category')
        self.assertEqual(model_info['model_type'], 'random_forest')
        self.assertIn('accuracy', model_info)
        self.assertIn('precision', model_info)
        self.assertIn('recall', model_info)
        self.assertIn('f1_score', model_info)
        self.assertIn('cv_mean', model_info)
        self.assertIn('training_date', model_info)
    
    def test_get_model_info_nonexistent(self):
        """Test getting info for a nonexistent model."""
        # Get info for nonexistent model
        model_info = self.classifier.get_model_info('nonexistent', 'nonexistent')
        
        # Check model info
        self.assertIsInstance(model_info, dict)
        self.assertEqual(model_info['target'], 'nonexistent')
        self.assertEqual(model_info['model_type'], 'nonexistent')
        self.assertEqual(model_info['status'], 'not_trained')
    
    def test_get_training_history(self):
        """Test getting training history."""
        # Train multiple models
        targets = ['category', 'severity']
        model_types = ['random_forest', 'naive_bayes']
        
        for target in targets:
            for model_type in model_types:
                self.classifier.train(
                    self.sample_errors,
                    target=target,
                    model_type=model_type
                )
        
        # Get training history
        history = self.classifier.get_training_history()
        
        # Check history
        self.assertIsInstance(history, dict)
        self.assertEqual(len(history), len(targets) * len(model_types))
        
        # Check if all models are in history
        for target in targets:
            for model_type in model_types:
                model_key = f"{target}_{model_type}"
                self.assertIn(model_key, history)


class TestErrorFeatureExtractor(unittest.TestCase):
    """Test cases for the ErrorFeatureExtractor class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create feature extractor
        self.extractor = ErrorFeatureExtractor(text_column='message')
        
        # Sample error data for testing
        self.sample_errors = pd.DataFrame([
            {
                "message": "ImportError: No module named 'tensorflow'",
                "category": "DEPENDENCY",
                "context": {
                    "line_number": 42,
                    "surrounding_context": "import tensorflow as tf\nimport numpy as np"
                }
            },
            {
                "message": "PermissionError: [Errno 13] Permission denied: '/var/log/app.log'",
                "category": "PERMISSION",
                "context": {
                    "line_number": 123,
                    "surrounding_context": "with open('/var/log/app.log', 'w') as f:\n    f.write('test')"
                }
            },
            {
                "message": """Traceback (most recent call last):
  File "app.py", line 42, in <module>
    main()
  File "app.py", line 36, in main
    result = process_data(data)
  File "app.py", line 25, in process_data
    return data['key']
KeyError: 'key'""",
                "category": "BUILD",
                "context": {
                    "line_number": 42,
                    "surrounding_context": "def process_data(data):\n    return data['key']\n\ndata = {}"
                }
            }
        ])
    
    def test_fit(self):
        """Test fitting the feature extractor."""
        # Fit extractor
        self.extractor.fit(self.sample_errors)
        
        # Check if vectorizer was fitted
        self.assertTrue(hasattr(self.extractor.vectorizer, 'vocabulary_'))
    
    def test_transform(self):
        """Test transforming data with the feature extractor."""
        # Fit extractor
        self.extractor.fit(self.sample_errors)
        
        # Transform data
        features = self.extractor.transform(self.sample_errors)
        
        # Check features
        self.assertIsInstance(features, np.ndarray)
        self.assertEqual(features.shape[0], len(self.sample_errors))
        
        # Check if additional features were extracted
        # Text features + additional features
        self.assertGreater(features.shape[1], self.extractor.max_features)
    
    def test_extract_additional_features(self):
        """Test extracting additional features."""
        # Extract additional features
        features = self.extractor._extract_additional_features(self.sample_errors)
        
        # Check features
        self.assertIsInstance(features, np.ndarray)
        self.assertEqual(features.shape[0], len(self.sample_errors))
        self.assertEqual(features.shape[1], 30)  # 30 additional features
        
        # Check specific features
        # Message length (feature 0)
        self.assertGreater(features[0, 0], 0)
        
        # Number of lines (feature 1)
        self.assertEqual(features[0, 1], 1)  # First message is one line
        self.assertGreater(features[2, 1], 1)  # Third message is multi-line
        
        # Has error indicator (feature 4)
        self.assertEqual(features[0, 4], 1)  # "error" in first message
        
        # Has stack trace (feature 10)
        self.assertEqual(features[0, 10], 0)  # No stack trace in first message
        self.assertEqual(features[2, 10], 1)  # Stack trace in third message
        
        # Has line number in context (feature 24)
        self.assertEqual(features[0, 24], 1)  # All samples have line_number in context


if __name__ == '__main__':
    unittest.main()
