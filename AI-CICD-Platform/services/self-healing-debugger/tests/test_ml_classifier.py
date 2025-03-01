import pytest
import os
import json
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from models.ml_classifier import MLErrorClassifier, ErrorFeatureExtractor
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
    },
    {
        "error_id": "err_4",
        "message": "ConnectionError: Failed to connect to database at postgres://localhost:5432",
        "category": "NETWORK",
        "severity": "CRITICAL",
        "stage": "DEPLOY",
        "context": {
            "line_number": 55,
            "surrounding_context": "conn = psycopg2.connect(db_url)\ncursor = conn.cursor()\n"
        }
    },
    {
        "error_id": "err_5",
        "message": "MemoryError: Unable to allocate 2.5 GiB for array",
        "category": "RESOURCE",
        "severity": "CRITICAL",
        "stage": "BUILD",
        "context": {
            "line_number": 78,
            "surrounding_context": "data = np.zeros((10000, 10000, 25))\nprocess_data(data)\n"
        }
    }
]

@pytest.fixture
def ml_classifier():
    """Create a test ML classifier instance."""
    # Use a temporary directory for test models
    test_model_dir = os.path.join(os.path.dirname(__file__), 'test_models')
    os.makedirs(test_model_dir, exist_ok=True)
    
    classifier = MLErrorClassifier(model_dir=test_model_dir)
    yield classifier
    
    # Cleanup
    import shutil
    if os.path.exists(test_model_dir):
        shutil.rmtree(test_model_dir)

@pytest.fixture
def sample_errors_df():
    """Create a pandas DataFrame with sample errors."""
    return pd.DataFrame(SAMPLE_ERRORS)

class TestErrorFeatureExtractor:
    """Tests for the ErrorFeatureExtractor class."""
    
    def test_init(self):
        """Test initialization of feature extractor."""
        extractor = ErrorFeatureExtractor()
        assert extractor.text_column == 'message'
        assert extractor.vectorizer is not None
    
    def test_fit(self, sample_errors_df):
        """Test fitting the feature extractor to data."""
        extractor = ErrorFeatureExtractor()
        result = extractor.fit(sample_errors_df)
        assert result is extractor  # Should return self
    
    def test_transform(self, sample_errors_df):
        """Test transforming data with the feature extractor."""
        extractor = ErrorFeatureExtractor()
        extractor.fit(sample_errors_df)
        
        features = extractor.transform(sample_errors_df)
        assert features is not None
        assert features.shape[0] == len(sample_errors_df)  # Should have one row per error
    
    def test_extract_additional_features(self, sample_errors_df):
        """Test extracting additional features from error data."""
        extractor = ErrorFeatureExtractor()
        features = extractor._extract_additional_features(sample_errors_df)
        
        assert features is not None
        assert features.shape == (len(sample_errors_df), 10)  # 10 additional features

class TestMLErrorClassifier:
    """Tests for the MLErrorClassifier class."""
    
    def test_init(self, ml_classifier):
        """Test initialization of ML classifier."""
        assert ml_classifier.model_dir is not None
        assert ml_classifier.models == {}
        assert ml_classifier.training_history == {}
    
    @pytest.mark.asyncio
    async def test_train(self, ml_classifier, sample_errors_df):
        """Test training a model."""
        # Convert DataFrame to list of dicts
        errors = sample_errors_df.to_dict('records')
        
        # Train a model
        result = ml_classifier.train(errors, target='category', model_type='random_forest')
        
        # Check result
        assert result is not None
        assert 'accuracy' in result
        assert 'cv_mean' in result
        assert 'num_samples' in result
        assert 'model_path' in result
        
        # Check that model was saved
        assert os.path.exists(result['model_path'])
        
        # Check that model is in memory
        assert 'category_random_forest' in ml_classifier.models
        
        # Check training history
        assert 'category_random_forest' in ml_classifier.training_history
    
    def test_load_model(self, ml_classifier, sample_errors_df):
        """Test loading a trained model."""
        # Train a model first
        errors = sample_errors_df.to_dict('records')
        ml_classifier.train(errors, target='category', model_type='random_forest')
        
        # Clear models from memory
        ml_classifier.models = {}
        
        # Load model
        result = ml_classifier.load_model(target='category', model_type='random_forest')
        
        # Check result
        assert result is True
        assert 'category_random_forest' in ml_classifier.models
    
    def test_predict(self, ml_classifier, sample_errors_df):
        """Test predicting with a trained model."""
        # Train a model first
        errors = sample_errors_df.to_dict('records')
        ml_classifier.train(errors, target='category', model_type='random_forest')
        
        # Make a prediction
        error_message = "ModuleNotFoundError: No module named 'pandas'"
        prediction, confidence = ml_classifier.predict(
            error_message, 
            context={},
            target='category',
            model_type='random_forest'
        )
        
        # Check prediction
        assert prediction is not None
        assert isinstance(prediction, str)
        assert confidence >= 0.0 and confidence <= 1.0
    
    def test_classify_error(self, ml_classifier, sample_errors_df):
        """Test classifying an error with all models."""
        # Train models for all targets
        errors = sample_errors_df.to_dict('records')
        for target in ['category', 'severity', 'stage']:
            ml_classifier.train(errors, target=target, model_type='random_forest')
        
        # Create a test error
        error = PipelineError(
            error_id="test_err",
            message="Failed to connect to database at postgres://localhost:5432",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.CRITICAL,
            stage=PipelineStage.DEPLOY,
            context={}
        )
        
        # Classify error
        predictions = ml_classifier.classify_error(error)
        
        # Check predictions
        assert predictions is not None
        assert 'category' in predictions
        assert 'severity' in predictions
        assert 'stage' in predictions
        
        # Check prediction format
        for target, (prediction, confidence) in predictions.items():
            assert prediction is not None or confidence == 0.0
            assert confidence >= 0.0 and confidence <= 1.0
    
    def test_get_training_history(self, ml_classifier, sample_errors_df):
        """Test getting training history."""
        # Train a model first
        errors = sample_errors_df.to_dict('records')
        ml_classifier.train(errors, target='category', model_type='random_forest')
        
        # Get training history
        history = ml_classifier.get_training_history()
        
        # Check history
        assert history is not None
        assert 'category_random_forest' in history
    
    def test_get_model_info(self, ml_classifier, sample_errors_df):
        """Test getting model information."""
        # Train a model first
        errors = sample_errors_df.to_dict('records')
        ml_classifier.train(errors, target='category', model_type='random_forest')
        
        # Get model info for trained model
        info = ml_classifier.get_model_info(target='category', model_type='random_forest')
        
        # Check info
        assert info is not None
        assert info['target'] == 'category'
        assert info['model_type'] == 'random_forest'
        assert 'accuracy' in info
        
        # Get model info for untrained model
        info = ml_classifier.get_model_info(target='category', model_type='naive_bayes')
        
        # Check info
        assert info is not None
        assert info['target'] == 'category'
        assert info['model_type'] == 'naive_bayes'
        assert info['status'] == 'not_trained'
