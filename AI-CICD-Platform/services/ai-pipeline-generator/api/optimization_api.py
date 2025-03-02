"""
API endpoints for pipeline optimization services.
This module provides API endpoints for optimizing CI/CD pipelines.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field

from services.pipeline_optimizer import PipelineOptimizerService
from services.performance_profiler import PerformanceProfilerService
from services.parallel_execution_optimizer import ParallelExecutionOptimizerService
from services.resource_optimizer import ResourceOptimizerService
from services.cache_optimizer import CacheOptimizerService
from models.optimization_metrics import OptimizationMetricsRepository

router = APIRouter(prefix="/optimization", tags=["optimization"])

# Models
class PipelineConfig(BaseModel):
    """Pipeline configuration model."""
    
    pipeline_id: str = Field(..., description="The pipeline ID")
    platform: str = Field(..., description="The CI/CD platform")
    config: Dict[str, Any] = Field(..., description="The pipeline configuration")
    execution_data: Optional[Dict[str, Any]] = Field(None, description="Optional pipeline execution data")

class OptimizationResponse(BaseModel):
    """Optimization response model."""
    
    pipeline_id: str = Field(..., description="The pipeline ID")
    platform: str = Field(..., description="The CI/CD platform")
    optimized_config: Dict[str, Any] = Field(..., description="The optimized pipeline configuration")
    optimization_details: Dict[str, Any] = Field(..., description="Optimization details")

class AnalysisResponse(BaseModel):
    """Analysis response model."""
    
    pipeline_id: str = Field(..., description="The pipeline ID")
    platform: str = Field(..., description="The CI/CD platform")
    analysis_results: Dict[str, Any] = Field(..., description="Analysis results")

# Dependencies
def get_pipeline_optimizer_service():
    """Get pipeline optimizer service."""
    return PipelineOptimizerService()

def get_performance_profiler_service():
    """Get performance profiler service."""
    return PerformanceProfilerService()

def get_parallel_execution_optimizer_service():
    """Get parallel execution optimizer service."""
    return ParallelExecutionOptimizerService()

def get_resource_optimizer_service():
    """Get resource optimizer service."""
    return ResourceOptimizerService()

def get_cache_optimizer_service():
    """Get cache optimizer service."""
    return CacheOptimizerService()

def get_optimization_metrics_repository():
    """Get optimization metrics repository."""
    return OptimizationMetricsRepository()

# Endpoints
@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_pipeline(
    pipeline_config: PipelineConfig,
    optimizer_service: PipelineOptimizerService = Depends(get_pipeline_optimizer_service)
):
    """
    Optimize a pipeline configuration.
    
    This endpoint optimizes a pipeline configuration using various optimization techniques.
    """
    try:
        optimized_config, optimization_details = optimizer_service.optimize_pipeline(
            pipeline_config.pipeline_id,
            pipeline_config.platform,
            pipeline_config.config,
            pipeline_config.execution_data
        )
        
        return {
            "pipeline_id": pipeline_config.pipeline_id,
            "platform": pipeline_config.platform,
            "optimized_config": optimized_config,
            "optimization_details": optimization_details
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing pipeline: {str(e)}")

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_pipeline(
    pipeline_config: PipelineConfig,
    optimizer_service: PipelineOptimizerService = Depends(get_pipeline_optimizer_service)
):
    """
    Analyze a pipeline configuration.
    
    This endpoint analyzes a pipeline configuration and identifies optimization opportunities.
    """
    try:
        analysis_results = optimizer_service.analyze_pipeline(
            pipeline_config.pipeline_id,
            pipeline_config.platform,
            pipeline_config.config,
            pipeline_config.execution_data
        )
        
        return {
            "pipeline_id": pipeline_config.pipeline_id,
            "platform": pipeline_config.platform,
            "analysis_results": analysis_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing pipeline: {str(e)}")

@router.post("/optimize/performance", response_model=OptimizationResponse)
async def optimize_performance(
    pipeline_config: PipelineConfig,
    profiler_service: PerformanceProfilerService = Depends(get_performance_profiler_service)
):
    """
    Optimize pipeline performance.
    
    This endpoint optimizes pipeline performance based on execution data.
    """
    if not pipeline_config.execution_data:
        raise HTTPException(status_code=400, detail="Execution data is required for performance optimization")
    
    try:
        # For performance optimization, we don't actually modify the pipeline configuration
        # Instead, we provide recommendations for improving performance
        analysis_results = profiler_service.analyze_pipeline_performance(
            pipeline_config.pipeline_id,
            pipeline_config.platform,
            pipeline_config.config,
            pipeline_config.execution_data
        )
        
        performance_report = profiler_service.generate_performance_report(
            pipeline_config.pipeline_id,
            pipeline_config.platform,
            analysis_results
        )
        
        return {
            "pipeline_id": pipeline_config.pipeline_id,
            "platform": pipeline_config.platform,
            "optimized_config": pipeline_config.config,  # No changes to config
            "optimization_details": {
                "analysis_results": analysis_results,
                "performance_report": performance_report
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing pipeline performance: {str(e)}")

@router.post("/optimize/parallel", response_model=OptimizationResponse)
async def optimize_parallel_execution(
    pipeline_config: PipelineConfig,
    optimizer_service: ParallelExecutionOptimizerService = Depends(get_parallel_execution_optimizer_service)
):
    """
    Optimize parallel execution in a pipeline.
    
    This endpoint optimizes parallel execution of pipeline steps.
    """
    try:
        optimized_config, optimization_details = optimizer_service.optimize_parallel_execution(
            pipeline_config.pipeline_id,
            pipeline_config.platform,
            pipeline_config.config,
            pipeline_config.execution_data
        )
        
        return {
            "pipeline_id": pipeline_config.pipeline_id,
            "platform": pipeline_config.platform,
            "optimized_config": optimized_config,
            "optimization_details": optimization_details
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing parallel execution: {str(e)}")

@router.post("/optimize/resources", response_model=OptimizationResponse)
async def optimize_resource_usage(
    pipeline_config: PipelineConfig,
    optimizer_service: ResourceOptimizerService = Depends(get_resource_optimizer_service)
):
    """
    Optimize resource usage in a pipeline.
    
    This endpoint optimizes resource usage in pipeline jobs.
    """
    try:
        optimized_config, optimization_details = optimizer_service.optimize_resource_usage(
            pipeline_config.pipeline_id,
            pipeline_config.platform,
            pipeline_config.config,
            pipeline_config.execution_data
        )
        
        return {
            "pipeline_id": pipeline_config.pipeline_id,
            "platform": pipeline_config.platform,
            "optimized_config": optimized_config,
            "optimization_details": optimization_details
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing resource usage: {str(e)}")

@router.post("/optimize/caching", response_model=OptimizationResponse)
async def optimize_caching_strategies(
    pipeline_config: PipelineConfig,
    optimizer_service: CacheOptimizerService = Depends(get_cache_optimizer_service)
):
    """
    Optimize caching strategies in a pipeline.
    
    This endpoint optimizes caching strategies in pipeline jobs.
    """
    try:
        optimized_config, optimization_details = optimizer_service.optimize_caching_strategies(
            pipeline_config.pipeline_id,
            pipeline_config.platform,
            pipeline_config.config,
            pipeline_config.execution_data
        )
        
        return {
            "pipeline_id": pipeline_config.pipeline_id,
            "platform": pipeline_config.platform,
            "optimized_config": optimized_config,
            "optimization_details": optimization_details
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing caching strategies: {str(e)}")

@router.get("/metrics/{pipeline_id}")
async def get_optimization_metrics(
    pipeline_id: str,
    optimization_type: Optional[str] = Query(None, description="Filter by optimization type"),
    metrics_repository: OptimizationMetricsRepository = Depends(get_optimization_metrics_repository)
):
    """
    Get optimization metrics for a pipeline.
    
    This endpoint retrieves optimization metrics for a pipeline.
    """
    try:
        results = metrics_repository.list_optimization_results(
            pipeline_id=pipeline_id,
            optimization_type=optimization_type
        )
        
        return {
            "pipeline_id": pipeline_id,
            "optimization_type": optimization_type,
            "results": [result.to_dict() for result in results]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving optimization metrics: {str(e)}")

@router.get("/metrics/{pipeline_id}/{result_id}")
async def get_optimization_result(
    pipeline_id: str,
    result_id: str,
    metrics_repository: OptimizationMetricsRepository = Depends(get_optimization_metrics_repository)
):
    """
    Get a specific optimization result.
    
    This endpoint retrieves a specific optimization result.
    """
    try:
        result = metrics_repository.get_optimization_result(result_id)
        
        if not result or result.pipeline_id != pipeline_id:
            raise HTTPException(status_code=404, detail="Optimization result not found")
        
        return result.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving optimization result: {str(e)}")
