"""
Dependency Graph model for dependency analysis.
This module provides the data structures for representing dependency graphs.
"""

import json
from typing import Dict, List, Set, Any, Optional, Tuple, Union
from enum import Enum, auto

class NodeType(str, Enum):
    """
    Enum for node types.
    """
    FILE = "file"
    PACKAGE = "package"
    CLASS = "class"
    FUNCTION = "function"
    COMPONENT = "component"
    CUSTOM = "custom"

class DependencyType(str, Enum):
    """
    Enum for dependency types.
    """
    IMPORT = "import"
    FUNCTION_CALL = "function_call"
    INHERITANCE = "inheritance"
    PACKAGE = "package"
    CUSTOM = "custom"

class NodeMetadata:
    """
    Metadata for a node in the dependency graph.
    """
    
    def __init__(self, type: Union[NodeType, str] = NodeType.CUSTOM,
                language: Optional[str] = None,
                path: Optional[str] = None,
                attributes: Optional[Dict[str, Any]] = None):
        """
        Initialize node metadata.
        
        Args:
            type: Type of the node
            language: Programming language of the node
            path: Path to the file or directory
            attributes: Additional attributes
        """
        self.type = type
        self.language = language
        self.path = path
        self.attributes = attributes or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "type": self.type,
            "language": self.language,
            "path": self.path,
            "attributes": self.attributes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NodeMetadata':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            NodeMetadata instance
        """
        return cls(
            type=data.get("type", NodeType.CUSTOM),
            language=data.get("language"),
            path=data.get("path"),
            attributes=data.get("attributes", {})
        )

class DependencyMetadata:
    """
    Metadata for a dependency in the dependency graph.
    """
    
    def __init__(self, type: Union[DependencyType, str] = DependencyType.CUSTOM,
                is_direct: bool = True,
                attributes: Optional[Dict[str, Any]] = None):
        """
        Initialize dependency metadata.
        
        Args:
            type: Type of the dependency
            is_direct: Whether the dependency is direct
            attributes: Additional attributes
        """
        self.type = type
        self.is_direct = is_direct
        self.attributes = attributes or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "type": self.type,
            "is_direct": self.is_direct,
            "attributes": self.attributes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DependencyMetadata':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            DependencyMetadata instance
        """
        return cls(
            type=data.get("type", DependencyType.CUSTOM),
            is_direct=data.get("is_direct", True),
            attributes=data.get("attributes", {})
        )

class DependencyGraph:
    """
    Dependency graph for representing dependencies between nodes.
    """
    
    def __init__(self):
        """Initialize dependency graph."""
        # Map of node ID to node metadata
        self.nodes: Dict[str, Dict[str, Any]] = {}
        
        # Map of source node ID to map of target node ID to edge metadata
        self.edges: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        # Map of target node ID to set of source node IDs
        self.reverse_edges: Dict[str, Set[str]] = {}
    
    def add_node(self, node_id: str, metadata: Union[NodeMetadata, Dict[str, Any]]) -> None:
        """
        Add a node to the graph.
        
        Args:
            node_id: ID of the node
            metadata: Metadata for the node
        """
        # Convert metadata to dictionary if needed
        if isinstance(metadata, NodeMetadata):
            metadata = metadata.to_dict()
        
        # Add node
        self.nodes[node_id] = metadata
        
        # Initialize edges
        if node_id not in self.edges:
            self.edges[node_id] = {}
        
        # Initialize reverse edges
        if node_id not in self.reverse_edges:
            self.reverse_edges[node_id] = set()
    
    def add_edge(self, source_id: str, target_id: str, metadata: Union[DependencyMetadata, Dict[str, Any]]) -> None:
        """
        Add an edge to the graph.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            metadata: Metadata for the edge
        """
        # Add nodes if they don't exist
        if source_id not in self.nodes:
            self.add_node(source_id, NodeMetadata())
        
        if target_id not in self.nodes:
            self.add_node(target_id, NodeMetadata())
        
        # Convert metadata to dictionary if needed
        if isinstance(metadata, DependencyMetadata):
            metadata = metadata.to_dict()
        
        # Add edge
        self.edges[source_id][target_id] = metadata
        
        # Add reverse edge
        self.reverse_edges[target_id].add(source_id)
    
    def remove_node(self, node_id: str) -> None:
        """
        Remove a node from the graph.
        
        Args:
            node_id: ID of the node to remove
        """
        # Remove node
        if node_id in self.nodes:
            del self.nodes[node_id]
        
        # Remove outgoing edges
        if node_id in self.edges:
            # Remove reverse edges
            for target_id in self.edges[node_id]:
                if target_id in self.reverse_edges:
                    self.reverse_edges[target_id].discard(node_id)
            
            # Remove edges
            del self.edges[node_id]
        
        # Remove incoming edges
        if node_id in self.reverse_edges:
            # Remove edges
            for source_id in self.reverse_edges[node_id]:
                if source_id in self.edges and node_id in self.edges[source_id]:
                    del self.edges[source_id][node_id]
            
            # Remove reverse edges
            del self.reverse_edges[node_id]
    
    def remove_edge(self, source_id: str, target_id: str) -> None:
        """
        Remove an edge from the graph.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
        """
        # Remove edge
        if source_id in self.edges and target_id in self.edges[source_id]:
            del self.edges[source_id][target_id]
        
        # Remove reverse edge
        if target_id in self.reverse_edges:
            self.reverse_edges[target_id].discard(source_id)
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node from the graph.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Node metadata, or None if not found
        """
        return self.nodes.get(node_id)
    
    def get_edge(self, source_id: str, target_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an edge from the graph.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            
        Returns:
            Edge metadata, or None if not found
        """
        if source_id in self.edges and target_id in self.edges[source_id]:
            return self.edges[source_id][target_id]
        
        return None
    
    def get_dependencies(self, node_id: str) -> List[str]:
        """
        Get dependencies of a node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            List of node IDs that the given node depends on
        """
        if node_id in self.edges:
            return list(self.edges[node_id].keys())
        
        return []
    
    def get_dependents(self, node_id: str) -> List[str]:
        """
        Get dependents of a node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            List of node IDs that depend on the given node
        """
        if node_id in self.reverse_edges:
            return list(self.reverse_edges[node_id])
        
        return []
    
    def get_all_nodes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all nodes in the graph.
        
        Returns:
            Dictionary mapping node IDs to node metadata
        """
        return self.nodes
    
    def get_all_edges(self) -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Get all edges in the graph.
        
        Returns:
            List of tuples (source_id, target_id, metadata)
        """
        edges = []
        
        for source_id, targets in self.edges.items():
            for target_id, metadata in targets.items():
                edges.append((source_id, target_id, metadata))
        
        return edges
    
    def find_cycles(self) -> List[List[str]]:
        """
        Find cycles in the graph.
        
        Returns:
            List of cycles, where each cycle is a list of node IDs
        """
        # Initialize result
        cycles = []
        
        # Initialize visited set
        visited = set()
        
        # Initialize recursion stack
        rec_stack = set()
        
        # DFS function
        def dfs(node_id, path):
            # Mark node as visited
            visited.add(node_id)
            
            # Add to recursion stack
            rec_stack.add(node_id)
            
            # Add to path
            path.append(node_id)
            
            # Visit dependencies
            for dep_id in self.get_dependencies(node_id):
                # If not visited, visit
                if dep_id not in visited:
                    if dfs(dep_id, path):
                        return True
                
                # If in recursion stack, we found a cycle
                elif dep_id in rec_stack:
                    # Find start of cycle
                    start_idx = path.index(dep_id)
                    
                    # Extract cycle
                    cycle = path[start_idx:]
                    
                    # Add to result
                    cycles.append(cycle)
                    
                    return True
            
            # Remove from recursion stack
            rec_stack.remove(node_id)
            
            # Remove from path
            path.pop()
            
            return False
        
        # Visit all nodes
        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id, [])
        
        return cycles
    
    def find_critical_path(self) -> List[str]:
        """
        Find the critical path in the graph.
        
        Returns:
            List of node IDs in the critical path
        """
        # Initialize result
        result = []
        
        # Calculate longest path for each node
        longest_path = {node_id: 0 for node_id in self.nodes}
        predecessor = {node_id: None for node_id in self.nodes}
        
        # Perform topological sort
        topo_order = self._topological_sort()
        
        # Calculate longest path
        for node_id in topo_order:
            # Get dependencies
            dependencies = self.get_dependencies(node_id)
            
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
    
    def _topological_sort(self) -> List[str]:
        """
        Perform topological sort on the graph.
        
        Returns:
            List of node IDs in topological order
        """
        # Initialize result
        result = []
        
        # Calculate in-degree for each node
        in_degree = {node_id: 0 for node_id in self.nodes}
        for node_id in self.nodes:
            for dep_id in self.get_dependencies(node_id):
                in_degree[dep_id] += 1
        
        # Initialize queue with nodes that have no dependencies
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        
        # Process queue
        while queue:
            # Get next node
            node_id = queue.pop(0)
            
            # Add to result
            result.append(node_id)
            
            # Update in-degree of dependents
            for dep_id in self.get_dependents(node_id):
                in_degree[dep_id] -= 1
                
                # If in-degree is 0, add to queue
                if in_degree[dep_id] == 0:
                    queue.append(dep_id)
        
        # Check for cycles
        if len(result) != len(self.nodes):
            # If there are cycles, add remaining nodes
            for node_id in self.nodes:
                if node_id not in result:
                    result.append(node_id)
        
        return result
    
    def merge(self, other: 'DependencyGraph') -> None:
        """
        Merge another dependency graph into this one.
        
        Args:
            other: Dependency graph to merge
        """
        # Merge nodes
        for node_id, metadata in other.nodes.items():
            self.add_node(node_id, metadata)
        
        # Merge edges
        for source_id, target_id, metadata in other.get_all_edges():
            self.add_edge(source_id, target_id, metadata)
    
    def to_json(self) -> str:
        """
        Convert to JSON string.
        
        Returns:
            JSON string representation
        """
        data = {
            "nodes": self.nodes,
            "edges": []
        }
        
        # Add edges
        for source_id, target_id, metadata in self.get_all_edges():
            data["edges"].append({
                "source": source_id,
                "target": target_id,
                "metadata": metadata
            })
        
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DependencyGraph':
        """
        Create from JSON string.
        
        Args:
            json_str: JSON string representation
            
        Returns:
            DependencyGraph instance
        """
        data = json.loads(json_str)
        
        # Create graph
        graph = cls()
        
        # Add nodes
        for node_id, metadata in data.get("nodes", {}).items():
            graph.add_node(node_id, metadata)
        
        # Add edges
        for edge in data.get("edges", []):
            source_id = edge.get("source")
            target_id = edge.get("target")
            metadata = edge.get("metadata", {})
            
            if source_id and target_id:
                graph.add_edge(source_id, target_id, metadata)
        
        return graph
