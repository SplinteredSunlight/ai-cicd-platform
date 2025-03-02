"""
Dependency Analyzer service for analyzing project dependencies.
This module provides functionality to analyze dependencies between files, classes, functions, and packages.
"""

import os
import logging
import json
from typing import Dict, List, Set, Any, Optional, Tuple, Union
import networkx as nx
from pathlib import Path

from ..models.dependency_graph import DependencyGraph, NodeMetadata, DependencyMetadata, NodeType, DependencyType

logger = logging.getLogger(__name__)

class DependencyAnalyzerService:
    """
    Service for analyzing project dependencies.
    """
    
    def __init__(self):
        """Initialize the dependency analyzer service."""
        # Map of file extensions to languages
        self.extension_to_language = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".rs": "rust",
        }
    
    def analyze_project(self, project_path: str,
                       languages: Optional[List[str]] = None,
                       include_patterns: Optional[List[str]] = None,
                       exclude_patterns: Optional[List[str]] = None,
                       analyze_imports: bool = True,
                       analyze_function_calls: bool = True,
                       analyze_class_hierarchy: bool = True,
                       analyze_packages: bool = True,
                       max_depth: Optional[int] = None) -> DependencyGraph:
        """
        Analyze dependencies in a project.
        
        Args:
            project_path: Path to the project directory
            languages: List of languages to analyze
            include_patterns: List of glob patterns to include
            exclude_patterns: List of glob patterns to exclude
            analyze_imports: Whether to analyze imports
            analyze_function_calls: Whether to analyze function calls
            analyze_class_hierarchy: Whether to analyze class hierarchy
            analyze_packages: Whether to analyze package dependencies
            max_depth: Maximum depth to analyze
            
        Returns:
            Dependency graph
        """
        logger.info(f"Analyzing project dependencies: {project_path}")
        
        # Import services here to avoid circular imports
        from .code_analyzer import CodeAnalyzerService
        from .package_analyzer import PackageAnalyzerService
        
        # Create services
        code_analyzer = CodeAnalyzerService()
        package_analyzer = PackageAnalyzerService()
        
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
        
        # Analyze package dependencies
        package_dependencies = {}
        if analyze_packages:
            package_dependencies = package_analyzer.analyze_project_dependencies(project_path)
        
        # Create dependency graph
        dependency_graph = self.create_dependency_graph(code_dependencies, package_dependencies)
        
        logger.info(f"Dependency analysis complete: {len(dependency_graph.get_all_nodes())} nodes, {len(dependency_graph.get_all_edges())} edges")
        
        return dependency_graph
    
    def create_dependency_graph(self, code_dependencies: Dict[str, Any],
                              package_dependencies: Dict[str, Any]) -> DependencyGraph:
        """
        Create a dependency graph from code and package dependencies.
        
        Args:
            code_dependencies: Code dependencies
            package_dependencies: Package dependencies
            
        Returns:
            Dependency graph
        """
        # Create dependency graph
        graph = DependencyGraph()
        
        # Process imports
        if "imports" in code_dependencies:
            self._process_imports(graph, code_dependencies["imports"])
        
        # Process function calls
        if "function_calls" in code_dependencies:
            self._process_function_calls(graph, code_dependencies["function_calls"])
        
        # Process class hierarchy
        if "class_hierarchy" in code_dependencies:
            self._process_class_hierarchy(graph, code_dependencies["class_hierarchy"])
        
        # Process package dependencies
        if "dependency_graphs" in package_dependencies:
            self._process_package_dependencies(graph, package_dependencies["dependency_graphs"])
        
        return graph
    
    def _process_imports(self, graph: DependencyGraph, imports: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Process imports and add to the dependency graph.
        
        Args:
            graph: Dependency graph
            imports: Dictionary mapping file paths to lists of imports
        """
        for file_path, file_imports in imports.items():
            # Add file node
            file_node_id = f"file:{file_path}"
            language = self._get_language_from_file(file_path)
            graph.add_node(file_node_id, NodeMetadata(
                type=NodeType.FILE,
                language=language,
                path=file_path
            ))
            
            # Process imports
            for import_info in file_imports:
                import_name = import_info.get("name")
                import_file = import_info.get("file")
                
                if import_file:
                    # Add imported file node
                    import_node_id = f"file:{import_file}"
                    import_language = self._get_language_from_file(import_file)
                    graph.add_node(import_node_id, NodeMetadata(
                        type=NodeType.FILE,
                        language=import_language,
                        path=import_file
                    ))
                    
                    # Add edge
                    graph.add_edge(file_node_id, import_node_id, DependencyMetadata(
                        type=DependencyType.IMPORT,
                        is_direct=True,
                        attributes={"name": import_name}
                    ))
    
    def _process_function_calls(self, graph: DependencyGraph, function_calls: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Process function calls and add to the dependency graph.
        
        Args:
            graph: Dependency graph
            function_calls: Dictionary mapping file paths to lists of function calls
        """
        for file_path, calls in function_calls.items():
            # Add file node if not exists
            file_node_id = f"file:{file_path}"
            if not graph.get_node(file_node_id):
                language = self._get_language_from_file(file_path)
                graph.add_node(file_node_id, NodeMetadata(
                    type=NodeType.FILE,
                    language=language,
                    path=file_path
                ))
            
            # Process function calls
            for call_info in calls:
                function_name = call_info.get("name")
                function_file = call_info.get("file")
                
                if function_file:
                    # Add function file node if not exists
                    function_file_node_id = f"file:{function_file}"
                    if not graph.get_node(function_file_node_id):
                        function_language = self._get_language_from_file(function_file)
                        graph.add_node(function_file_node_id, NodeMetadata(
                            type=NodeType.FILE,
                            language=function_language,
                            path=function_file
                        ))
                    
                    # Add function node
                    function_node_id = f"function:{function_name}:{function_file}"
                    graph.add_node(function_node_id, NodeMetadata(
                        type=NodeType.FUNCTION,
                        language=self._get_language_from_file(function_file),
                        path=function_file,
                        attributes={"name": function_name}
                    ))
                    
                    # Add edge from file to function
                    graph.add_edge(file_node_id, function_node_id, DependencyMetadata(
                        type=DependencyType.FUNCTION_CALL,
                        is_direct=True
                    ))
                    
                    # Add edge from function to file
                    graph.add_edge(function_node_id, function_file_node_id, DependencyMetadata(
                        type=DependencyType.CUSTOM,
                        is_direct=True,
                        attributes={"relationship": "defined_in"}
                    ))
    
    def _process_class_hierarchy(self, graph: DependencyGraph, class_hierarchy: Dict[str, Dict[str, Any]]) -> None:
        """
        Process class hierarchy and add to the dependency graph.
        
        Args:
            graph: Dependency graph
            class_hierarchy: Dictionary mapping class names to class information
        """
        for class_name, class_info in class_hierarchy.items():
            class_file = class_info.get("file")
            parents = class_info.get("parents", [])
            
            if class_file:
                # Add file node if not exists
                file_node_id = f"file:{class_file}"
                if not graph.get_node(file_node_id):
                    language = self._get_language_from_file(class_file)
                    graph.add_node(file_node_id, NodeMetadata(
                        type=NodeType.FILE,
                        language=language,
                        path=class_file
                    ))
                
                # Add class node
                class_node_id = f"class:{class_name}:{class_file}"
                graph.add_node(class_node_id, NodeMetadata(
                    type=NodeType.CLASS,
                    language=self._get_language_from_file(class_file),
                    path=class_file,
                    attributes={"name": class_name}
                ))
                
                # Add edge from class to file
                graph.add_edge(class_node_id, file_node_id, DependencyMetadata(
                    type=DependencyType.CUSTOM,
                    is_direct=True,
                    attributes={"relationship": "defined_in"}
                ))
                
                # Process parent classes
                for parent_name in parents:
                    parent_info = class_hierarchy.get(parent_name)
                    
                    if parent_info:
                        parent_file = parent_info.get("file")
                        
                        if parent_file:
                            # Add parent class node
                            parent_node_id = f"class:{parent_name}:{parent_file}"
                            graph.add_node(parent_node_id, NodeMetadata(
                                type=NodeType.CLASS,
                                language=self._get_language_from_file(parent_file),
                                path=parent_file,
                                attributes={"name": parent_name}
                            ))
                            
                            # Add inheritance edge
                            graph.add_edge(class_node_id, parent_node_id, DependencyMetadata(
                                type=DependencyType.INHERITANCE,
                                is_direct=True
                            ))
    
    def _process_package_dependencies(self, graph: DependencyGraph, dependency_graphs: Dict[str, Dict[str, Any]]) -> None:
        """
        Process package dependencies and add to the dependency graph.
        
        Args:
            graph: Dependency graph
            dependency_graphs: Dictionary mapping package manager names to dependency graphs
        """
        for manager_name, manager_graph in dependency_graphs.items():
            # Process nodes
            if "nodes" in manager_graph:
                for node_id, node_attrs in manager_graph["nodes"].items():
                    graph.add_node(node_id, node_attrs)
            
            # Process edges
            if "edges" in manager_graph:
                for edge in manager_graph["edges"]:
                    source_id = edge.get("source")
                    target_id = edge.get("target")
                    metadata = edge.get("metadata", {})
                    
                    if source_id and target_id:
                        graph.add_edge(source_id, target_id, metadata)
    
    def calculate_metrics(self, graph: DependencyGraph) -> Dict[str, Any]:
        """
        Calculate metrics for a dependency graph.
        
        Args:
            graph: Dependency graph
            
        Returns:
            Dictionary of metrics
        """
        # Get all nodes and edges
        nodes = graph.get_all_nodes()
        edges = graph.get_all_edges()
        
        # Calculate node type counts
        node_types = {}
        for node_id, node_attrs in nodes.items():
            node_type = node_attrs.get("type")
            if node_type:
                node_types[node_type] = node_types.get(node_type, 0) + 1
        
        # Calculate edge type counts
        edge_types = {}
        for source_id, target_id, edge_attrs in edges:
            edge_type = edge_attrs.get("type")
            if edge_type:
                edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        # Calculate connectivity metrics
        in_degree = {}
        out_degree = {}
        for node_id in nodes:
            in_degree[node_id] = len(graph.get_dependents(node_id))
            out_degree[node_id] = len(graph.get_dependencies(node_id))
        
        # Find highly connected nodes
        highly_connected_nodes = []
        for node_id in nodes:
            in_deg = in_degree.get(node_id, 0)
            out_deg = out_degree.get(node_id, 0)
            total_deg = in_deg + out_deg
            
            if total_deg > 5:  # Arbitrary threshold
                highly_connected_nodes.append({
                    "node_id": node_id,
                    "in_degree": in_deg,
                    "out_degree": out_deg,
                    "total_degree": total_deg
                })
        
        # Sort by total degree
        highly_connected_nodes.sort(key=lambda x: x["total_degree"], reverse=True)
        
        # Calculate average degree
        total_nodes = len(nodes)
        total_edges = len(edges)
        avg_degree = total_edges * 2 / total_nodes if total_nodes > 0 else 0
        
        # Calculate max degrees
        max_in_degree = max(in_degree.values()) if in_degree else 0
        max_out_degree = max(out_degree.values()) if out_degree else 0
        
        # Find cycles
        cycles = graph.find_cycles()
        
        # Calculate cyclomatic complexity
        cyclomatic_complexity = total_edges - total_nodes + 2 if total_nodes > 0 else 0
        
        # Calculate dependency depth
        dependency_depth = 0
        for node_id in nodes:
            depth = self._calculate_node_depth(graph, node_id)
            dependency_depth = max(dependency_depth, depth)
        
        # Return metrics
        return {
            "node_count": total_nodes,
            "edge_count": total_edges,
            "node_types": node_types,
            "edge_types": edge_types,
            "connectivity": {
                "average_degree": avg_degree,
                "max_in_degree": max_in_degree,
                "max_out_degree": max_out_degree,
                "highly_connected_nodes": highly_connected_nodes[:10]  # Limit to top 10
            },
            "complexity": {
                "cyclomatic_complexity": cyclomatic_complexity,
                "dependency_depth": dependency_depth,
                "dependency_cycles": cycles
            }
        }
    
    def _calculate_node_depth(self, graph: DependencyGraph, node_id: str) -> int:
        """
        Calculate the depth of a node in the dependency graph.
        
        Args:
            graph: Dependency graph
            node_id: ID of the node
            
        Returns:
            Depth of the node
        """
        # Get dependencies
        dependencies = graph.get_dependencies(node_id)
        
        # If no dependencies, depth is 0
        if not dependencies:
            return 0
        
        # Otherwise, depth is 1 + max depth of dependencies
        max_depth = 0
        for dep_id in dependencies:
            depth = self._calculate_node_depth(graph, dep_id)
            max_depth = max(max_depth, depth)
        
        return 1 + max_depth
    
    def export_dependency_graph(self, graph: DependencyGraph, format: str = "json") -> str:
        """
        Export a dependency graph to a specific format.
        
        Args:
            graph: Dependency graph
            format: Export format (json, dot)
            
        Returns:
            String representation of the graph in the specified format
        """
        if format == "json":
            return graph.to_json()
        elif format == "dot":
            return self._export_to_dot(graph)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_to_dot(self, graph: DependencyGraph) -> str:
        """
        Export a dependency graph to DOT format.
        
        Args:
            graph: Dependency graph
            
        Returns:
            DOT representation of the graph
        """
        # Create NetworkX graph
        nx_graph = nx.DiGraph()
        
        # Add nodes
        for node_id, node_attrs in graph.get_all_nodes().items():
            node_type = node_attrs.get("type", "unknown")
            node_label = node_id.split(":")[-1] if ":" in node_id else node_id
            
            # Add node with attributes
            nx_graph.add_node(node_id, label=node_label, type=node_type)
        
        # Add edges
        for source_id, target_id, edge_attrs in graph.get_all_edges():
            edge_type = edge_attrs.get("type", "unknown")
            
            # Add edge with attributes
            nx_graph.add_edge(source_id, target_id, label=edge_type)
        
        # Convert to DOT format
        try:
            return nx.drawing.nx_pydot.to_pydot(nx_graph).to_string()
        except Exception as e:
            logger.error(f"Error exporting to DOT format: {e}")
            return ""
    
    def import_dependency_graph(self, data: str, format: str = "json") -> DependencyGraph:
        """
        Import a dependency graph from a specific format.
        
        Args:
            data: String representation of the graph
            format: Import format (json, dot)
            
        Returns:
            Dependency graph
        """
        if format == "json":
            return DependencyGraph.from_json(data)
        else:
            raise ValueError(f"Unsupported import format: {format}")
    
    def _get_language_from_file(self, file_path: Optional[str]) -> Optional[str]:
        """
        Get the programming language from a file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Programming language, or None if unknown
        """
        if not file_path:
            return None
        
        # Get file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        # Return language based on extension
        return self.extension_to_language.get(ext)
