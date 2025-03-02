"""
Pipeline optimization service for CI/CD pipelines.
This module provides tools to analyze and optimize CI/CD pipeline structures.
"""

from typing import Dict, List, Any, Optional, Tuple
import copy
import logging

from services.performance_profiler import PerformanceProfilerService
from services.parallel_execution_optimizer import ParallelExecutionOptimizerService
from services.resource_optimizer import ResourceOptimizerService
from services.cache_optimizer import CacheOptimizerService
from models.optimization_metrics import (
    OptimizationMetricsRepository,
    StructureMetric,
    MetricUnit,
    OptimizationResult,
    OptimizationType
)

logger = logging.getLogger(__name__)

class PipelineOptimizerService:
    """Service for optimizing CI/CD pipeline structures."""
    
    def __init__(self, metrics_repository: Optional[OptimizationMetricsRepository] = None):
        """Initialize the pipeline optimizer service."""
        self.metrics_repository = metrics_repository or OptimizationMetricsRepository()
        self.performance_profiler = PerformanceProfilerService(self.metrics_repository)
        self.parallel_execution_optimizer = ParallelExecutionOptimizerService(self.metrics_repository)
        self.resource_optimizer = ResourceOptimizerService(self.metrics_repository)
        self.cache_optimizer = CacheOptimizerService(self.metrics_repository)
    
    def analyze_pipeline(self, pipeline_id: str, platform: str,
                       pipeline_config: Dict[str, Any],
                       execution_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze a pipeline configuration and identify optimization opportunities.
        
        Args:
            pipeline_id: The pipeline ID
            platform: The CI/CD platform
            pipeline_config: The pipeline configuration
            execution_data: Optional pipeline execution data
            
        Returns:
            Analysis results with optimization opportunities
        """
        # Extract components from the pipeline configuration
        components = self._extract_components(platform, pipeline_config)
        
        # Analyze pipeline structure
        structure_analysis = self._analyze_pipeline_structure(
            pipeline_id, platform, components
        )
        
        # Analyze performance if execution data is available
        performance_analysis = {}
        if execution_data:
            performance_analysis = self.performance_profiler.analyze_pipeline_performance(
                pipeline_id, platform, pipeline_config, execution_data
            )
        
        # Analyze parallelization opportunities
        parallelization_analysis = self.parallel_execution_optimizer.analyze_parallelization_opportunities(
            pipeline_id, platform, pipeline_config, execution_data
        )
        
        # Analyze resource usage
        resource_analysis = self.resource_optimizer.analyze_resource_usage(
            pipeline_id, platform, pipeline_config, execution_data
        )
        
        # Analyze caching strategies
        caching_analysis = self.cache_optimizer.analyze_caching_strategies(
            pipeline_id, platform, pipeline_config, execution_data
        )
        
        # Combine all analyses
        combined_analysis = {
            "pipeline_id": pipeline_id,
            "platform": platform,
            "components": components,
            "structure_analysis": structure_analysis,
            "performance_analysis": performance_analysis,
            "parallelization_analysis": parallelization_analysis,
            "resource_analysis": resource_analysis,
            "caching_analysis": caching_analysis
        }
        
        # Create optimization result
        result = OptimizationResult(
            pipeline_id=pipeline_id,
            platform=platform,
            optimization_type=OptimizationType.STRUCTURE,
            metrics_before=structure_analysis.get("metrics", []),
            metrics_after=[],  # Will be populated after optimization
            improvement_percentage=0,  # Will be calculated after optimization
            details=combined_analysis
        )
        
        # Save the result
        self.metrics_repository.save_optimization_result(result)
        
        return combined_analysis
    
    def optimize_pipeline(self, pipeline_id: str, platform: str,
                        pipeline_config: Dict[str, Any],
                        execution_data: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Optimize a pipeline configuration.
        
        Args:
            pipeline_id: The pipeline ID
            platform: The CI/CD platform
            pipeline_config: The pipeline configuration
            execution_data: Optional pipeline execution data
            
        Returns:
            Tuple containing:
            - The optimized pipeline configuration
            - Optimization details
        """
        # Create a deep copy of the pipeline config to avoid modifying the original
        optimized_config = copy.deepcopy(pipeline_config)
        
        # Analyze the pipeline
        analysis = self.analyze_pipeline(pipeline_id, platform, pipeline_config, execution_data)
        
        # Apply structure optimizations
        optimized_config, structure_optimizations = self._apply_structure_optimizations(
            platform, optimized_config, analysis["structure_analysis"]
        )
        
        # Apply parallelization optimizations
        optimized_config, parallelization_optimizations = self.parallel_execution_optimizer._apply_parallelization_optimizations(
            platform, optimized_config, analysis["parallelization_analysis"]
        )
        
        # Apply resource optimizations
        optimized_config, resource_optimizations = self.resource_optimizer._apply_resource_optimizations(
            platform, optimized_config, analysis["resource_analysis"]
        )
        
        # Apply caching optimizations
        optimized_config, caching_optimizations = self.cache_optimizer._apply_caching_optimizations(
            platform, optimized_config, analysis["caching_analysis"]
        )
        
        # Combine all optimizations
        applied_optimizations = {
            "structure_optimizations": structure_optimizations,
            "parallelization_optimizations": parallelization_optimizations,
            "resource_optimizations": resource_optimizations,
            "caching_optimizations": caching_optimizations
        }
        
        # Calculate improvement metrics
        improvement_metrics = self._calculate_improvement_metrics(
            pipeline_id, platform, pipeline_config, optimized_config, analysis
        )
        
        # Create optimization result
        result = OptimizationResult(
            pipeline_id=pipeline_id,
            platform=platform,
            optimization_type=OptimizationType.STRUCTURE,
            metrics_before=analysis["structure_analysis"].get("metrics", []),
            metrics_after=improvement_metrics,
            improvement_percentage=improvement_metrics[0].value if improvement_metrics else 0,
            details={
                "original_analysis": analysis,
                "applied_optimizations": applied_optimizations
            }
        )
        
        # Save the result
        self.metrics_repository.save_optimization_result(result)
        
        return optimized_config, {
            "original_analysis": analysis,
            "applied_optimizations": applied_optimizations,
            "improvement_metrics": [metric.to_dict() for metric in improvement_metrics]
        }
    
    def _extract_components(self, platform: str, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract components from a pipeline configuration.
        
        Args:
            platform: The CI/CD platform
            pipeline_config: The pipeline configuration
            
        Returns:
            Dictionary of component IDs to component configurations
        """
        components = {}
        
        if platform == "github-actions":
            # Extract jobs from GitHub Actions workflow
            jobs = pipeline_config.get("jobs", {})
            
            for job_id, job_config in jobs.items():
                components[job_id] = {
                    "id": job_id,
                    "type": "job",
                    "config": job_config,
                    "steps": job_config.get("steps", [])
                }
        
        elif platform == "gitlab-ci":
            # Extract jobs from GitLab CI pipeline
            for job_id, job_config in pipeline_config.items():
                if isinstance(job_config, dict) and "stage" in job_config:
                    components[job_id] = {
                        "id": job_id,
                        "type": "job",
                        "config": job_config,
                        "stage": job_config.get("stage"),
                        "script": job_config.get("script", [])
                    }
        
        elif platform == "circle-ci":
            # Extract jobs from CircleCI config
            jobs = pipeline_config.get("jobs", {})
            
            for job_id, job_config in jobs.items():
                components[job_id] = {
                    "id": job_id,
                    "type": "job",
                    "config": job_config,
                    "steps": job_config.get("steps", [])
                }
        
        elif platform == "jenkins":
            # Extract stages from Jenkins pipeline
            stages = pipeline_config.get("stages", [])
            
            for i, stage in enumerate(stages):
                if "name" in stage:
                    stage_id = stage["name"]
                    
                    components[stage_id] = {
                        "id": stage_id,
                        "type": "stage",
                        "config": stage,
                        "steps": stage.get("steps", []),
                        "stage_index": i
                    }
        
        return components
    
    def _analyze_pipeline_structure(self, pipeline_id: str, platform: str,
                                 components: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze pipeline structure.
        
        Args:
            pipeline_id: The pipeline ID
            platform: The CI/CD platform
            components: Dictionary of component IDs to component configurations
            
        Returns:
            Analysis results with structure optimization opportunities
        """
        # Identify redundant steps
        redundant_steps = self._identify_redundant_steps(platform, components)
        
        # Identify dependency issues
        dependency_issues = self._identify_dependency_issues(platform, components)
        
        # Identify conditional execution opportunities
        conditional_execution_opportunities = self._identify_conditional_execution_opportunities(platform, components)
        
        # Identify pipeline splitting opportunities
        splitting_opportunities = self._identify_splitting_opportunities(platform, components)
        
        # Create metrics
        metrics = self._create_structure_metrics(pipeline_id, platform, components, redundant_steps, dependency_issues)
        
        return {
            "redundant_steps": redundant_steps,
            "dependency_issues": dependency_issues,
            "conditional_execution_opportunities": conditional_execution_opportunities,
            "splitting_opportunities": splitting_opportunities,
            "metrics": metrics
        }
    
    def _identify_redundant_steps(self, platform: str, components: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify redundant steps in pipeline components.
        
        Args:
            platform: The CI/CD platform
            components: Dictionary of component IDs to component configurations
            
        Returns:
            List of redundant steps
        """
        redundant_steps = []
        
        if platform == "github-actions":
            # Check for redundant checkout steps
            checkout_steps = {}
            
            for component_id, component in components.items():
                steps = component.get("steps", [])
                
                for i, step in enumerate(steps):
                    if isinstance(step, dict) and step.get("uses", "").startswith("actions/checkout@"):
                        if component_id not in checkout_steps:
                            checkout_steps[component_id] = []
                        
                        checkout_steps[component_id].append({
                            "step_index": i,
                            "step": step
                        })
            
            # Identify jobs with multiple checkout steps
            for component_id, checkouts in checkout_steps.items():
                if len(checkouts) > 1:
                    # Keep the first checkout step, mark the rest as redundant
                    for checkout in checkouts[1:]:
                        redundant_steps.append({
                            "component_id": component_id,
                            "step_index": checkout["step_index"],
                            "step": checkout["step"],
                            "reason": "Redundant checkout step"
                        })
        
        # Add more platform-specific redundant step detection logic here
        
        return redundant_steps
    
    def _identify_dependency_issues(self, platform: str, components: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify dependency issues in pipeline components.
        
        Args:
            platform: The CI/CD platform
            components: Dictionary of component IDs to component configurations
            
        Returns:
            List of dependency issues
        """
        dependency_issues = []
        
        if platform == "github-actions":
            # Check for circular dependencies
            dependencies = {}
            
            for component_id, component in components.items():
                config = component.get("config", {})
                needs = config.get("needs", [])
                
                if isinstance(needs, str):
                    needs = [needs]
                
                dependencies[component_id] = needs
            
            # Check for circular dependencies
            for component_id, needs in dependencies.items():
                for need in needs:
                    if need in dependencies and component_id in dependencies[need]:
                        dependency_issues.append({
                            "component_id": component_id,
                            "dependency": need,
                            "type": "circular",
                            "reason": f"Circular dependency between {component_id} and {need}"
                        })
        
        # Add more platform-specific dependency issue detection logic here
        
        return dependency_issues
    
    def _identify_conditional_execution_opportunities(self, platform: str, components: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify conditional execution opportunities in pipeline components.
        
        Args:
            platform: The CI/CD platform
            components: Dictionary of component IDs to component configurations
            
        Returns:
            List of conditional execution opportunities
        """
        conditional_execution_opportunities = []
        
        if platform == "github-actions":
            # Check for jobs that could use path filters
            for component_id, component in components.items():
                config = component.get("config", {})
                
                # Check if the job already has path filters
                if "paths" in config.get("on", {}).get("push", {}):
                    continue
                
                # Check if the job is related to a specific directory
                steps = component.get("steps", [])
                directory_patterns = set()
                
                for step in steps:
                    if isinstance(step, dict):
                        run = step.get("run", "")
                        
                        if run:
                            # Check for commands that operate on specific directories
                            if "cd " in run:
                                for line in run.split("\n"):
                                    if line.strip().startswith("cd "):
                                        directory = line.strip()[3:].strip()
                                        if directory and directory != "." and directory != "..":
                                            directory_patterns.add(directory)
                
                if directory_patterns:
                    conditional_execution_opportunities.append({
                        "component_id": component_id,
                        "type": "path_filter",
                        "directories": list(directory_patterns),
                        "reason": f"Job {component_id} could use path filters for {', '.join(directory_patterns)}"
                    })
        
        # Add more platform-specific conditional execution opportunity detection logic here
        
        return conditional_execution_opportunities
    
    def _identify_splitting_opportunities(self, platform: str, components: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify pipeline splitting opportunities.
        
        Args:
            platform: The CI/CD platform
            components: Dictionary of component IDs to component configurations
            
        Returns:
            List of pipeline splitting opportunities
        """
        splitting_opportunities = []
        
        if platform == "github-actions":
            # Check for jobs with many steps that could be split
            for component_id, component in components.items():
                steps = component.get("steps", [])
                
                if len(steps) > 10:
                    # Identify logical groups of steps
                    step_groups = []
                    current_group = []
                    current_group_name = None
                    
                    for i, step in enumerate(steps):
                        if isinstance(step, dict):
                            name = step.get("name", "")
                            
                            if name and ":" in name:
                                # This step has a name with a prefix, which could indicate a logical group
                                prefix = name.split(":")[0].strip()
                                
                                if prefix != current_group_name:
                                    # Start a new group
                                    if current_group:
                                        step_groups.append({
                                            "name": current_group_name or "Unknown",
                                            "steps": current_group
                                        })
                                    
                                    current_group = [i]
                                    current_group_name = prefix
                                else:
                                    # Add to current group
                                    current_group.append(i)
                            else:
                                # Add to current group
                                current_group.append(i)
                    
                    # Add the last group
                    if current_group:
                        step_groups.append({
                            "name": current_group_name or "Unknown",
                            "steps": current_group
                        })
                    
                    # If we found logical groups, suggest splitting
                    if len(step_groups) > 1:
                        splitting_opportunities.append({
                            "component_id": component_id,
                            "type": "logical_groups",
                            "groups": step_groups,
                            "reason": f"Job {component_id} has {len(steps)} steps that could be split into {len(step_groups)} logical groups"
                        })
                    else:
                        # Suggest splitting based on step count
                        splitting_opportunities.append({
                            "component_id": component_id,
                            "type": "step_count",
                            "step_count": len(steps),
                            "reason": f"Job {component_id} has {len(steps)} steps and could be split into smaller jobs"
                        })
        
        # Add more platform-specific splitting opportunity detection logic here
        
        return splitting_opportunities
    
    def _create_structure_metrics(self, pipeline_id: str, platform: str,
                               components: Dict[str, Any],
                               redundant_steps: List[Dict[str, Any]],
                               dependency_issues: List[Dict[str, Any]]) -> List[StructureMetric]:
        """
        Create structure metrics.
        
        Args:
            pipeline_id: The pipeline ID
            platform: The CI/CD platform
            components: Dictionary of component IDs to component configurations
            redundant_steps: List of redundant steps
            dependency_issues: List of dependency issues
            
        Returns:
            List of structure metrics
        """
        metrics = []
        
        # Calculate component count
        component_count = len(components)
        metrics.append(StructureMetric(
            name="component_count",
            value=component_count,
            unit=MetricUnit.COUNT,
            description=f"Number of components in the pipeline",
            pipeline_id=pipeline_id,
            optimization_type=OptimizationType.STRUCTURE
        ))
        
        # Calculate step count
        step_count = 0
        for component in components.values():
            steps = component.get("steps", [])
            step_count += len(steps)
        
        metrics.append(StructureMetric(
            name="step_count",
            value=step_count,
            unit=MetricUnit.COUNT,
            description=f"Number of steps in the pipeline",
            pipeline_id=pipeline_id,
            optimization_type=OptimizationType.STRUCTURE
        ))
        
        # Calculate redundant step count
        redundant_step_count = len(redundant_steps)
        metrics.append(StructureMetric(
            name="redundant_step_count",
            value=redundant_step_count,
            unit=MetricUnit.COUNT,
            description=f"Number of redundant steps in the pipeline",
            pipeline_id=pipeline_id,
            optimization_type=OptimizationType.STRUCTURE
        ))
        
        # Calculate dependency issue count
        dependency_issue_count = len(dependency_issues)
        metrics.append(StructureMetric(
            name="dependency_issue_count",
            value=dependency_issue_count,
            unit=MetricUnit.COUNT,
            description=f"Number of dependency issues in the pipeline",
            pipeline_id=pipeline_id,
            optimization_type=OptimizationType.STRUCTURE
        ))
        
        # Calculate redundancy percentage
        if step_count > 0:
            redundancy_percentage = (redundant_step_count / step_count) * 100
            metrics.append(StructureMetric(
                name="redundancy_percentage",
                value=redundancy_percentage,
                unit=MetricUnit.PERCENTAGE,
                description=f"Percentage of redundant steps in the pipeline",
                pipeline_id=pipeline_id,
                optimization_type=OptimizationType.STRUCTURE
            ))
        
        return metrics
    
    def _apply_structure_optimizations(self, platform: str, pipeline_config: Dict[str, Any],
                                    structure_analysis: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Apply structure optimizations to pipeline config.
        
        Args:
            platform: The CI/CD platform
            pipeline_config: The pipeline configuration
            structure_analysis: Structure analysis results
            
        Returns:
            Tuple containing:
            - The optimized pipeline configuration
            - List of applied optimizations
        """
        optimized_config = copy.deepcopy(pipeline_config)
        applied_optimizations = []
        
        if platform == "github-actions":
            # Remove redundant steps
            redundant_steps = structure_analysis.get("redundant_steps", [])
            
            for redundant_step in redundant_steps:
                component_id = redundant_step["component_id"]
                step_index = redundant_step["step_index"]
                
                if "jobs" in optimized_config and component_id in optimized_config["jobs"]:
                    job_config = optimized_config["jobs"][component_id]
                    
                    if "steps" in job_config and 0 <= step_index < len(job_config["steps"]):
                        # Remove the redundant step
                        removed_step = job_config["steps"].pop(step_index)
                        
                        applied_optimizations.append({
                            "type": "remove_redundant_step",
                            "component_id": component_id,
                            "step_index": step_index,
                            "step": removed_step,
                            "reason": redundant_step["reason"]
                        })
            
            # Add conditional execution
            conditional_execution_opportunities = structure_analysis.get("conditional_execution_opportunities", [])
            
            for opportunity in conditional_execution_opportunities:
                component_id = opportunity["component_id"]
                
                if "jobs" in optimized_config and component_id in optimized_config["jobs"]:
                    job_config = optimized_config["jobs"][component_id]
                    
                    if opportunity["type"] == "path_filter":
                        # Add path filters
                        directories = opportunity["directories"]
                        
                        if "on" not in job_config:
                            job_config["on"] = {}
                        
                        if "push" not in job_config["on"]:
                            job_config["on"]["push"] = {}
                        
                        if "paths" not in job_config["on"]["push"]:
                            job_config["on"]["push"]["paths"] = []
                        
                        for directory in directories:
                            path_pattern = f"{directory}/**"
                            
                            if path_pattern not in job_config["on"]["push"]["paths"]:
                                job_config["on"]["push"]["paths"].append(path_pattern)
                        
                        applied_optimizations.append({
                            "type": "add_path_filters",
                            "component_id": component_id,
                            "directories": directories,
                            "reason": opportunity["reason"]
                        })
        
        # Add more platform-specific structure optimization logic here
        
        return optimized_config, applied_optimizations
    
    def _calculate_improvement_metrics(self, pipeline_id: str, platform: str,
                                    original_config: Dict[str, Any],
                                    optimized_config: Dict[str, Any],
                                    analysis: Dict[str, Any]) -> List[StructureMetric]:
        """
        Calculate improvement metrics.
        
        Args:
            pipeline_id: The pipeline ID
            platform: The CI/CD platform
            original_config: The original pipeline configuration
            optimized_config: The optimized pipeline configuration
            analysis: Analysis results
            
        Returns:
            List of improvement metrics
        """
        metrics = []
        
        # Calculate overall improvement percentage
        structure_metrics = analysis["structure_analysis"].get("metrics", [])
        redundancy_percentage = 0
        
        for metric in structure_metrics:
            if metric.name == "redundancy_percentage":
                redundancy_percentage = metric.value
        
        # Assume that removing redundant steps improves the pipeline by the redundancy percentage
        metrics.append(StructureMetric(
            name="overall_improvement_percentage",
            value=redundancy_percentage,
            unit=MetricUnit.PERCENTAGE,
            description=f"Overall improvement percentage",
            pipeline_id=pipeline_id,
            optimization_type=OptimizationType.STRUCTURE
        ))
        
        return metrics
