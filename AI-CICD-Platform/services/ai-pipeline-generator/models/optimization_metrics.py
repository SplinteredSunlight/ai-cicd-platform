"""
Optimization metrics models for CI/CD pipelines.
This module provides models for storing and analyzing optimization metrics.
"""

from typing import Dict, List, Any, Optional, Union
from enum import Enum
import uuid
import datetime
import json

class MetricUnit(str, Enum):
    """Metric unit enumeration."""
    
    COUNT = "count"
    PERCENTAGE = "percentage"
    SECONDS = "seconds"
    BYTES = "bytes"
    MEGABYTES = "megabytes"
    CORES = "cores"
    MEMORY = "memory"
    CURRENCY = "currency"

class OptimizationType(str, Enum):
    """Optimization type enumeration."""
    
    STRUCTURE = "structure"
    PERFORMANCE = "performance"
    PARALLELIZATION = "parallelization"
    RESOURCE = "resource"
    CACHING = "caching"

class BaseMetric:
    """Base metric class."""
    
    def __init__(self, name: str, value: float, unit: MetricUnit, description: str,
               job_id: Optional[str] = None, optimization_type: Optional[str] = None):
        """Initialize the base metric."""
        self.name = name
        self.value = value
        self.unit = unit
        self.description = description
        self.job_id = job_id
        self.optimization_type = optimization_type
        self.timestamp = datetime.datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the metric to a dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "description": self.description,
            "job_id": self.job_id,
            "optimization_type": self.optimization_type,
            "timestamp": self.timestamp
        }

class StructureMetric(BaseMetric):
    """Structure metric class."""
    
    def __init__(self, name: str, value: float, unit: MetricUnit, description: str,
               job_id: Optional[str] = None, optimization_type: Optional[str] = None):
        """Initialize the structure metric."""
        super().__init__(name, value, unit, description, job_id, optimization_type)
        self.metric_type = "structure"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the metric to a dictionary."""
        result = super().to_dict()
        result["metric_type"] = self.metric_type
        return result

class PerformanceMetric(BaseMetric):
    """Performance metric class."""
    
    def __init__(self, name: str, value: float, unit: MetricUnit, description: str,
               job_id: Optional[str] = None, optimization_type: Optional[str] = None):
        """Initialize the performance metric."""
        super().__init__(name, value, unit, description, job_id, optimization_type)
        self.metric_type = "performance"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the metric to a dictionary."""
        result = super().to_dict()
        result["metric_type"] = self.metric_type
        return result

class ParallelizationMetric(BaseMetric):
    """Parallelization metric class."""
    
    def __init__(self, name: str, value: float, unit: MetricUnit, description: str,
               job_id: Optional[str] = None, optimization_type: Optional[str] = None):
        """Initialize the parallelization metric."""
        super().__init__(name, value, unit, description, job_id, optimization_type)
        self.metric_type = "parallelization"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the metric to a dictionary."""
        result = super().to_dict()
        result["metric_type"] = self.metric_type
        return result

class ResourceMetric(BaseMetric):
    """Resource metric class."""
    
    def __init__(self, name: str, value: float, unit: MetricUnit, description: str,
               job_id: Optional[str] = None, optimization_type: Optional[str] = None):
        """Initialize the resource metric."""
        super().__init__(name, value, unit, description, job_id, optimization_type)
        self.metric_type = "resource"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the metric to a dictionary."""
        result = super().to_dict()
        result["metric_type"] = self.metric_type
        return result

class CachingMetric(BaseMetric):
    """Caching metric class."""
    
    def __init__(self, name: str, value: float, unit: MetricUnit, description: str,
               job_id: Optional[str] = None, optimization_type: Optional[str] = None):
        """Initialize the caching metric."""
        super().__init__(name, value, unit, description, job_id, optimization_type)
        self.metric_type = "caching"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the metric to a dictionary."""
        result = super().to_dict()
        result["metric_type"] = self.metric_type
        return result

class OptimizationResult:
    """Optimization result class."""
    
    def __init__(self, pipeline_id: str, platform: str, optimization_type: OptimizationType,
               metrics_before: List[BaseMetric], metrics_after: List[BaseMetric],
               improvement_percentage: float, details: Dict[str, Any]):
        """Initialize the optimization result."""
        self.id = str(uuid.uuid4())
        self.pipeline_id = pipeline_id
        self.platform = platform
        self.optimization_type = optimization_type
        self.metrics_before = metrics_before
        self.metrics_after = metrics_after
        self.improvement_percentage = improvement_percentage
        self.details = details
        self.timestamp = datetime.datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the optimization result to a dictionary."""
        return {
            "id": self.id,
            "pipeline_id": self.pipeline_id,
            "platform": self.platform,
            "optimization_type": self.optimization_type,
            "metrics_before": [metric.to_dict() for metric in self.metrics_before],
            "metrics_after": [metric.to_dict() for metric in self.metrics_after],
            "improvement_percentage": self.improvement_percentage,
            "details": self.details,
            "timestamp": self.timestamp
        }

class OptimizationMetricsRepository:
    """Repository for optimization metrics."""
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize the optimization metrics repository."""
        self.storage_path = storage_path or "data/optimization_metrics.json"
        self.results = []
    
    def save_optimization_result(self, result: OptimizationResult) -> str:
        """
        Save an optimization result.
        
        Args:
            result: The optimization result to save
            
        Returns:
            The ID of the saved result
        """
        # Add the result to the in-memory list
        self.results.append(result)
        
        # Save the result to storage
        try:
            with open(self.storage_path, "w") as f:
                json.dump([result.to_dict() for result in self.results], f, indent=2)
        except Exception as e:
            # Log the error but don't fail
            print(f"Error saving optimization result: {e}")
        
        return result.id
    
    def get_optimization_result(self, result_id: str) -> Optional[OptimizationResult]:
        """
        Get an optimization result by ID.
        
        Args:
            result_id: The ID of the result to get
            
        Returns:
            The optimization result, or None if not found
        """
        for result in self.results:
            if result.id == result_id:
                return result
        
        return None
    
    def list_optimization_results(self, pipeline_id: Optional[str] = None,
                               optimization_type: Optional[OptimizationType] = None) -> List[OptimizationResult]:
        """
        List optimization results.
        
        Args:
            pipeline_id: Optional pipeline ID to filter by
            optimization_type: Optional optimization type to filter by
            
        Returns:
            List of optimization results
        """
        results = self.results
        
        if pipeline_id:
            results = [result for result in results if result.pipeline_id == pipeline_id]
        
        if optimization_type:
            results = [result for result in results if result.optimization_type == optimization_type]
        
        return results
    
    def delete_optimization_result(self, result_id: str) -> bool:
        """
        Delete an optimization result.
        
        Args:
            result_id: The ID of the result to delete
            
        Returns:
            True if the result was deleted, False otherwise
        """
        for i, result in enumerate(self.results):
            if result.id == result_id:
                # Remove the result from the in-memory list
                self.results.pop(i)
                
                # Save the updated list to storage
                try:
                    with open(self.storage_path, "w") as f:
                        json.dump([result.to_dict() for result in self.results], f, indent=2)
                except Exception as e:
                    # Log the error but don't fail
                    print(f"Error saving optimization results: {e}")
                
                return True
        
        return False
