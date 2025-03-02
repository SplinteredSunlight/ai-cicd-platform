"""
Build Optimizer service for dependency analysis.
This module provides build optimization capabilities.
"""

import os
import logging
from typing import Dict, List, Set, Any, Optional, Tuple, Union
from pathlib import Path
import heapq
import copy

from ..models.dependency_graph import DependencyGraph

logger = logging.getLogger(__name__)

class BuildOptimizerService:
    """
    Service for optimizing build order and parallel execution.
    """
    
    def __init__(self):
        """Initialize the build optimizer service."""
        pass
    
    def optimize_build_order(self, dependency_graph: DependencyGraph,
                            changed_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Optimize the build order based on dependencies.
        
        Args:
            dependency_graph: Dependency graph of the project
            changed_files: Optional list of files that have been changed
            
        Returns:
            Dictionary containing build order optimization results
        """
        # Initialize result
        result = {
            "build_order": [],
            "critical_path": [],
            "metrics": {
                "total_nodes": 0,
                "critical_path_length": 0,
                "max_depth": 0
            }
        }
        
        # Get all nodes and edges
        all_nodes = dependency_graph.get_all_nodes()
        
        # Filter nodes if changed files are provided
        if changed_files and len(changed_files) > 0:
            # Find affected nodes
            affected_nodes = self._find_affected_nodes(dependency_graph, changed_files)
            
            # Filter nodes
            filtered_nodes = {node_id: node_attrs for node_id, node_attrs in all_nodes.items() if node_id in affected_nodes}
        else:
            # Use all nodes
            filtered_nodes = all_nodes
        
        # Update metrics
        result["metrics"]["total_nodes"] = len(filtered_nodes)
        
        # Perform topological sort
        build_order = self._topological_sort(dependency_graph, filtered_nodes)
        
        # Find critical path
        critical_path = self._find_critical_path(dependency_graph, filtered_nodes)
        
        # Calculate max depth
        max_depth = self._calculate_max_depth(dependency_graph, filtered_nodes)
        
        # Update result
        result["build_order"] = build_order
        result["critical_path"] = critical_path
        result["metrics"]["critical_path_length"] = len(critical_path)
        result["metrics"]["max_depth"] = max_depth
        
        return result
    
    def optimize_parallel_execution(self, dependency_graph: DependencyGraph,
                                   max_parallel_jobs: int = 4) -> Dict[str, Any]:
        """
        Optimize parallel execution of build jobs.
        
        Args:
            dependency_graph: Dependency graph of the project
            max_parallel_jobs: Maximum number of parallel jobs to run
            
        Returns:
            Dictionary containing parallel execution optimization results
        """
        # Initialize result
        result = {
            "parallel_groups": [],
            "execution_plan": [],
            "metrics": {
                "total_nodes": 0,
                "total_groups": 0,
                "estimated_time": 0
            }
        }
        
        # Get all nodes and edges
        all_nodes = dependency_graph.get_all_nodes()
        
        # Update metrics
        result["metrics"]["total_nodes"] = len(all_nodes)
        
        # Perform level-based parallelization
        parallel_groups = self._level_based_parallelization(dependency_graph, all_nodes)
        
        # Create execution plan
        execution_plan = self._create_execution_plan(parallel_groups, max_parallel_jobs)
        
        # Estimate execution time
        estimated_time = self._estimate_execution_time(execution_plan)
        
        # Update result
        result["parallel_groups"] = parallel_groups
        result["execution_plan"] = execution_plan
        result["metrics"]["total_groups"] = len(parallel_groups)
        result["metrics"]["estimated_time"] = estimated_time
        
        return result
    
    def _find_affected_nodes(self, dependency_graph: DependencyGraph, changed_files: List[str]) -> Set[str]:
        """
        Find nodes affected by changes to files.
        
        Args:
            dependency_graph: Dependency graph
            changed_files: List of files that have been changed
            
        Returns:
            Set of affected node IDs
        """
        # Initialize result
        affected_nodes = set()
        
        # Get all nodes
        all_nodes = dependency_graph.get_all_nodes()
        
        # Map file paths to node IDs
        file_node_ids = {}
        for node_id, node_attrs in all_nodes.items():
            if node_attrs.get("type") == "file":
                path = node_attrs.get("path")
                if path:
                    file_node_ids[path] = node_id
        
        # Find directly affected nodes
        directly_affected_nodes = set()
        for file_path in changed_files:
            # Find node ID for this file
            node_id = file_node_ids.get(file_path)
            if node_id:
                directly_affected_nodes.add(node_id)
        
        # Find all dependencies of affected nodes
        for node_id in directly_affected_nodes:
            # Add the node itself
            affected_nodes.add(node_id)
            
            # Find all dependencies
            dependencies = self._find_all_dependencies(dependency_graph, node_id)
            affected_nodes.update(dependencies)
        
        return affected_nodes
    
    def _find_all_dependencies(self, dependency_graph: DependencyGraph, node_id: str) -> Set[str]:
        """
        Find all nodes that a given node depends on.
        
        Args:
            dependency_graph: Dependency graph
            node_id: ID of the node
            
        Returns:
            Set of node IDs that the given node depends on
        """
        # Initialize result
        dependencies = set()
        
        # Find direct dependencies
        direct_dependencies = dependency_graph.get_dependencies(node_id)
        
        # Add direct dependencies
        dependencies.update(direct_dependencies)
        
        # Find indirect dependencies
        for dependency_id in direct_dependencies:
            indirect_dependencies = self._find_all_dependencies(dependency_graph, dependency_id)
            dependencies.update(indirect_dependencies)
        
        return dependencies
    
    def _topological_sort(self, dependency_graph: DependencyGraph, nodes: Dict[str, Any]) -> List[str]:
        """
        Perform topological sort on the dependency graph.
        
        Args:
            dependency_graph: Dependency graph
            nodes: Dictionary of nodes to sort
            
        Returns:
            List of node IDs in topological order
        """
        # Initialize result
        result = []
        
        # Create a copy of the graph
        graph = {}
        for node_id in nodes:
            # Get dependencies
            dependencies = dependency_graph.get_dependencies(node_id)
            
            # Filter dependencies to only include nodes in the input set
            filtered_dependencies = [dep_id for dep_id in dependencies if dep_id in nodes]
            
            # Add to graph
            graph[node_id] = filtered_dependencies
        
        # Calculate in-degree for each node
        in_degree = {node_id: 0 for node_id in graph}
        for node_id, dependencies in graph.items():
            for dep_id in dependencies:
                in_degree[dep_id] += 1
        
        # Initialize queue with nodes that have no dependencies
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        
        # Process queue
        while queue:
            # Get next node
            node_id = queue.pop(0)
            
            # Add to result
            result.append(node_id)
            
            # Update in-degree of dependencies
            for dep_id in graph.get(node_id, []):
                in_degree[dep_id] -= 1
                
                # If in-degree is 0, add to queue
                if in_degree[dep_id] == 0:
                    queue.append(dep_id)
        
        # Check for cycles
        if len(result) != len(nodes):
            logger.warning("Dependency graph contains cycles")
        
        return result
    
    def _find_critical_path(self, dependency_graph: DependencyGraph, nodes: Dict[str, Any]) -> List[str]:
        """
        Find the critical path in the dependency graph.
        
        Args:
            dependency_graph: Dependency graph
            nodes: Dictionary of nodes to analyze
            
        Returns:
            List of node IDs in the critical path
        """
        # Initialize result
        result = []
        
        # Create a copy of the graph
        graph = {}
        for node_id in nodes:
            # Get dependencies
            dependencies = dependency_graph.get_dependencies(node_id)
            
            # Filter dependencies to only include nodes in the input set
            filtered_dependencies = [dep_id for dep_id in dependencies if dep_id in nodes]
            
            # Add to graph
            graph[node_id] = filtered_dependencies
        
        # Calculate longest path for each node
        longest_path = {node_id: 0 for node_id in graph}
        predecessor = {node_id: None for node_id in graph}
        
        # Perform topological sort
        topo_order = self._topological_sort(dependency_graph, nodes)
        
        # Calculate longest path
        for node_id in topo_order:
            # Get dependencies
            dependencies = graph.get(node_id, [])
            
            # Update longest path
            for dep_id in dependencies:
                if longest_path[dep_id] < longest_path[node_id] + 1:
                    longest_path[dep_id] = longest_path[node_id] + 1
                    predecessor[dep_id] = node_id
        
        # Find node with longest path
        end_node = max(longest_path.items(), key=lambda x: x[1])[0]
        
        # Build critical path
        current = end_node
        while current is not None:
            result.append(current)
            current = predecessor[current]
        
        # Reverse path
        result.reverse()
        
        return result
    
    def _calculate_max_depth(self, dependency_graph: DependencyGraph, nodes: Dict[str, Any]) -> int:
        """
        Calculate the maximum depth of the dependency graph.
        
        Args:
            dependency_graph: Dependency graph
            nodes: Dictionary of nodes to analyze
            
        Returns:
            Maximum depth of the dependency graph
        """
        # Create a copy of the graph
        graph = {}
        for node_id in nodes:
            # Get dependencies
            dependencies = dependency_graph.get_dependencies(node_id)
            
            # Filter dependencies to only include nodes in the input set
            filtered_dependencies = [dep_id for dep_id in dependencies if dep_id in nodes]
            
            # Add to graph
            graph[node_id] = filtered_dependencies
        
        # Calculate depth for each node
        depth = {}
        
        def get_depth(node_id):
            # If depth is already calculated, return it
            if node_id in depth:
                return depth[node_id]
            
            # If node has no dependencies, depth is 0
            dependencies = graph.get(node_id, [])
            if not dependencies:
                depth[node_id] = 0
                return 0
            
            # Calculate depth as 1 + max depth of dependencies
            max_dep_depth = max(get_depth(dep_id) for dep_id in dependencies)
            depth[node_id] = 1 + max_dep_depth
            
            return depth[node_id]
        
        # Calculate depth for all nodes
        for node_id in graph:
            get_depth(node_id)
        
        # Return maximum depth
        return max(depth.values()) if depth else 0
    
    def _level_based_parallelization(self, dependency_graph: DependencyGraph, nodes: Dict[str, Any]) -> List[List[str]]:
        """
        Perform level-based parallelization.
        
        Args:
            dependency_graph: Dependency graph
            nodes: Dictionary of nodes to analyze
            
        Returns:
            List of lists of node IDs, where each inner list represents a level
        """
        # Initialize result
        result = []
        
        # Create a copy of the graph
        graph = {}
        reverse_graph = {}
        for node_id in nodes:
            # Get dependencies
            dependencies = dependency_graph.get_dependencies(node_id)
            
            # Filter dependencies to only include nodes in the input set
            filtered_dependencies = [dep_id for dep_id in dependencies if dep_id in nodes]
            
            # Add to graph
            graph[node_id] = filtered_dependencies
            
            # Add to reverse graph
            for dep_id in filtered_dependencies:
                if dep_id not in reverse_graph:
                    reverse_graph[dep_id] = []
                
                reverse_graph[dep_id].append(node_id)
        
        # Calculate in-degree for each node
        in_degree = {node_id: 0 for node_id in graph}
        for node_id, dependencies in graph.items():
            for dep_id in dependencies:
                in_degree[dep_id] += 1
        
        # Initialize queue with nodes that have no dependencies
        current_level = [node_id for node_id, degree in in_degree.items() if degree == 0]
        
        # Process levels
        while current_level:
            # Add current level to result
            result.append(current_level)
            
            # Find next level
            next_level = []
            for node_id in current_level:
                # Get dependents
                dependents = reverse_graph.get(node_id, [])
                
                for dependent_id in dependents:
                    # Decrease in-degree
                    in_degree[dependent_id] -= 1
                    
                    # If in-degree is 0, add to next level
                    if in_degree[dependent_id] == 0:
                        next_level.append(dependent_id)
            
            # Update current level
            current_level = next_level
        
        return result
    
    def _create_execution_plan(self, parallel_groups: List[List[str]], max_parallel_jobs: int) -> List[List[str]]:
        """
        Create an execution plan from parallel groups.
        
        Args:
            parallel_groups: List of lists of node IDs, where each inner list represents a level
            max_parallel_jobs: Maximum number of parallel jobs to run
            
        Returns:
            List of lists of node IDs, where each inner list represents a batch of jobs to run in parallel
        """
        # Initialize result
        result = []
        
        # Process each level
        for level in parallel_groups:
            # Split level into batches
            batches = []
            for i in range(0, len(level), max_parallel_jobs):
                batch = level[i:i + max_parallel_jobs]
                batches.append(batch)
            
            # Add batches to result
            result.extend(batches)
        
        return result
    
    def _estimate_execution_time(self, execution_plan: List[List[str]]) -> int:
        """
        Estimate the execution time of an execution plan.
        
        Args:
            execution_plan: List of lists of node IDs, where each inner list represents a batch of jobs to run in parallel
            
        Returns:
            Estimated execution time in arbitrary units
        """
        # Assume each batch takes 1 time unit
        return len(execution_plan)
    
    def identify_parallel_build_opportunities(self, dependency_graph: DependencyGraph) -> Dict[str, Any]:
        """
        Identify opportunities for parallel builds.
        
        Args:
            dependency_graph: Dependency graph of the project
            
        Returns:
            Dictionary containing parallel build opportunities
        """
        # Initialize result
        result = {
            "independent_components": [],
            "parallel_paths": [],
            "metrics": {
                "total_independent_components": 0,
                "total_parallel_paths": 0,
                "parallelization_potential": 0.0
            }
        }
        
        # Get all nodes and edges
        all_nodes = dependency_graph.get_all_nodes()
        
        # Find connected components
        components = self._find_connected_components(dependency_graph, all_nodes)
        
        # Find independent components
        independent_components = []
        for component in components:
            if len(component) > 1:
                independent_components.append(component)
        
        # Find parallel paths
        parallel_paths = self._find_parallel_paths(dependency_graph, all_nodes)
        
        # Calculate parallelization potential
        parallelization_potential = 0.0
        if len(all_nodes) > 0:
            # Calculate as ratio of nodes that can be parallelized
            parallelizable_nodes = sum(len(component) for component in independent_components)
            parallelizable_nodes += sum(len(path) for path in parallel_paths)
            
            parallelization_potential = min(1.0, parallelizable_nodes / len(all_nodes))
        
        # Update result
        result["independent_components"] = independent_components
        result["parallel_paths"] = parallel_paths
        result["metrics"]["total_independent_components"] = len(independent_components)
        result["metrics"]["total_parallel_paths"] = len(parallel_paths)
        result["metrics"]["parallelization_potential"] = parallelization_potential
        
        return result
    
    def _find_connected_components(self, dependency_graph: DependencyGraph, nodes: Dict[str, Any]) -> List[List[str]]:
        """
        Find connected components in the dependency graph.
        
        Args:
            dependency_graph: Dependency graph
            nodes: Dictionary of nodes to analyze
            
        Returns:
            List of lists of node IDs, where each inner list represents a connected component
        """
        # Initialize result
        result = []
        
        # Create an undirected graph
        undirected_graph = {}
        for node_id in nodes:
            # Get dependencies
            dependencies = dependency_graph.get_dependencies(node_id)
            
            # Get dependents
            dependents = dependency_graph.get_dependents(node_id)
            
            # Combine dependencies and dependents
            neighbors = set(dependencies).union(dependents)
            
            # Filter neighbors to only include nodes in the input set
            filtered_neighbors = [neighbor_id for neighbor_id in neighbors if neighbor_id in nodes]
            
            # Add to graph
            undirected_graph[node_id] = filtered_neighbors
        
        # Find connected components
        visited = set()
        
        def dfs(node_id, component):
            # Mark node as visited
            visited.add(node_id)
            
            # Add node to component
            component.append(node_id)
            
            # Visit neighbors
            for neighbor_id in undirected_graph.get(node_id, []):
                if neighbor_id not in visited:
                    dfs(neighbor_id, component)
        
        # Process all nodes
        for node_id in undirected_graph:
            if node_id not in visited:
                component = []
                dfs(node_id, component)
                result.append(component)
        
        return result
    
    def _find_parallel_paths(self, dependency_graph: DependencyGraph, nodes: Dict[str, Any]) -> List[List[str]]:
        """
        Find parallel paths in the dependency graph.
        
        Args:
            dependency_graph: Dependency graph
            nodes: Dictionary of nodes to analyze
            
        Returns:
            List of lists of node IDs, where each inner list represents a parallel path
        """
        # Initialize result
        result = []
        
        # Create a copy of the graph
        graph = {}
        for node_id in nodes:
            # Get dependencies
            dependencies = dependency_graph.get_dependencies(node_id)
            
            # Filter dependencies to only include nodes in the input set
            filtered_dependencies = [dep_id for dep_id in dependencies if dep_id in nodes]
            
            # Add to graph
            graph[node_id] = filtered_dependencies
        
        # Find nodes with multiple dependencies
        for node_id, dependencies in graph.items():
            if len(dependencies) > 1:
                # Each dependency represents a potential parallel path
                for dep_id in dependencies:
                    # Find path from dep_id to a node with no dependencies
                    path = self._find_path_to_root(graph, dep_id)
                    
                    if path:
                        result.append(path)
        
        return result
    
    def _find_path_to_root(self, graph: Dict[str, List[str]], start_node: str) -> List[str]:
        """
        Find a path from a node to a root node (a node with no dependencies).
        
        Args:
            graph: Dependency graph
            start_node: ID of the starting node
            
        Returns:
            List of node IDs representing the path, or None if no path is found
        """
        # Initialize result
        path = [start_node]
        
        # Find path
        current = start_node
        while True:
            # Get dependencies
            dependencies = graph.get(current, [])
            
            # If no dependencies, we've reached a root node
            if not dependencies:
                break
            
            # Otherwise, follow the first dependency
            current = dependencies[0]
            
            # Check for cycles
            if current in path:
                return None
            
            # Add to path
            path.append(current)
        
        return path
