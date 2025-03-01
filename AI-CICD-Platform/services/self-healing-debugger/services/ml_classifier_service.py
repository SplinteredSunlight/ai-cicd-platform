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

from config import get_settings
from models.pipeline_debug import PipelineError, ErrorCategory, ErrorSeverity, PipelineStage
from models.ml_classifier import MLErrorClassifier

# Configure logging
logger = logging.getLogger(__name__)

class MLClassifierService:
    """
    Service for ML-based error classification.
    
    This service provides functionality for training and using ML models
    to classify pipeline errors.
    """
    
    def __init__(self):
        """Initialize the ML classifier service."""
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
        
        # Load models if available
        self._load_models()
    
    def _load_models(self):
        """Load all available models."""
        targets = ['category', 'severity', 'stage']
        model_types = ['random_forest', 'naive_bayes', 'logistic_regression']
        
        for target in targets:
            for model_type in model_types:
                try:
                    self.classifier.load_model(target, model_type)
                except Exception as e:
                    logger.warning(f"Could not load model {target}_{model_type}: {str(e)}")
    
    async def train_models(
        self,
        pipeline_id: Optional[str] = None,
        limit: int = 1000,
        model_types: List[str] = ['random_forest']
    ) -> Dict:
        """
        Train ML models using historical error data from Elasticsearch.
        
        Args:
            pipeline_id: Optional pipeline ID to filter errors
            limit: Maximum number of errors to retrieve
            model_types: List of model types to train
            
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
        
        for target in targets:
            for model_type in model_types:
                try:
                    result = self.classifier.train(errors, target, model_type)
                    results[f"{target}_{model_type}"] = {
                        "status": "success",
                        "accuracy": result['accuracy'],
                        "cv_mean": result['cv_mean'],
                        "num_samples": result['num_samples']
                    }
                except Exception as e:
                    logger.error(f"Error training {target}_{model_type} model: {str(e)}")
                    results[f"{target}_{model_type}"] = {
                        "status": "error",
                        "message": str(e)
                    }
        
        return {
            "status": "success",
            "models_trained": len(results),
            "results": results
        }
    
    async def _get_historical_errors(
        self,
        pipeline_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Retrieve historical errors from Elasticsearch.
        
        Args:
            pipeline_id: Optional pipeline ID to filter errors
            limit: Maximum number of errors to retrieve
            
        Returns:
            List of error dictionaries
        """
        try:
            index = f"{self.settings.elasticsearch_index_prefix}*"
            
            # Build query
            query = {
                "size": limit,
                "sort": [{"timestamp": "desc"}]
            }
            
            # Add pipeline_id filter if provided
            if pipeline_id:
                query["query"] = {
                    "term": {"pipeline_id": pipeline_id}
                }
            
            # Execute search
            result = await self.es_client.search(index=index, body=query)
            
            # Extract errors from search results
            errors = []
            for hit in result["hits"]["hits"]:
                error = hit["_source"]
                errors.append(error)
            
            return errors
            
        except Exception as e:
            logger.error(f"Error retrieving historical errors: {str(e)}")
            return []
    
    async def classify_error(
        self,
        error: Union[PipelineError, Dict, str],
        model_types: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Classify an error using ML models.
        
        Args:
            error: The error to classify (PipelineError object, dictionary, or string)
            model_types: Dictionary mapping targets to model types to use
                         (defaults to {'category': 'random_forest', 'severity': 'random_forest', 'stage': 'random_forest'})
                         
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
            
            # Classify error
            predictions = self.classifier.classify_error(error, model_types)
            
            # Format results
            results = {}
            for target, (prediction, confidence) in predictions.items():
                results[target] = {
                    "prediction": prediction,
                    "confidence": confidence
                }
            
            return {
                "status": "success",
                "classifications": results
            }
            
        except Exception as e:
            logger.error(f"Error classifying error: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
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
                    "cv_mean": info.get('cv_mean'),
                    "num_samples": info.get('num_samples'),
                    "training_date": info.get('training_date')
                }
            
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
        limit: int = 1000
    ) -> Dict:
        """
        Generate training data from historical errors and save to a file.
        
        Args:
            output_file: Path to save the training data
            limit: Maximum number of errors to retrieve
            
        Returns:
            Dictionary with generation results
        """
        try:
            # Retrieve historical errors
            errors = await self._get_historical_errors(None, limit)
            
            if not errors:
                return {
                    "status": "error",
                    "message": "No historical errors found for training data generation"
                }
            
            # Save to file
            with open(output_file, 'w') as f:
                json.dump(errors, f, indent=2)
            
            return {
                "status": "success",
                "num_errors": len(errors),
                "output_file": output_file
            }
            
        except Exception as e:
            logger.error(f"Error generating training data: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.es_client.close()
