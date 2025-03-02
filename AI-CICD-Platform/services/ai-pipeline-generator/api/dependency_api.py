"""
Dependency API for the AI Pipeline Generator service.
This module provides API endpoints for dependency analysis.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, List, Any, Optional

from ..services.dependency_analyzer import DependencyAnalyzerService
from ..services.code_analyzer import CodeAnalyzerService
from ..services.package_analyzer import PackageAnalyzerService
from ..services.graph_visualizer import GraphVisualizerService
from ..services.impact_analyzer import ImpactAnalyzerService
from ..services.build_optimizer import BuildOptimizerService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/dependencies",
    tags=["dependencies"],
    responses={404: {"description": "Not found"}},
)

# Create services
dependency_analyzer = DependencyAnalyzerService()
code_analyzer = CodeAnalyzerService()
package_analyzer = PackageAnalyzerService()
graph_visualizer = GraphVisualizerService()
impact_analyzer = ImpactAnalyzerService()
build_optimizer = BuildOptimizerService()

@router.post("/analyze")
async def analyze_dependencies(
    project_path: str = Body(..., description="Path to the project directory"),
    languages: Optional[List[str]] = Body(None, description="List of languages to analyze"),
    include_patterns: Optional[List[str]] = Body(None, description="List of glob patterns to include"),
    exclude_patterns: Optional[List[str]] = Body(None, description="List of glob patterns to exclude"),
    analyze_imports: bool = Body(True, description="Whether to analyze imports"),
    analyze_function_calls: bool = Body(True, description="Whether to analyze function calls"),
    analyze_class_hierarchy: bool = Body(True, description="Whether to analyze class hierarchy"),
    analyze_packages: bool = Body(True, description="Whether to analyze package dependencies"),
    max_depth: Optional[int] = Body(None, description="Maximum depth to analyze")
) -> Dict[str, Any]:
    """
    Analyze dependencies in a project.
    """
    try:
        # Analyze dependencies
        dependency_graph = dependency_analyzer.analyze_project(
            project_path,
            languages=languages,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            analyze_imports=analyze_imports,
            analyze_function_calls=analyze_function_calls,
            analyze_class_hierarchy=analyze_class_hierarchy,
            analyze_packages=analyze_packages,
            max_depth=max_depth
        )
        
        # Calculate metrics
        metrics = dependency_analyzer.calculate_metrics(dependency_graph)
        
        # Create visualization data
        visualization_data = graph_visualizer.create_visualization_data(dependency_graph)
        
        # Return result
        return {
            "dependency_graph": visualization_data["data"],
            "metrics": metrics,
            "stats": visualization_data["stats"]
        }
    except Exception as e:
        logger.error(f"Error analyzing dependencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/code")
async def analyze_code_dependencies(
    project_path: str = Body(..., description="Path to the project directory"),
    languages: Optional[List[str]] = Body(None, description="List of languages to analyze"),
    include_patterns: Optional[List[str]] = Body(None, description="List of glob patterns to include"),
    exclude_patterns: Optional[List[str]] = Body(None, description="List of glob patterns to exclude"),
    analyze_imports: bool = Body(True, description="Whether to analyze imports"),
    analyze_function_calls: bool = Body(True, description="Whether to analyze function calls"),
    analyze_class_hierarchy: bool = Body(True, description="Whether to analyze class hierarchy"),
    max_depth: Optional[int] = Body(None, description="Maximum depth to analyze")
) -> Dict[str, Any]:
    """
    Analyze code dependencies in a project.
    """
    try:
        # Analyze code dependencies
        code_dependencies = code_analyzer.analyze_code_dependencies(
            project_path,
            languages=languages,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            analyze_imports=analyze_imports,
            analyze_function_calls=analyze_function_calls,
            analyze_class_hierarchy=analyze_class_hierarchy,
            max_depth=max_depth
        )
        
        # Return result
        return {
            "code_dependencies": code_dependencies
        }
    except Exception as e:
        logger.error(f"Error analyzing code dependencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/packages")
async def analyze_package_dependencies(
    project_path: str = Body(..., description="Path to the project directory")
) -> Dict[str, Any]:
    """
    Analyze package dependencies in a project.
    """
    try:
        # Analyze package dependencies
        package_dependencies = package_analyzer.analyze_project_dependencies(project_path)
        
        # Return result
        return {
            "package_dependencies": package_dependencies
        }
    except Exception as e:
        logger.error(f"Error analyzing package dependencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/visualize")
async def visualize_dependencies(
    project_path: str = Body(..., description="Path to the project directory"),
    format: str = Body("json", description="Output format (json, dot, png, svg)"),
    layout: str = Body("spring", description="Layout algorithm to use"),
    include_node_types: Optional[List[str]] = Body(None, description="List of node types to include"),
    include_edge_types: Optional[List[str]] = Body(None, description="List of edge types to include"),
    group_by: Optional[str] = Body(None, description="Attribute to group nodes by"),
    max_nodes: int = Body(100, description="Maximum number of nodes to include")
) -> Dict[str, Any]:
    """
    Visualize dependencies in a project.
    """
    try:
        # Analyze dependencies
        dependency_graph = dependency_analyzer.analyze_project(project_path)
        
        # Visualize graph
        visualization_data = graph_visualizer.visualize_graph(
            dependency_graph,
            format=format,
            layout=layout,
            include_node_types=include_node_types,
            include_edge_types=include_edge_types,
            group_by=group_by,
            max_nodes=max_nodes
        )
        
        # Return result
        return visualization_data
    except Exception as e:
        logger.error(f"Error visualizing dependencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/impact")
async def analyze_impact(
    project_path: str = Body(..., description="Path to the project directory"),
    changed_files: List[str] = Body(..., description="List of files that have been changed")
) -> Dict[str, Any]:
    """
    Analyze the impact of changes to files.
    """
    try:
        # Analyze dependencies
        dependency_graph = dependency_analyzer.analyze_project(project_path)
        
        # Analyze impact
        impact_analysis = impact_analyzer.analyze_impact(
            dependency_graph,
            changed_files,
            project_path
        )
        
        # Return result
        return impact_analysis
    except Exception as e:
        logger.error(f"Error analyzing impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/build-order")
async def optimize_build_order(
    project_path: str = Body(..., description="Path to the project directory"),
    changed_files: Optional[List[str]] = Body(None, description="List of files that have been changed")
) -> Dict[str, Any]:
    """
    Optimize the build order based on dependencies.
    """
    try:
        # Analyze dependencies
        dependency_graph = dependency_analyzer.analyze_project(project_path)
        
        # Optimize build order
        build_order = build_optimizer.optimize_build_order(
            dependency_graph,
            changed_files
        )
        
        # Return result
        return build_order
    except Exception as e:
        logger.error(f"Error optimizing build order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parallel-execution")
async def optimize_parallel_execution(
    project_path: str = Body(..., description="Path to the project directory"),
    max_parallel_jobs: int = Body(4, description="Maximum number of parallel jobs to run")
) -> Dict[str, Any]:
    """
    Optimize parallel execution of build jobs.
    """
    try:
        # Analyze dependencies
        dependency_graph = dependency_analyzer.analyze_project(project_path)
        
        # Optimize parallel execution
        parallel_execution = build_optimizer.optimize_parallel_execution(
            dependency_graph,
            max_parallel_jobs
        )
        
        # Return result
        return parallel_execution
    except Exception as e:
        logger.error(f"Error optimizing parallel execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parallel-opportunities")
async def identify_parallel_build_opportunities(
    project_path: str = Body(..., description="Path to the project directory")
) -> Dict[str, Any]:
    """
    Identify opportunities for parallel builds.
    """
    try:
        # Analyze dependencies
        dependency_graph = dependency_analyzer.analyze_project(project_path)
        
        # Identify parallel build opportunities
        parallel_opportunities = build_optimizer.identify_parallel_build_opportunities(
            dependency_graph
        )
        
        # Return result
        return parallel_opportunities
    except Exception as e:
        logger.error(f"Error identifying parallel build opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_dependency_graph(
    project_path: str = Body(..., description="Path to the project directory"),
    format: str = Body("json", description="Output format (json, dot, png, svg)"),
    output_path: str = Body(..., description="Path to output file")
) -> Dict[str, Any]:
    """
    Export a dependency graph to a file.
    """
    try:
        # Analyze dependencies
        dependency_graph = dependency_analyzer.analyze_project(project_path)
        
        # Export graph
        success = graph_visualizer.export_graph(
            dependency_graph,
            format,
            output_path
        )
        
        # Return result
        return {
            "success": success,
            "output_path": output_path
        }
    except Exception as e:
        logger.error(f"Error exporting dependency graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))
