import pytest
import os
import json
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, AsyncMock

from services.ml_classifier_service import MLClassifierService
from models.pipeline_debug import ErrorCategory, PipelineStage, ErrorSeverity, PipelineError

# Sample test data
SAMPLE_ERRORS = [
    {
        "error_id": "err_1",
        "message": "ModuleNotFoundError: No module named 'requests'",
        "category": "DEPENDENCY",
        "severity": "HIGH",
        "stage": "BUILD",
        "context": {
            "line_number": 10,
            "surrounding_context": "import requests\nimport json\n"
        }
    },
    {
        "error_id": "err_2",
        "message": "PermissionError: [Errno 13] Permission denied: '/var/log/app.log'",
        "category": "PERMISSION",
        "severity": "MEDIUM",
        "stage": "DEPLOY",
        "context": {
            "line_number": 25,
            "surrounding_context": "with open('/var/log/app.log', 'w') as f:\n    f.write(log_message)\n"
        }
    },
    {
        "error_id": "err_3",
        "message": "ConfigurationError: Missing required configuration: DATABASE_URL",
        "category": "CONFIGURATION",
        "severity": "HIGH",
        "stage": "DEPLOY",
        "context": {
            "line_number": 42,
            "surrounding_context": "db_url = os.environ['DATABASE_URL']\ndb = connect_to_db(db_url)\n"
        }
    }
]

@pytest.fixture
def mock_elasticsearch():
    """Create a mock Elasticsearch client."""
    mock_es = AsyncMock()
    mock_es.search = AsyncMock(return_value={
        "hits": {
            "hits": [
                {"_source": error} for error in SAMPLE_ERRORS
            ]
        }
    })
    mock_es.index = AsyncMock()
    mock_es.close = AsyncMock()
    return mock_es

@pytest.fixture
def mock_ml_classifier():
    """Create a mock ML classifier."""
    mock_classifier = MagicMock()
    mock_classifier.train = MagicMock(return_value={
        "accuracy": 0.85,
        "cv_mean": 0.82,
        "cv_std": 0.03,
        "num_samples": len(SAMPLE_ERRORS),
        "model_path": "/path/to/model.joblib"
    })
    mock_classifier.classify_error = MagicMock(return_value={
        "category": ("DEPENDENCY", 0.95),
        "severity": ("HIGH", 0.85),
        "stage": ("BUILD", 0.75)
    })
    mock_classifier.get_training_history = MagicMock(return_value={
        "category_random_forest": {
            "target": "category",
            "model_type": "random_forest",
            "accuracy": 0.85,
            "cv_mean": 0.82,
            "num_samples": len(SAMPLE_ERRORS),
            "training_date": "2025-02-25T12:00:00"
        }
    })
    return mock_classifier

@pytest.fixture
def ml_classifier_service(mock_elasticsearch, mock_ml_classifier):
    """Create a test ML classifier service with mocked dependencies."""
    with patch('services.ml_classifier_service.AsyncElasticsearch', return_value=mock_elasticsearch):
        with patch('services.ml_classifier_service.MLErrorClassifier', return_value=mock_ml_classifier):
            service = MLClassifierService()
            service.es_client = mock_elasticsearch
            service.classifier = mock_ml_classifier
            yield service

class TestMLClassifierService:
    """Tests for the MLClassifierService class."""
    
    def test_init(self, ml_classifier_service, mock_elasticsearch, mock_ml_classifier):
        """Test initialization of ML classifier service."""
        assert ml_classifier_service.es_client is mock_elasticsearch
        assert ml_classifier_service.classifier is mock_ml_classifier
    
    @pytest.mark.asyncio
    async def test_train_models(self, ml_classifier_service, mock_elasticsearch, mock_ml_classifier):
        """Test training ML models."""
        # Set up mock
        mock_elasticsearch.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": error} for error in SAMPLE_ERRORS
                ]
            }
        }
        
        # Call method
        result = await ml_classifier_service.train_models(
            pipeline_id="test_pipeline",
            limit=10,
            model_types=["random_forest"]
        )
        
        # Check result
        assert result["status"] == "success"
        assert result["models_trained"] > 0
        
        # Check that Elasticsearch was called
        mock_elasticsearch.search.assert_called_once()
        
        # Check that classifier.train was called
        assert mock_ml_classifier.train.call_count > 0
    
    @pytest.mark.asyncio
    async def test_get_historical_errors(self, ml_classifier_service, mock_elasticsearch):
        """Test retrieving historical errors."""
        # Set up mock
        mock_elasticsearch.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": error} for error in SAMPLE_ERRORS
                ]
            }
        }
        
        # Call method
        errors = await ml_classifier_service._get_historical_errors(
            pipeline_id="test_pipeline",
            limit=10
        )
        
        # Check result
        assert len(errors) == len(SAMPLE_ERRORS)
        assert errors[0]["error_id"] == SAMPLE_ERRORS[0]["error_id"]
        
        # Check that Elasticsearch was called
        mock_elasticsearch.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_classify_error(self, ml_classifier_service, mock_ml_classifier):
        """Test classifying an error."""
        # Create test error
        error = PipelineError(
            error_id="test_err",
            message="ModuleNotFoundError: No module named 'pandas'",
            category=ErrorCategory.DEPENDENCY,
            severity=ErrorSeverity.HIGH,
            stage=PipelineStage.BUILD,
            context={}
        )
        
        # Set up mock
        mock_ml_classifier.classify_error.return_value = {
            "category": ("DEPENDENCY", 0.95),
            "severity": ("HIGH", 0.85),
            "stage": ("BUILD", 0.75)
        }
        
        # Call method
        result = await ml_classifier_service.classify_error(error)
        
        # Check result
        assert result["status"] == "success"
        assert "classifications" in result
        assert "category" in result["classifications"]
        assert "severity" in result["classifications"]
        assert "stage" in result["classifications"]
        
        # Check that classifier.classify_error was called
        mock_ml_classifier.classify_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_model_info(self, ml_classifier_service, mock_ml_classifier):
        """Test getting model information."""
        # Set up mock
        mock_ml_classifier.get_training_history.return_value = {
            "category_random_forest": {
                "target": "category",
                "model_type": "random_forest",
                "accuracy": 0.85,
                "cv_mean": 0.82,
                "num_samples": len(SAMPLE_ERRORS),
                "training_date": "2025-02-25T12:00:00"
            }
        }
        
        # Call method
        result = await ml_classifier_service.get_model_info()
        
        # Check result
        assert result["status"] == "success"
        assert "models" in result
        assert "category_random_forest" in result["models"]
        
        # Check that classifier.get_training_history was called
        mock_ml_classifier.get_training_history.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_training_data(self, ml_classifier_service, mock_elasticsearch, tmp_path):
        """Test generating training data."""
        # Set up mock
        mock_elasticsearch.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": error} for error in SAMPLE_ERRORS
                ]
            }
        }
        
        # Create temporary output file
        output_file = os.path.join(tmp_path, "training_data.json")
        
        # Call method
        result = await ml_classifier_service.generate_training_data(
            output_file=output_file,
            limit=10
        )
        
        # Check result
        assert result["status"] == "success"
        assert result["num_errors"] == len(SAMPLE_ERRORS)
        assert result["output_file"] == output_file
        
        # Check that Elasticsearch was called
        mock_elasticsearch.search.assert_called_once()
        
        # Check that file was created
        assert os.path.exists(output_file)
        
        # Check file contents
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert len(data) == len(SAMPLE_ERRORS)
            assert data[0]["error_id"] == SAMPLE_ERRORS[0]["error_id"]
    
    @pytest.mark.asyncio
    async def test_cleanup(self, ml_classifier_service, mock_elasticsearch):
        """Test cleanup method."""
        # Call method
        await ml_classifier_service.cleanup()
        
        # Check that Elasticsearch.close was called
        mock_elasticsearch.close.assert_called_once()
