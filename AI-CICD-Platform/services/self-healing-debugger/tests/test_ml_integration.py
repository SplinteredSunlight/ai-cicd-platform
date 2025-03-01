import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from main import app, debug_service
from models.pipeline_debug import PipelineError, ErrorCategory, ErrorSeverity, PipelineStage

# Sample test data
SAMPLE_ERROR = PipelineError(
    error_id="test_err_1",
    message="ModuleNotFoundError: No module named 'requests'",
    category=ErrorCategory.DEPENDENCY,
    severity=ErrorSeverity.HIGH,
    stage=PipelineStage.BUILD,
    context={
        "line_number": 10,
        "surrounding_context": "import requests\nimport json\n"
    }
)

SAMPLE_CLASSIFICATION_RESULT = {
    "status": "success",
    "classifications": {
        "category": {
            "prediction": "DEPENDENCY",
            "confidence": 0.95
        },
        "severity": {
            "prediction": "HIGH",
            "confidence": 0.85
        },
        "stage": {
            "prediction": "BUILD",
            "confidence": 0.75
        }
    }
}

SAMPLE_TRAINING_RESULT = {
    "status": "success",
    "models_trained": 3,
    "results": {
        "category_random_forest": {
            "status": "success",
            "accuracy": 0.85,
            "cv_mean": 0.82,
            "num_samples": 100
        },
        "severity_random_forest": {
            "status": "success",
            "accuracy": 0.80,
            "cv_mean": 0.78,
            "num_samples": 100
        },
        "stage_random_forest": {
            "status": "success",
            "accuracy": 0.75,
            "cv_mean": 0.72,
            "num_samples": 100
        }
    }
}

SAMPLE_MODEL_INFO = {
    "status": "success",
    "models": {
        "category_random_forest": {
            "target": "category",
            "model_type": "random_forest",
            "accuracy": 0.85,
            "cv_mean": 0.82,
            "num_samples": 100,
            "training_date": "2025-02-25T12:00:00"
        },
        "severity_random_forest": {
            "target": "severity",
            "model_type": "random_forest",
            "accuracy": 0.80,
            "cv_mean": 0.78,
            "num_samples": 100,
            "training_date": "2025-02-25T12:00:00"
        },
        "stage_random_forest": {
            "target": "stage",
            "model_type": "random_forest",
            "accuracy": 0.75,
            "cv_mean": 0.72,
            "num_samples": 100,
            "training_date": "2025-02-25T12:00:00"
        }
    }
}

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
def mock_ml_classifier_service():
    """Create a mock ML classifier service."""
    mock_service = AsyncMock()
    mock_service.classify_error = AsyncMock(return_value=SAMPLE_CLASSIFICATION_RESULT)
    mock_service.train_models = AsyncMock(return_value=SAMPLE_TRAINING_RESULT)
    mock_service.get_model_info = AsyncMock(return_value=SAMPLE_MODEL_INFO)
    mock_service.generate_training_data = AsyncMock(return_value={
        "status": "success",
        "num_errors": 100,
        "output_file": "training_data.json"
    })
    mock_service.cleanup = AsyncMock()
    return mock_service

class TestMLIntegration:
    """Tests for ML-based error classification integration."""
    
    def test_classify_error_endpoint(self, client, mock_ml_classifier_service):
        """Test the classify-error endpoint."""
        with patch.object(debug_service, 'get_ml_classifier_service', return_value=mock_ml_classifier_service):
            response = client.post(
                "/api/v1/ml/classify-error",
                json=SAMPLE_ERROR.dict()
            )
            
            assert response.status_code == 200
            assert response.json() == SAMPLE_CLASSIFICATION_RESULT
            mock_ml_classifier_service.classify_error.assert_called_once()
    
    def test_train_models_endpoint(self, client, mock_ml_classifier_service):
        """Test the train-models endpoint."""
        with patch.object(debug_service, 'get_ml_classifier_service', return_value=mock_ml_classifier_service):
            response = client.post(
                "/api/v1/ml/train-models",
                json={
                    "pipeline_id": "test_pipeline",
                    "limit": 100,
                    "model_types": ["random_forest"]
                }
            )
            
            assert response.status_code == 200
            assert response.json() == SAMPLE_TRAINING_RESULT
            mock_ml_classifier_service.train_models.assert_called_once()
    
    def test_model_info_endpoint(self, client, mock_ml_classifier_service):
        """Test the model-info endpoint."""
        with patch.object(debug_service, 'get_ml_classifier_service', return_value=mock_ml_classifier_service):
            response = client.get("/api/v1/ml/model-info")
            
            assert response.status_code == 200
            assert response.json() == SAMPLE_MODEL_INFO
            mock_ml_classifier_service.get_model_info.assert_called_once()
    
    def test_generate_training_data_endpoint(self, client, mock_ml_classifier_service):
        """Test the generate-training-data endpoint."""
        with patch.object(debug_service, 'get_ml_classifier_service', return_value=mock_ml_classifier_service):
            response = client.post(
                "/api/v1/ml/generate-training-data",
                json={
                    "output_file": "training_data.json",
                    "limit": 100
                }
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "success"
            mock_ml_classifier_service.generate_training_data.assert_called_once()

class TestWebSocketMLIntegration:
    """Tests for ML-based error classification integration in WebSocket."""
    
    @pytest.mark.asyncio
    async def test_classify_error_ml_command(self, mock_ml_classifier_service):
        """Test the classify_error_ml command in WebSocket."""
        # Mock WebSocket
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_json = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        # Mock CLI debugger
        mock_cli_debugger = AsyncMock()
        mock_cli_debugger.start_debug_session = AsyncMock(return_value=MagicMock())
        
        # Set up WebSocket receive_json to return different values on each call
        mock_websocket.receive_json.side_effect = [
            # First call: session parameters
            {
                "pipeline_id": "test_pipeline",
                "log_content": "test log content"
            },
            # Second call: classify_error_ml command
            {
                "command": "classify_error_ml",
                "error_id": "test_err_1",
                "model_types": {
                    "category": "random_forest",
                    "severity": "random_forest",
                    "stage": "random_forest"
                }
            },
            # Third call: exit command
            {
                "command": "exit"
            }
        ]
        
        # Mock session with errors
        mock_session = MagicMock()
        mock_session.errors = [SAMPLE_ERROR]
        mock_session.status = "active"
        mock_cli_debugger.start_debug_session.return_value = mock_session
        
        # Mock debug_service
        with patch.object(debug_service, 'get_cli_debugger', return_value=mock_cli_debugger), \
             patch.object(debug_service, 'get_ml_classifier_service', return_value=mock_ml_classifier_service), \
             patch.object(debug_service, 'active_sessions', {}):
            
            # Call WebSocket endpoint
            from main import websocket_debug_session
            await websocket_debug_session(mock_websocket, mock_cli_debugger)
            
            # Check that WebSocket was accepted and closed
            mock_websocket.accept.assert_called_once()
            mock_websocket.close.assert_called_once()
            
            # Check that classify_error_ml command was handled
            mock_ml_classifier_service.classify_error.assert_called_once()
            
            # Check that WebSocket sent the correct response
            mock_websocket.send_json.assert_any_call({
                "type": "ml_classification_result",
                "data": SAMPLE_CLASSIFICATION_RESULT
            })
    
    @pytest.mark.asyncio
    async def test_train_ml_models_command(self, mock_ml_classifier_service):
        """Test the train_ml_models command in WebSocket."""
        # Mock WebSocket
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_json = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        # Mock CLI debugger
        mock_cli_debugger = AsyncMock()
        mock_cli_debugger.start_debug_session = AsyncMock(return_value=MagicMock())
        
        # Set up WebSocket receive_json to return different values on each call
        mock_websocket.receive_json.side_effect = [
            # First call: session parameters
            {
                "pipeline_id": "test_pipeline",
                "log_content": "test log content"
            },
            # Second call: train_ml_models command
            {
                "command": "train_ml_models",
                "pipeline_id": "test_pipeline",
                "limit": 100,
                "model_types": ["random_forest"]
            },
            # Third call: exit command
            {
                "command": "exit"
            }
        ]
        
        # Mock session
        mock_session = MagicMock()
        mock_session.pipeline_id = "test_pipeline"
        mock_session.status = "active"
        mock_cli_debugger.start_debug_session.return_value = mock_session
        
        # Mock debug_service
        with patch.object(debug_service, 'get_cli_debugger', return_value=mock_cli_debugger), \
             patch.object(debug_service, 'get_ml_classifier_service', return_value=mock_ml_classifier_service), \
             patch.object(debug_service, 'active_sessions', {}):
            
            # Call WebSocket endpoint
            from main import websocket_debug_session
            await websocket_debug_session(mock_websocket, mock_cli_debugger)
            
            # Check that WebSocket was accepted and closed
            mock_websocket.accept.assert_called_once()
            mock_websocket.close.assert_called_once()
            
            # Check that train_ml_models command was handled
            mock_ml_classifier_service.train_models.assert_called_once()
            
            # Check that WebSocket sent the correct response
            mock_websocket.send_json.assert_any_call({
                "type": "ml_training_result",
                "data": SAMPLE_TRAINING_RESULT
            })
    
    @pytest.mark.asyncio
    async def test_get_ml_model_info_command(self, mock_ml_classifier_service):
        """Test the get_ml_model_info command in WebSocket."""
        # Mock WebSocket
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_json = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        # Mock CLI debugger
        mock_cli_debugger = AsyncMock()
        mock_cli_debugger.start_debug_session = AsyncMock(return_value=MagicMock())
        
        # Set up WebSocket receive_json to return different values on each call
        mock_websocket.receive_json.side_effect = [
            # First call: session parameters
            {
                "pipeline_id": "test_pipeline",
                "log_content": "test log content"
            },
            # Second call: get_ml_model_info command
            {
                "command": "get_ml_model_info"
            },
            # Third call: exit command
            {
                "command": "exit"
            }
        ]
        
        # Mock session
        mock_session = MagicMock()
        mock_session.status = "active"
        mock_cli_debugger.start_debug_session.return_value = mock_session
        
        # Mock debug_service
        with patch.object(debug_service, 'get_cli_debugger', return_value=mock_cli_debugger), \
             patch.object(debug_service, 'get_ml_classifier_service', return_value=mock_ml_classifier_service), \
             patch.object(debug_service, 'active_sessions', {}):
            
            # Call WebSocket endpoint
            from main import websocket_debug_session
            await websocket_debug_session(mock_websocket, mock_cli_debugger)
            
            # Check that WebSocket was accepted and closed
            mock_websocket.accept.assert_called_once()
            mock_websocket.close.assert_called_once()
            
            # Check that get_ml_model_info command was handled
            mock_ml_classifier_service.get_model_info.assert_called_once()
            
            # Check that WebSocket sent the correct response
            mock_websocket.send_json.assert_any_call({
                "type": "ml_model_info",
                "data": SAMPLE_MODEL_INFO
            })
