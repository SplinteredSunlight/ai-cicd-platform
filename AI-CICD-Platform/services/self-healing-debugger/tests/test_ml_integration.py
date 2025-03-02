"""
Integration tests for the ML classifier service.
"""

import os
import sys
import unittest
import tempfile
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import pandas as pd
import numpy as np

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.ml_classifier import MLErrorClassifier
from services.ml_classifier_service import MLClassifierService
from models.pipeline_debug import PipelineError, ErrorCategory, PipelineStage, ErrorSeverity

class TestMLClassifierServiceIntegration(unittest.TestCase):
    """Integration tests for the MLClassifierService class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for model storage
        self.temp_dir = tempfile.TemporaryDirectory()
        self.model_dir = os.path.join(self.temp_dir.name, 'models/trained')
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Mock Elasticsearch client
        self.es_mock = AsyncMock()
        self.es_mock.search = AsyncMock()
        self.es_mock.close = AsyncMock()
        
        # Mock WebSocket service
        self.ws_mock = AsyncMock()
        self.ws_mock.emit_ml_classification = AsyncMock()
        self.ws_mock.emit_event = AsyncMock()
        
        # Create classifier service with mocks
        with patch('services.ml_classifier_service.AsyncElasticsearch', return_value=self.es_mock):
            with patch('services.ml_classifier_service.get_settings') as mock_settings:
                # Configure mock settings
                mock_settings.return_value = MagicMock(
                    elasticsearch_hosts=['http://localhost:9200'],
                    elasticsearch_index_prefix='debugger-',
                    elasticsearch_username=None,
                    elasticsearch_password=None,
                    ml_confidence_threshold=0.6
                )
                
                # Create service with mocked dependencies
                self.service = MLClassifierService(websocket_service=self.ws_mock)
                
                # Replace classifier with one using our temp directory
                self.service.classifier = MLErrorClassifier(model_dir=self.model_dir)
        
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
            }
        ]
        
        # Configure Elasticsearch mock to return sample errors
        self.es_mock.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": error} for error in self.sample_errors
                ]
            }
        }
    
    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()
    
    def asyncSetUp(self):
        """Async setup - train models for testing."""
        # Train models for testing
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._train_test_models())
    
    async def _train_test_models(self):
        """Train models for testing."""
        # Configure Elasticsearch mock to return sample errors
        self.es_mock.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": error} for error in self.sample_errors
                ]
            }
        }
        
        # Train models
        await self.service.train_models(
            model_types=['random_forest'],
            emit_updates=False
        )
    
    def test_init(self):
        """Test initialization of MLClassifierService."""
        self.assertIsInstance(self.service.classifier, MLErrorClassifier)
        self.assertEqual(self.service.websocket_service, self.ws_mock)
        self.assertEqual(self.service.confidence_threshold, 0.6)
    
    def test_train_models(self):
        """Test training models."""
        # Run async test
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.service.train_models(
            model_types=['random_forest'],
            emit_updates=False
        ))
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertIn("models_trained", result)
        self.assertIn("results", result)
        
        # Check if Elasticsearch was called
        self.es_mock.search.assert_called_once()
        
        # Check if models were trained
        self.assertIn("category_random_forest", result["results"])
        self.assertIn("severity_random_forest", result["results"])
        self.assertIn("stage_random_forest", result["results"])
    
    def test_train_models_with_hyperparameter_tuning(self):
        """Test training models with hyperparameter tuning."""
        # Run async test
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.service.train_models(
            model_types=['random_forest'],
            hyperparameter_tuning=True,
            emit_updates=False
        ))
        
        # Check result
        self.assertEqual(result["status"], "success")
        
        # Check if hyperparameter tuning was performed
        for model_key, model_result in result["results"].items():
            if model_result["status"] == "success":
                self.assertTrue(model_result["hyperparameter_tuning"])
    
    def test_train_models_with_websocket_updates(self):
        """Test training models with WebSocket updates."""
        # Run async test
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.service.train_models(
            model_types=['random_forest'],
            emit_updates=True
        ))
        
        # Check result
        self.assertEqual(result["status"], "success")
        
        # Check if WebSocket events were emitted
        self.ws_mock.emit_event.assert_called()
        
        # Check number of WebSocket calls
        # At least 1 for training started + 1 for each model + 1 for training completed
        expected_min_calls = 1 + 3 + 1  # 3 models (category, severity, stage)
        self.assertGreaterEqual(self.ws_mock.emit_event.call_count, expected_min_calls)
    
    def test_classify_error(self):
        """Test classifying an error."""
        # First train models
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._train_test_models())
        
        # Test error message
        error = {
            "message": "ImportError: No module named 'pandas'",
            "error_id": "test_error_1"
        }
        
        # Run async test
        result = loop.run_until_complete(self.service.classify_error(
            error,
            emit_update=False
        ))
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertIn("classifications", result)
        self.assertIn("category", result["classifications"])
        self.assertIn("severity", result["classifications"])
        self.assertIn("stage", result["classifications"])
        
        # Check category classification
        category_result = result["classifications"]["category"]
        self.assertIn("prediction", category_result)
        self.assertIn("confidence", category_result)
        self.assertIn("meets_threshold", category_result)
    
    def test_classify_error_with_websocket_update(self):
        """Test classifying an error with WebSocket update."""
        # First train models
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._train_test_models())
        
        # Test error message
        error = {
            "message": "ImportError: No module named 'pandas'",
            "error_id": "test_error_2"
        }
        
        # Run async test
        result = loop.run_until_complete(self.service.classify_error(
            error,
            emit_update=True
        ))
        
        # Check result
        self.assertEqual(result["status"], "success")
        
        # Check if WebSocket event was emitted
        self.ws_mock.emit_ml_classification.assert_called_once_with(
            "test_error_2", result
        )
    
    def test_classify_error_detailed(self):
        """Test classifying an error with detailed results."""
        # First train models
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._train_test_models())
        
        # Test error message
        error = {
            "message": "ImportError: No module named 'pandas'",
            "error_id": "test_error_3"
        }
        
        # Run async test
        result = loop.run_until_complete(self.service.classify_error(
            error,
            detailed=True,
            emit_update=False
        ))
        
        # Check result
        self.assertEqual(result["status"], "success")
        
        # Check detailed classifications
        for target in ["category", "severity", "stage"]:
            target_result = result["classifications"][target]
            self.assertIn("probabilities", target_result)
            self.assertIn("sorted_probabilities", target_result)
    
    def test_classify_error_with_confidence_threshold(self):
        """Test classifying an error with confidence threshold."""
        # First train models
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._train_test_models())
        
        # Test error message - something unlikely to match well
        error = {
            "message": "Some completely unknown error type that doesn't match any category",
            "error_id": "test_error_4"
        }
        
        # Run async test with high threshold
        result = loop.run_until_complete(self.service.classify_error(
            error,
            confidence_threshold=0.9,
            emit_update=False
        ))
        
        # Check result
        self.assertEqual(result["status"], "success")
        
        # Check if any predictions meet the threshold
        meets_threshold = [
            cls_info.get("meets_threshold", False)
            for cls_info in result["classifications"].values()
        ]
        
        # Check overall threshold status
        self.assertEqual(result["all_meet_threshold"], all(meets_threshold))
    
    def test_get_model_info(self):
        """Test getting model information."""
        # First train models
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._train_test_models())
        
        # Run async test
        result = loop.run_until_complete(self.service.get_model_info())
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertIn("models", result)
        
        # Check if all models are included
        models = result["models"]
        self.assertIn("category_random_forest", models)
        self.assertIn("severity_random_forest", models)
        self.assertIn("stage_random_forest", models)
        
        # Check model info
        for model_key, model_info in models.items():
            self.assertIn("target", model_info)
            self.assertIn("model_type", model_info)
            self.assertIn("accuracy", model_info)
            self.assertIn("precision", model_info)
            self.assertIn("recall", model_info)
            self.assertIn("f1_score", model_info)
            self.assertIn("cv_mean", model_info)
            self.assertIn("training_date", model_info)
    
    def test_generate_training_data(self):
        """Test generating training data."""
        # Create temporary output file
        output_file = os.path.join(self.temp_dir.name, 'training_data.json')
        
        # Run async test
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.service.generate_training_data(
            output_file=output_file
        ))
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["num_errors"], len(self.sample_errors))
        self.assertEqual(result["output_file"], output_file)
        
        # Check if Elasticsearch was called
        self.es_mock.search.assert_called()
        
        # Check if file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Check file contents
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(len(data), len(self.sample_errors))
    
    def test_evaluate_model(self):
        """Test evaluating a model."""
        # First train models
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._train_test_models())
        
        # Run async test
        result = loop.run_until_complete(self.service.evaluate_model(
            target='category',
            model_type='random_forest',
            test_data=self.sample_errors
        ))
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["model_key"], "category_random_forest")
        self.assertIn("accuracy", result)
        self.assertIn("precision", result)
        self.assertIn("recall", result)
        self.assertIn("f1_score", result)
        self.assertIn("report", result)
        self.assertIn("num_test_samples", result)
    
    def test_set_confidence_threshold(self):
        """Test setting confidence threshold."""
        # Run async test
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.service.set_confidence_threshold(0.8))
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["confidence_threshold"], 0.8)
        
        # Check if threshold was updated
        self.assertEqual(self.service.confidence_threshold, 0.8)
    
    def test_set_confidence_threshold_invalid(self):
        """Test setting invalid confidence threshold."""
        # Run async test with invalid threshold
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.service.set_confidence_threshold(1.5))
        
        # Check result
        self.assertEqual(result["status"], "error")
        
        # Check if threshold was not updated
        self.assertEqual(self.service.confidence_threshold, 0.6)


class TestEndToEndWorkflow(unittest.TestCase):
    """End-to-end tests for the ML classification workflow."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for model storage
        self.temp_dir = tempfile.TemporaryDirectory()
        self.model_dir = os.path.join(self.temp_dir.name, 'models/trained')
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Mock Elasticsearch client
        self.es_mock = AsyncMock()
        self.es_mock.search = AsyncMock()
        self.es_mock.index = AsyncMock()
        self.es_mock.close = AsyncMock()
        
        # Mock WebSocket service
        self.ws_mock = AsyncMock()
        self.ws_mock.emit_ml_classification = AsyncMock()
        self.ws_mock.emit_event = AsyncMock()
        
        # Create classifier service with mocks
        with patch('services.ml_classifier_service.AsyncElasticsearch', return_value=self.es_mock):
            with patch('services.ml_classifier_service.get_settings') as mock_settings:
                # Configure mock settings
                mock_settings.return_value = MagicMock(
                    elasticsearch_hosts=['http://localhost:9200'],
                    elasticsearch_index_prefix='debugger-',
                    elasticsearch_username=None,
                    elasticsearch_password=None,
                    ml_confidence_threshold=0.6,
                    use_ml_classification=True
                )
                
                # Create service with mocked dependencies
                self.ml_service = MLClassifierService(websocket_service=self.ws_mock)
                
                # Replace classifier with one using our temp directory
                self.ml_service.classifier = MLErrorClassifier(model_dir=self.model_dir)
        
        # Sample error data for training
        self.training_errors = [
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
        
        # Configure Elasticsearch mock to return training errors
        self.es_mock.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": error} for error in self.training_errors
                ]
            }
        }
        
        # Sample test errors for classification
        self.test_errors = [
            {
                "message": "ImportError: No module named 'pandas'",
                "error_id": "test_error_1"
            },
            {
                "message": "PermissionError: [Errno 13] Permission denied: '/var/log/app2.log'",
                "error_id": "test_error_2"
            },
            {
                "message": "ConfigurationError: Missing required configuration parameter 'SECRET_KEY'",
                "error_id": "test_error_3"
            }
        ]
    
    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()
    
    def test_end_to_end_workflow(self):
        """Test end-to-end ML classification workflow."""
        # Create event loop
        loop = asyncio.get_event_loop()
        
        # Step 1: Train models
        train_result = loop.run_until_complete(self.ml_service.train_models(
            model_types=['random_forest', 'gradient_boosting'],
            hyperparameter_tuning=True,
            emit_updates=True
        ))
        
        # Check training result
        self.assertEqual(train_result["status"], "success")
        self.assertGreaterEqual(train_result["models_trained"], 3)  # At least 3 models (category, severity, stage)
        
        # Check WebSocket events for training
        self.ws_mock.emit_event.assert_called()
        
        # Reset WebSocket mock for next steps
        self.ws_mock.reset_mock()
        
        # Step 2: Classify errors
        classification_results = []
        for error in self.test_errors:
            result = loop.run_until_complete(self.ml_service.classify_error(
                error,
                detailed=True,
                emit_update=True
            ))
            classification_results.append(result)
        
        # Check classification results
        for result in classification_results:
            self.assertEqual(result["status"], "success")
            self.assertIn("classifications", result)
            self.assertIn("overall_confidence", result)
            
            # Check if all targets were classified
            self.assertIn("category", result["classifications"])
            self.assertIn("severity", result["classifications"])
            self.assertIn("stage", result["classifications"])
            
            # Check detailed results
            for target, target_result in result["classifications"].items():
                self.assertIn("probabilities", target_result)
                self.assertIn("sorted_probabilities", target_result)
        
        # Check WebSocket events for classification
        self.assertEqual(self.ws_mock.emit_ml_classification.call_count, len(self.test_errors))
        
        # Step 3: Evaluate models
        eval_result = loop.run_until_complete(self.ml_service.evaluate_model(
            target='category',
            model_type='random_forest'
        ))
        
        # Check evaluation result
        self.assertEqual(eval_result["status"], "success")
        self.assertIn("accuracy", eval_result)
        self.assertIn("precision", eval_result)
        self.assertIn("recall", eval_result)
        self.assertIn("f1_score", eval_result)
        
        # Step 4: Get model info
        info_result = loop.run_until_complete(self.ml_service.get_model_info())
        
        # Check model info result
        self.assertEqual(info_result["status"], "success")
        self.assertIn("models", info_result)
        
        # Check if all trained models are included
        models = info_result["models"]
        self.assertIn("category_random_forest", models)
        self.assertIn("category_gradient_boosting", models)
        self.assertIn("severity_random_forest", models)
        self.assertIn("severity_gradient_boosting", models)
        self.assertIn("stage_random_forest", models)
        self.assertIn("stage_gradient_boosting", models)


if __name__ == '__main__':
    unittest.main()
