"""
ML-based error classification service for the Self-Healing Debugger.
"""

from typing import List, Dict, Optional, Tuple, Union, Any
import os
import json
import asyncio
from datetime import datetime
import logging
from elasticsearch import AsyncElasticsearch
import aiohttp
import uuid

from config import get_settings
from models.pipeline_debug import PipelineError, ErrorCategory, ErrorSeverity, PipelineStage
from models.ml_classifier import MLErrorClassifier

# Configure logging
logger = logging.getLogger(__name__)

class MLClassifierService:
    """
    Service for ML-based error classification.
    
    This service provides functionality for training and using ML models
    to classify pipeline errors. It includes:
    - Advanced error classification with confidence scoring
    - Model training with hyperparameter tuning
    - Real-time classification updates via WebSocket
    - Integration with Elasticsearch for historical error data
    """
    
    def __init__(self, websocket_service=None):
        """
        Initialize the ML classifier service.
        
        Args:
            websocket_service: Optional WebSocket service for real-time updates
        """
        self.settings = get_settings()
        self.classifier = MLErrorClassifier(
            model_dir=os.path.join(os.path.dirname(__file__), '../models/trained')
        )
        self.es_client = AsyncElasticsearch(
            self.settings.elasticsearch_hosts,
            basic_auth=(
                self.settings.elasticsearch_username,
                self.settings.elasticsearch_password
            ) if self.settings.elasticsearch_username else None
        )
        
        # WebSocket service for real-time updates
        self.websocket_service = websocket_service
        
        # Default confidence threshold
        self.confidence_threshold = getattr(self.settings, 'ml_confidence_threshold', 0.6)
        
        # Load models if available
        self._load_models()
    
    def _load_models(self):
        """Load all available models."""
        targets = ['category', 'severity', 'stage']
        model_types = [
            'random_forest', 
            'gradient_boosting',
            'naive_bayes', 
            'logistic_regression',
            'svm'
        ]
        
        loaded_models = 0
        for target in targets:
            for model_type in model_types:
                try:
                    if self.classifier.load_model(target, model_type):
                        loaded_models += 1
                        logger.info(f"Loaded model {target}_{model_type}")
                except Exception as e:
                    logger.warning(f"Could not load model {target}_{model_type}: {str(e)}")
        
        logger.info(f"Loaded {loaded_models} ML classification models")
    
    async def train_models(
        self,
        pipeline_id: Optional[str] = None,
        limit: int = 1000,
        model_types: List[str] = ['random_forest'],
        hyperparameter_tuning: bool = False,
        class_weights: Optional[Dict[str, Dict[str, float]]] = None,
        emit_updates: bool = True
    ) -> Dict:
        """
        Train ML models using historical error data from Elasticsearch.
        
        Args:
            pipeline_id: Optional pipeline ID to filter errors
            limit: Maximum number of errors to retrieve
            model_types: List of model types to train
            hyperparameter_tuning: Whether to perform hyperparameter tuning
            class_weights: Optional dictionary mapping targets to class weights
            emit_updates: Whether to emit real-time updates via WebSocket
            
        Returns:
            Dictionary with training results
        """
        # Retrieve historical errors from Elasticsearch
        errors = await self._get_historical_errors(pipeline_id, limit)
        
        if not errors:
            logger.warning("No historical errors found for training")
            return {"status": "error", "message": "No historical errors found for training"}
        
        # Train models for each target and model type
        results = {}
        targets = ['category', 'severity', 'stage']
        
        # Create training session ID for tracking
        training_session_id = str(uuid.uuid4())
        
        # Emit training started event
        if emit_updates and self.websocket_service:
            await self._emit_training_started(training_session_id, {
                'pipeline_id': pipeline_id,
                'num_errors': len(errors),
                'model_types': model_types,
                'targets': targets,
                'hyperparameter_tuning': hyperparameter_tuning
            })
        
        for target in targets:
            for model_type in model_types:
                try:
                    # Emit model training started event
                    if emit_updates and self.websocket_service:
                        await self._emit_model_training_started(
                            training_session_id, target, model_type
                        )
                    
                    # Get class weights for this target if provided
                    target_weights = None
                    if class_weights and target in class_weights:
                        target_weights = class_weights[target]
                    
                    # Train model
                    result = self.classifier.train(
                        errors, 
                        target=target, 
                        model_type=model_type,
                        hyperparameter_tuning=hyperparameter_tuning,
                        class_weights=target_weights
                    )
                    
                    # Format result
                    model_result = {
                        "status": "success",
                        "accuracy": result['accuracy'],
                        "precision": result.get('precision'),
                        "recall": result.get('recall'),
                        "f1_score": result.get('f1_score'),
                        "cv_mean": result['cv_mean'],
                        "num_samples": result['num_samples'],
                        "class_distribution": result.get('class_distribution'),
                        "training_date": result.get('training_date')
                    }
                    
                    # Add best parameters if hyperparameter tuning was performed
                    if hyperparameter_tuning and 'best_params' in result:
                        model_result["best_params"] = result['best_params']
                    
                    results[f"{target}_{model_type}"] = model_result
                    
                    # Emit model training completed event
                    if emit_updates and self.websocket_service:
                        await self._emit_model_training_completed(
                            training_session_id, target, model_type, model_result
                        )
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error training {target}_{model_type} model: {error_msg}")
                    
                    results[f"{target}_{model_type}"] = {
                        "status": "error",
                        "message": error_msg
                    }
                    
                    # Emit model training error event
                    if emit_updates and self.websocket_service:
                        await self._emit_model_training_error(
                            training_session_id, target, model_type, error_msg
                        )
        
        # Emit training completed event
        if emit_updates and self.websocket_service:
            await self._emit_training_completed(training_session_id, results)
        
        return {
            "status": "success",
            "training_session_id": training_session_id,
            "models_trained": len([r for r in results.values() if r.get("status") == "success"]),
            "models_failed": len([r for r in results.values() if r.get("status") == "error"]),
            "results": results
        }
    
    async def _get_historical_errors(
        self,
        pipeline_id: Optional[str] = None,
        limit: int = 1000,
        error_types: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> List[Dict]:
        """
        Retrieve historical errors from Elasticsearch.
        
        Args:
            pipeline_id: Optional pipeline ID to filter errors
            limit: Maximum number of errors to retrieve
            error_types: Optional list of error types to filter
            date_range: Optional date range to filter (format: {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'})
            
        Returns:
            List of error dictionaries
        """
        try:
            index = f"{self.settings.elasticsearch_index_prefix}*"
            
            # Build query
            query_parts = []
            
            # Add pipeline_id filter if provided
            if pipeline_id:
                query_parts.append({"term": {"pipeline_id": pipeline_id}})
            
            # Add error types filter if provided
            if error_types:
                query_parts.append({"terms": {"category": error_types}})
            
            # Add date range filter if provided
            if date_range:
                date_filter = {"range": {"timestamp": {}}}
                if 'start' in date_range:
                    date_filter["range"]["timestamp"]["gte"] = date_range["start"]
                if 'end' in date_range:
                    date_filter["range"]["timestamp"]["lte"] = date_range["end"]
                query_parts.append(date_filter)
            
            # Combine query parts
            if query_parts:
                query = {
                    "size": limit,
                    "sort": [{"timestamp": "desc"}],
                    "query": {"bool": {"must": query_parts}}
                }
            else:
                query = {
                    "size": limit,
                    "sort": [{"timestamp": "desc"}]
                }
            
            # Execute search
            result = await self.es_client.search(index=index, body=query)
            
            # Extract errors from search results
            errors = []
            for hit in result["hits"]["hits"]:
                error = hit["_source"]
                errors.append(error)
            
            logger.info(f"Retrieved {len(errors)} historical errors from Elasticsearch")
            return errors
            
        except Exception as e:
            logger.error(f"Error retrieving historical errors: {str(e)}")
            return []
    
    async def classify_error(
        self,
        error: Union[PipelineError, Dict, str],
        model_types: Optional[Dict[str, str]] = None,
        confidence_threshold: Optional[float] = None,
        detailed: bool = False,
        emit_update: bool = True
    ) -> Dict:
        """
        Classify an error using ML models.
        
        Args:
            error: The error to classify (PipelineError object, dictionary, or string)
            model_types: Dictionary mapping targets to model types to use
                         (defaults to {'category': 'random_forest', 'severity': 'random_forest', 'stage': 'random_forest'})
            confidence_threshold: Minimum confidence threshold for a valid prediction
                                 (defaults to self.confidence_threshold)
            detailed: Whether to return detailed classification information
            emit_update: Whether to emit real-time update via WebSocket
                         
        Returns:
            Dictionary with classification results
        """
        try:
            # Set default model types if not provided
            if model_types is None:
                model_types = {
                    'category': 'random_forest',
                    'severity': 'random_forest',
                    'stage': 'random_forest'
                }
            
            # Set default confidence threshold if not provided
            if confidence_threshold is None:
                confidence_threshold = self.confidence_threshold
            
            # Classify error
            classification_result = self.classifier.classify_error(
                error, 
                model_types=model_types,
                confidence_threshold=confidence_threshold,
                detailed=detailed
            )
            
            # Extract error ID for WebSocket event
            error_id = classification_result.get('error_id')
            
            # Emit classification result via WebSocket
            if emit_update and self.websocket_service and error_id:
                await self._emit_classification_result(error_id, classification_result)
            
            # Add status to result
            classification_result["status"] = "success"
            
            return classification_result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error classifying error: {error_msg}")
            
            # Extract error ID if possible
            error_id = None
            if isinstance(error, PipelineError):
                error_id = error.error_id
            elif isinstance(error, dict) and 'error_id' in error:
                error_id = error['error_id']
            
            # Create error result
            error_result = {
                "status": "error",
                "message": error_msg,
                "error_id": error_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Emit error via WebSocket
            if emit_update and self.websocket_service and error_id:
                await self._emit_classification_error(error_id, error_msg)
            
            return error_result
    
    async def get_model_info(self) -> Dict:
        """
        Get information about all trained models.
        
        Returns:
            Dictionary with model information
        """
        try:
            # Get training history
            history = self.classifier.get_training_history()
            
            # Format results
            results = {}
            for model_key, info in history.items():
                results[model_key] = {
                    "target": info.get('target'),
                    "model_type": info.get('model_type'),
                    "accuracy": info.get('accuracy'),
                    "precision": info.get('precision'),
                    "recall": info.get('recall'),
                    "f1_score": info.get('f1_score'),
                    "cv_mean": info.get('cv_mean'),
                    "num_samples": info.get('num_samples'),
                    "training_date": info.get('training_date'),
                    "hyperparameter_tuning": info.get('hyperparameter_tuning', False),
                    "class_distribution": info.get('class_distribution')
                }
                
                # Add best parameters if hyperparameter tuning was performed
                if info.get('hyperparameter_tuning') and 'best_params' in info:
                    results[model_key]["best_params"] = info['best_params']
            
            return {
                "status": "success",
                "models": results
            }
            
        except Exception as e:
            logger.error(f"Error getting model info: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def generate_training_data(
        self,
        output_file: str = 'training_data.json',
        limit: int = 1000,
        pipeline_id: Optional[str] = None,
        error_types: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Generate training data from historical errors and save to a file.
        
        Args:
            output_file: Path to save the training data
            limit: Maximum number of errors to retrieve
            pipeline_id: Optional pipeline ID to filter errors
            error_types: Optional list of error types to filter
            date_range: Optional date range to filter
            
        Returns:
            Dictionary with generation results
        """
        try:
            # Retrieve historical errors
            errors = await self._get_historical_errors(
                pipeline_id=pipeline_id,
                limit=limit,
                error_types=error_types,
                date_range=date_range
            )
            
            if not errors:
                return {
                    "status": "error",
                    "message": "No historical errors found for training data generation"
                }
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # Save to file
            with open(output_file, 'w') as f:
                json.dump(errors, f, indent=2)
            
            return {
                "status": "success",
                "num_errors": len(errors),
                "output_file": output_file,
                "filters": {
                    "pipeline_id": pipeline_id,
                    "error_types": error_types,
                    "date_range": date_range
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating training data: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def evaluate_model(
        self,
        target: str = 'category',
        model_type: str = 'random_forest',
        test_data: Optional[List[Dict]] = None,
        test_size: float = 0.3,
        random_state: int = 42
    ) -> Dict:
        """
        Evaluate a trained model on test data.
        
        Args:
            target: Classification target ('category', 'severity', or 'stage')
            model_type: Type of model to evaluate
            test_data: Optional test data to use (if None, will retrieve from Elasticsearch)
            test_size: Proportion of data to use for testing (if test_data is None)
            random_state: Random seed for reproducibility
            
        Returns:
            Dictionary with evaluation results
        """
        try:
            model_key = f"{target}_{model_type}"
            
            # Check if model exists
            if not self.classifier.load_model(target, model_type):
                return {
                    "status": "error",
                    "message": f"Model {model_key} not found"
                }
            
            # Get test data if not provided
            if test_data is None:
                # Retrieve historical errors from Elasticsearch
                test_data = await self._get_historical_errors(limit=1000)
                
                if not test_data:
                    return {
                        "status": "error",
                        "message": "No test data available"
                    }
            
            # Convert to DataFrame
            import pandas as pd
            df = pd.DataFrame(test_data)
            
            # Ensure required columns exist
            required_columns = ['message', target]
            if not all(col in df.columns for col in required_columns):
                missing = [col for col in required_columns if col not in df.columns]
                return {
                    "status": "error",
                    "message": f"Missing required columns in test data: {missing}"
                }
            
            # Split data if needed
            from sklearn.model_selection import train_test_split
            if test_size > 0:
                _, X_test, _, y_test = train_test_split(
                    df, df[target], test_size=test_size, random_state=random_state
                )
            else:
                X_test = df
                y_test = df[target]
            
            # Get model
            model = self.classifier.models[model_key]
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
            accuracy = accuracy_score(y_test, y_pred)
            precision, recall, f1, _ = precision_recall_fscore_support(
                y_test, y_pred, average='weighted'
            )
            report = classification_report(y_test, y_pred, output_dict=True)
            
            # Return evaluation results
            return {
                "status": "success",
                "model_key": model_key,
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
                "report": report,
                "num_test_samples": len(X_test)
            }
            
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def set_confidence_threshold(self, threshold: float) -> Dict:
        """
        Set the confidence threshold for classifications.
        
        Args:
            threshold: New confidence threshold (0.0 to 1.0)
            
        Returns:
            Dictionary with result
        """
        try:
            # Validate threshold
            if not 0.0 <= threshold <= 1.0:
                return {
                    "status": "error",
                    "message": "Confidence threshold must be between 0.0 and 1.0"
                }
            
            # Set threshold
            self.confidence_threshold = threshold
            
            return {
                "status": "success",
                "confidence_threshold": threshold
            }
            
        except Exception as e:
            logger.error(f"Error setting confidence threshold: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    # WebSocket event emission methods
    
    async def _emit_classification_result(self, error_id: str, result: Dict) -> None:
        """Emit classification result via WebSocket."""
        if not self.websocket_service:
            return
        
        try:
            await self.websocket_service.emit_ml_classification(error_id, result)
            logger.debug(f"Emitted classification result for error {error_id}")
        except Exception as e:
            logger.error(f"Error emitting classification result: {str(e)}")
    
    async def _emit_classification_error(self, error_id: str, error_message: str) -> None:
        """Emit classification error via WebSocket."""
        if not self.websocket_service:
            return
        
        try:
            error_data = {
                "error": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.websocket_service.emit_ml_classification(error_id, error_data)
            logger.debug(f"Emitted classification error for error {error_id}")
        except Exception as e:
            logger.error(f"Error emitting classification error: {str(e)}")
    
    async def _emit_training_started(self, session_id: str, training_params: Dict) -> None:
        """Emit training started event via WebSocket."""
        if not self.websocket_service:
            return
        
        try:
            event_data = {
                "event": "training_started",
                "training_session_id": session_id,
                "params": training_params,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.websocket_service.emit_event(
                "debug_ml_training",
                event_data,
                category="DEBUG"
            )
            logger.debug(f"Emitted training started event for session {session_id}")
        except Exception as e:
            logger.error(f"Error emitting training started event: {str(e)}")
    
    async def _emit_training_completed(self, session_id: str, results: Dict) -> None:
        """Emit training completed event via WebSocket."""
        if not self.websocket_service:
            return
        
        try:
            event_data = {
                "event": "training_completed",
                "training_session_id": session_id,
                "results": results,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.websocket_service.emit_event(
                "debug_ml_training",
                event_data,
                category="DEBUG"
            )
            logger.debug(f"Emitted training completed event for session {session_id}")
        except Exception as e:
            logger.error(f"Error emitting training completed event: {str(e)}")
    
    async def _emit_model_training_started(self, session_id: str, target: str, model_type: str) -> None:
        """Emit model training started event via WebSocket."""
        if not self.websocket_service:
            return
        
        try:
            event_data = {
                "event": "model_training_started",
                "training_session_id": session_id,
                "target": target,
                "model_type": model_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.websocket_service.emit_event(
                "debug_ml_training",
                event_data,
                category="DEBUG"
            )
            logger.debug(f"Emitted model training started event for {target}_{model_type}")
        except Exception as e:
            logger.error(f"Error emitting model training started event: {str(e)}")
    
    async def _emit_model_training_completed(
        self, session_id: str, target: str, model_type: str, result: Dict
    ) -> None:
        """Emit model training completed event via WebSocket."""
        if not self.websocket_service:
            return
        
        try:
            event_data = {
                "event": "model_training_completed",
                "training_session_id": session_id,
                "target": target,
                "model_type": model_type,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.websocket_service.emit_event(
                "debug_ml_training",
                event_data,
                category="DEBUG"
            )
            logger.debug(f"Emitted model training completed event for {target}_{model_type}")
        except Exception as e:
            logger.error(f"Error emitting model training completed event: {str(e)}")
    
    async def _emit_model_training_error(
        self, session_id: str, target: str, model_type: str, error_message: str
    ) -> None:
        """Emit model training error event via WebSocket."""
        if not self.websocket_service:
            return
        
        try:
            event_data = {
                "event": "model_training_error",
                "training_session_id": session_id,
                "target": target,
                "model_type": model_type,
                "error": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.websocket_service.emit_event(
                "debug_ml_training",
                event_data,
                category="DEBUG"
            )
            logger.debug(f"Emitted model training error event for {target}_{model_type}")
        except Exception as e:
            logger.error(f"Error emitting model training error event: {str(e)}")
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.es_client.close()
