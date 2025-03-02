"""
Impact Analyzer service for dependency analysis.
This module provides impact analysis capabilities.
"""

import os
import logging
from typing import Dict, List, Set, Any, Optional, Tuple, Union
from pathlib import Path

from ..models.dependency_graph import DependencyGraph

logger = logging.getLogger(__name__)

class ImpactAnalyzerService:
    """
    Service for analyzing the impact of changes to files.
    """
    
    def __init__(self):
        """Initialize the impact analyzer service."""
        pass
    
    def analyze_impact(self, dependency_graph: DependencyGraph,
                      changed_files: List[str],
                      project_path: str) -> Dict[str, Any]:
        """
        Analyze the impact of changes to files.
        
        Args:
            dependency_graph: Dependency graph of the project
            changed_files: List of files that have been changed
            project_path: Path to the project directory
            
        Returns:
            Dictionary containing impact analysis results
        """
        # Initialize result
        result = {
            "affected_files": [],
            "affected_packages": [],
            "affected_components": [],
            "impact_graph": {},
            "metrics": {
                "total_affected_files": 0,
                "total_affected_packages": 0,
                "total_affected_components": 0,
                "direct_impacts": 0,
                "indirect_impacts": 0,
                "high_risk_impacts": 0
            }
        }
        
        # Normalize changed files
        normalized_changed_files = [self._normalize_path(f, project_path) for f in changed_files]
        
        # Get all nodes and edges
        all_nodes = dependency_graph.get_all_nodes()
        
        # Find affected files
        affected_files = set(normalized_changed_files)
        affected_packages = set()
        affected_components = set()
        
        # Map file paths to node IDs
        file_node_ids = {}
        for node_id, node_attrs in all_nodes.items():
            if node_attrs.get("type") == "file":
                path = node_attrs.get("path")
                if path:
                    file_node_ids[path] = node_id
        
        # Find directly affected nodes
        directly_affected_nodes = set()
        for file_path in normalized_changed_files:
            # Find node ID for this file
            node_id = file_node_ids.get(file_path)
            if node_id:
                directly_affected_nodes.add(node_id)
        
        # Find indirectly affected nodes
        indirectly_affected_nodes = set()
        for node_id in directly_affected_nodes:
            # Find dependents (nodes that depend on this node)
            dependents = self._find_all_dependents(dependency_graph, node_id)
            indirectly_affected_nodes.update(dependents)
        
        # Combine affected nodes
        all_affected_nodes = directly_affected_nodes.union(indirectly_affected_nodes)
        
        # Extract affected files, packages, and components
        for node_id in all_affected_nodes:
            node_attrs = all_nodes.get(node_id, {})
            node_type = node_attrs.get("type")
            
            if node_type == "file":
                path = node_attrs.get("path")
                if path and path not in affected_files:
                    affected_files.add(path)
            
            elif node_type == "package":
                name = node_attrs.get("name") or node_attrs.get("attributes", {}).get("name")
                if name:
                    affected_packages.add(name)
            
            elif node_type == "component":
                name = node_attrs.get("name") or node_attrs.get("attributes", {}).get("name")
                if name:
                    affected_components.add(name)
        
        # Build impact graph
        impact_graph = {
            "nodes": [],
            "edges": []
        }
        
        # Add nodes to impact graph
        for node_id in all_affected_nodes:
            node_attrs = all_nodes.get(node_id, {})
            
            # Skip if no attributes
            if not node_attrs:
                continue
            
            # Determine impact level
            impact_level = "direct" if node_id in directly_affected_nodes else "indirect"
            
            # Add node to impact graph
            impact_graph["nodes"].append({
                "id": node_id,
                "type": node_attrs.get("type", "unknown"),
                "impact_level": impact_level,
                "attributes": node_attrs
            })
        
        # Add edges to impact graph
        for source_id in all_affected_nodes:
            # Get dependencies
            dependencies = dependency_graph.get_dependencies(source_id)
            
            for target_id in dependencies:
                # Skip if target is not affected
                if target_id not in all_affected_nodes:
                    continue
                
                # Get edge attributes
                edge_attrs = dependency_graph.get_edge(source_id, target_id)
                
                # Add edge to impact graph
                impact_graph["edges"].append({
                    "source": source_id,
                    "target": target_id,
                    "type": edge_attrs.get("type", "unknown"),
                    "attributes": edge_attrs
                })
        
        # Update result
        result["affected_files"] = list(affected_files)
        result["affected_packages"] = list(affected_packages)
        result["affected_components"] = list(affected_components)
        result["impact_graph"] = impact_graph
        
        # Update metrics
        result["metrics"]["total_affected_files"] = len(affected_files)
        result["metrics"]["total_affected_packages"] = len(affected_packages)
        result["metrics"]["total_affected_components"] = len(affected_components)
        result["metrics"]["direct_impacts"] = len(directly_affected_nodes)
        result["metrics"]["indirect_impacts"] = len(indirectly_affected_nodes)
        
        # Calculate high-risk impacts
        high_risk_impacts = self._calculate_high_risk_impacts(dependency_graph, all_affected_nodes)
        result["metrics"]["high_risk_impacts"] = len(high_risk_impacts)
        
        # Add risk assessment
        result["risk_assessment"] = self._assess_risk(dependency_graph, all_affected_nodes, high_risk_impacts)
        
        # Add test coverage recommendations
        result["test_recommendations"] = self._recommend_tests(dependency_graph, all_affected_nodes)
        
        return result
    
    def _normalize_path(self, file_path: str, project_path: str) -> str:
        """
        Normalize a file path.
        
        Args:
            file_path: Path to normalize
            project_path: Path to the project directory
            
        Returns:
            Normalized path
        """
        # Convert to absolute path
        if not os.path.isabs(file_path):
            file_path = os.path.join(project_path, file_path)
        
        # Normalize path
        file_path = os.path.normpath(file_path)
        
        return file_path
    
    def _find_all_dependents(self, dependency_graph: DependencyGraph, node_id: str) -> Set[str]:
        """
        Find all nodes that depend on a given node.
        
        Args:
            dependency_graph: Dependency graph
            node_id: ID of the node
            
        Returns:
            Set of node IDs that depend on the given node
        """
        # Initialize result
        dependents = set()
        
        # Find direct dependents
        direct_dependents = dependency_graph.get_dependents(node_id)
        
        # Add direct dependents
        dependents.update(direct_dependents)
        
        # Find indirect dependents
        for dependent_id in direct_dependents:
            indirect_dependents = self._find_all_dependents(dependency_graph, dependent_id)
            dependents.update(indirect_dependents)
        
        return dependents
    
    def _calculate_high_risk_impacts(self, dependency_graph: DependencyGraph, affected_nodes: Set[str]) -> List[str]:
        """
        Calculate high-risk impacts.
        
        Args:
            dependency_graph: Dependency graph
            affected_nodes: Set of affected node IDs
            
        Returns:
            List of high-risk node IDs
        """
        # Initialize result
        high_risk_nodes = []
        
        # Get all nodes
        all_nodes = dependency_graph.get_all_nodes()
        
        # Calculate risk for each affected node
        for node_id in affected_nodes:
            node_attrs = all_nodes.get(node_id, {})
            
            # Skip if no attributes
            if not node_attrs:
                continue
            
            # Get dependents
            dependents = dependency_graph.get_dependents(node_id)
            
            # Calculate risk based on number of dependents
            if len(dependents) > 5:
                high_risk_nodes.append(node_id)
            
            # Calculate risk based on node type
            node_type = node_attrs.get("type")
            if node_type in ["package", "component"]:
                high_risk_nodes.append(node_id)
        
        return high_risk_nodes
    
    def _assess_risk(self, dependency_graph: DependencyGraph, affected_nodes: Set[str], high_risk_nodes: List[str]) -> Dict[str, Any]:
        """
        Assess the risk of changes.
        
        Args:
            dependency_graph: Dependency graph
            affected_nodes: Set of affected node IDs
            high_risk_nodes: List of high-risk node IDs
            
        Returns:
            Dictionary containing risk assessment
        """
        # Initialize result
        risk_assessment = {
            "overall_risk": "low",
            "risk_factors": [],
            "high_risk_nodes": []
        }
        
        # Get all nodes
        all_nodes = dependency_graph.get_all_nodes()
        
        # Calculate overall risk
        if len(high_risk_nodes) > 0:
            if len(high_risk_nodes) > 5:
                risk_assessment["overall_risk"] = "high"
            else:
                risk_assessment["overall_risk"] = "medium"
        
        # Add risk factors
        if len(affected_nodes) > 10:
            risk_assessment["risk_factors"].append({
                "factor": "large_impact_area",
                "description": "Changes affect a large number of files and components",
                "severity": "high"
            })
        
        if len(high_risk_nodes) > 0:
            risk_assessment["risk_factors"].append({
                "factor": "high_risk_components",
                "description": "Changes affect high-risk components with many dependents",
                "severity": "high"
            })
        
        # Add high-risk nodes
        for node_id in high_risk_nodes:
            node_attrs = all_nodes.get(node_id, {})
            
            # Skip if no attributes
            if not node_attrs:
                continue
            
            # Get node name
            node_name = node_attrs.get("name") or node_attrs.get("attributes", {}).get("name") or node_id
            
            # Add to high-risk nodes
            risk_assessment["high_risk_nodes"].append({
                "id": node_id,
                "name": node_name,
                "type": node_attrs.get("type", "unknown"),
                "dependents_count": len(dependency_graph.get_dependents(node_id))
            })
        
        return risk_assessment
    
    def _recommend_tests(self, dependency_graph: DependencyGraph, affected_nodes: Set[str]) -> Dict[str, Any]:
        """
        Recommend tests to run.
        
        Args:
            dependency_graph: Dependency graph
            affected_nodes: Set of affected node IDs
            
        Returns:
            Dictionary containing test recommendations
        """
        # Initialize result
        test_recommendations = {
            "recommended_tests": [],
            "test_coverage": {
                "unit_tests": [],
                "integration_tests": [],
                "end_to_end_tests": []
            }
        }
        
        # Get all nodes
        all_nodes = dependency_graph.get_all_nodes()
        
        # Find test files
        test_files = []
        for node_id, node_attrs in all_nodes.items():
            # Skip if not a file
            if node_attrs.get("type") != "file":
                continue
            
            # Get file path
            path = node_attrs.get("path")
            if not path:
                continue
            
            # Check if it's a test file
            if "test" in path.lower() or "spec" in path.lower():
                test_files.append((node_id, path))
        
        # Recommend tests for each affected node
        for node_id in affected_nodes:
            node_attrs = all_nodes.get(node_id, {})
            
            # Skip if no attributes
            if not node_attrs:
                continue
            
            # Skip if not a file
            if node_attrs.get("type") != "file":
                continue
            
            # Get file path
            path = node_attrs.get("path")
            if not path:
                continue
            
            # Find matching test files
            matching_tests = []
            for test_id, test_path in test_files:
                # Check if test file matches
                if os.path.basename(path).replace(".py", "") in test_path:
                    matching_tests.append(test_path)
            
            # Add to recommended tests
            if matching_tests:
                test_recommendations["recommended_tests"].append({
                    "file": path,
                    "tests": matching_tests
                })
                
                # Add to test coverage
                test_recommendations["test_coverage"]["unit_tests"].extend(matching_tests)
        
        # Remove duplicates
        test_recommendations["test_coverage"]["unit_tests"] = list(set(test_recommendations["test_coverage"]["unit_tests"]))
        
        return test_recommendations
