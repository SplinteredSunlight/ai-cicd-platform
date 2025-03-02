"""
Graph Visualizer service for visualizing dependency graphs.
This module provides functionality to visualize dependency graphs in various formats.
"""

import os
import logging
import json
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List, Set, Any, Optional, Tuple, Union
from pathlib import Path

from ..models.dependency_graph import DependencyGraph, NodeType

logger = logging.getLogger(__name__)

class GraphVisualizerService:
    """
    Service for visualizing dependency graphs.
    """
    
    def __init__(self):
        """Initialize the graph visualizer service."""
        # Map of node types to colors
        self.node_type_colors = {
            NodeType.FILE: "#4CAF50",      # Green
            NodeType.PACKAGE: "#2196F3",   # Blue
            NodeType.CLASS: "#FFC107",     # Yellow
            NodeType.FUNCTION: "#F44336",  # Red
            NodeType.COMPONENT: "#9C27B0", # Purple
            NodeType.CUSTOM: "#607D8B",    # Gray
        }
        
        # Map of layout algorithms
        self.layout_algorithms = {
            "spring": nx.spring_layout,
            "circular": nx.circular_layout,
            "kamada_kawai": nx.kamada_kawai_layout,
            "shell": nx.shell_layout,
            "spectral": nx.spectral_layout,
            "random": nx.random_layout,
            "planar": nx.planar_layout,
            "spiral": nx.spiral_layout,
            "multipartite": nx.multipartite_layout
        }
    
    def visualize_graph(self, graph: DependencyGraph,
                       format: str = "json",
                       layout: str = "spring",
                       include_node_types: Optional[List[str]] = None,
                       include_edge_types: Optional[List[str]] = None,
                       group_by: Optional[str] = None,
                       max_nodes: int = 100) -> Dict[str, Any]:
        """
        Visualize a dependency graph.
        
        Args:
            graph: Dependency graph to visualize
            format: Output format (json, dot, png, svg)
            layout: Layout algorithm to use
            include_node_types: List of node types to include
            include_edge_types: List of edge types to include
            group_by: Attribute to group nodes by
            max_nodes: Maximum number of nodes to include
            
        Returns:
            Dictionary containing visualization data
        """
        logger.info(f"Visualizing graph: format={format}, layout={layout}, max_nodes={max_nodes}")
        
        # Filter graph
        filtered_graph = self._filter_graph(
            graph,
            include_node_types,
            include_edge_types,
            max_nodes
        )
        
        # Convert to NetworkX graph
        nx_graph = self._to_networkx(filtered_graph, group_by)
        
        # Apply layout
        positions = self._apply_layout(nx_graph, layout)
        
        # Generate visualization
        if format == "json":
            result = self._to_json(filtered_graph, nx_graph, positions)
        elif format == "dot":
            result = self._to_dot(filtered_graph, nx_graph)
        elif format in ["png", "svg"]:
            result = self._to_image(filtered_graph, nx_graph, positions, format)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Add stats
        result["stats"] = {
            "total_nodes": len(graph.get_all_nodes()),
            "total_edges": len(graph.get_all_edges()),
            "visible_nodes": len(filtered_graph.get_all_nodes()),
            "visible_edges": len(filtered_graph.get_all_edges())
        }
        
        return result
    
    def _filter_graph(self, graph: DependencyGraph,
                    include_node_types: Optional[List[str]],
                    include_edge_types: Optional[List[str]],
                    max_nodes: int) -> DependencyGraph:
        """
        Filter a dependency graph.
        
        Args:
            graph: Dependency graph to filter
            include_node_types: List of node types to include
            include_edge_types: List of edge types to include
            max_nodes: Maximum number of nodes to include
            
        Returns:
            Filtered dependency graph
        """
        # Create a new graph
        filtered_graph = DependencyGraph()
        
        # Get all nodes and edges
        all_nodes = graph.get_all_nodes()
        all_edges = graph.get_all_edges()
        
        # Filter nodes by type
        if include_node_types and "all" not in include_node_types:
            filtered_nodes = {
                node_id: node_attrs
                for node_id, node_attrs in all_nodes.items()
                if node_attrs.get("type") in include_node_types
            }
        else:
            filtered_nodes = all_nodes
        
        # Limit number of nodes
        if len(filtered_nodes) > max_nodes:
            # Sort nodes by number of connections
            node_connections = {}
            for node_id in filtered_nodes:
                dependencies = graph.get_dependencies(node_id)
                dependents = graph.get_dependents(node_id)
                node_connections[node_id] = len(dependencies) + len(dependents)
            
            # Sort by number of connections
            sorted_nodes = sorted(
                node_connections.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Take top nodes
            top_nodes = [node_id for node_id, _ in sorted_nodes[:max_nodes]]
            
            # Filter nodes
            filtered_nodes = {
                node_id: node_attrs
                for node_id, node_attrs in filtered_nodes.items()
                if node_id in top_nodes
            }
        
        # Add nodes to filtered graph
        for node_id, node_attrs in filtered_nodes.items():
            filtered_graph.add_node(node_id, node_attrs)
        
        # Filter edges
        for source_id, target_id, edge_attrs in all_edges:
            # Skip if source or target not in filtered nodes
            if source_id not in filtered_nodes or target_id not in filtered_nodes:
                continue
            
            # Filter by edge type
            if include_edge_types and "all" not in include_edge_types:
                if edge_attrs.get("type") not in include_edge_types:
                    continue
            
            # Add edge to filtered graph
            filtered_graph.add_edge(source_id, target_id, edge_attrs)
        
        return filtered_graph
    
    def _to_networkx(self, graph: DependencyGraph, group_by: Optional[str] = None) -> nx.DiGraph:
        """
        Convert a dependency graph to a NetworkX graph.
        
        Args:
            graph: Dependency graph to convert
            group_by: Attribute to group nodes by
            
        Returns:
            NetworkX graph
        """
        # Create a new NetworkX graph
        nx_graph = nx.DiGraph()
        
        # Get all nodes and edges
        all_nodes = graph.get_all_nodes()
        all_edges = graph.get_all_edges()
        
        # Add nodes
        for node_id, node_attrs in all_nodes.items():
            # Get node type
            node_type = node_attrs.get("type", NodeType.CUSTOM)
            
            # Get node color
            node_color = self.node_type_colors.get(node_type, self.node_type_colors[NodeType.CUSTOM])
            
            # Get node label
            node_label = node_id.split(":")[-1] if ":" in node_id else node_id
            
            # Get node group
            node_group = None
            if group_by:
                if group_by == "type":
                    node_group = node_type
                elif group_by in node_attrs:
                    node_group = node_attrs[group_by]
                elif "attributes" in node_attrs and group_by in node_attrs["attributes"]:
                    node_group = node_attrs["attributes"][group_by]
            
            # Add node
            nx_graph.add_node(
                node_id,
                label=node_label,
                type=node_type,
                color=node_color,
                group=node_group,
                **node_attrs
            )
        
        # Add edges
        for source_id, target_id, edge_attrs in all_edges:
            # Add edge
            nx_graph.add_edge(
                source_id,
                target_id,
                **edge_attrs
            )
        
        return nx_graph
    
    def _apply_layout(self, nx_graph: nx.DiGraph, layout: str) -> Dict[str, Tuple[float, float]]:
        """
        Apply a layout algorithm to a NetworkX graph.
        
        Args:
            nx_graph: NetworkX graph
            layout: Layout algorithm to use
            
        Returns:
            Dictionary mapping node IDs to positions
        """
        # Get layout algorithm
        layout_algorithm = self.layout_algorithms.get(layout, nx.spring_layout)
        
        # Apply layout
        if layout == "multipartite":
            # Group nodes by type
            node_types = nx.get_node_attributes(nx_graph, "type")
            
            # Create a mapping of node types to integers
            type_to_int = {
                node_type: i for i, node_type in enumerate(set(node_types.values()))
            }
            
            # Create a mapping of nodes to their layer
            node_layer = {
                node: type_to_int[node_type]
                for node, node_type in node_types.items()
            }
            
            # Apply layout
            positions = layout_algorithm(nx_graph, subset_key="group")
        else:
            # Apply layout
            positions = layout_algorithm(nx_graph)
        
        return positions
    
    def _to_json(self, graph: DependencyGraph, nx_graph: nx.DiGraph,
               positions: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:
        """
        Convert a graph to JSON format.
        
        Args:
            graph: Dependency graph
            nx_graph: NetworkX graph
            positions: Node positions
            
        Returns:
            Dictionary containing JSON visualization data
        """
        # Initialize result
        result = {
            "format": "json",
            "data": {
                "nodes": [],
                "links": []
            },
            "layout": "force"
        }
        
        # Get all nodes and edges
        all_nodes = graph.get_all_nodes()
        all_edges = graph.get_all_edges()
        
        # Add nodes
        for node_id, node_attrs in all_nodes.items():
            # Get node position
            pos = positions.get(node_id, (0, 0))
            
            # Get node type
            node_type = node_attrs.get("type", NodeType.CUSTOM)
            
            # Get node label
            node_label = node_id.split(":")[-1] if ":" in node_id else node_id
            
            # Add node
            result["data"]["nodes"].append({
                "id": node_id,
                "label": node_label,
                "type": node_type,
                "x": pos[0],
                "y": pos[1],
                "attributes": node_attrs.get("attributes", {})
            })
        
        # Add edges
        for source_id, target_id, edge_attrs in all_edges:
            # Add edge
            result["data"]["links"].append({
                "source": source_id,
                "target": target_id,
                "type": edge_attrs.get("type", "unknown"),
                "attributes": edge_attrs.get("attributes", {})
            })
        
        return result
    
    def _to_dot(self, graph: DependencyGraph, nx_graph: nx.DiGraph) -> Dict[str, Any]:
        """
        Convert a graph to DOT format.
        
        Args:
            graph: Dependency graph
            nx_graph: NetworkX graph
            
        Returns:
            Dictionary containing DOT visualization data
        """
        # Initialize result
        result = {
            "format": "dot",
            "data": "",
            "layout": "dot"
        }
        
        try:
            # Convert to DOT format
            dot_data = nx.drawing.nx_pydot.to_pydot(nx_graph).to_string()
            
            # Add to result
            result["data"] = dot_data
        except Exception as e:
            logger.error(f"Error converting to DOT format: {e}")
            result["data"] = "digraph G {}"
        
        return result
    
    def _to_image(self, graph: DependencyGraph, nx_graph: nx.DiGraph,
                positions: Dict[str, Tuple[float, float]], format: str) -> Dict[str, Any]:
        """
        Convert a graph to an image format.
        
        Args:
            graph: Dependency graph
            nx_graph: NetworkX graph
            positions: Node positions
            format: Image format (png, svg)
            
        Returns:
            Dictionary containing image visualization data
        """
        # Initialize result
        result = {
            "format": format,
            "data": "",
            "layout": "force"
        }
        
        try:
            # Create figure
            plt.figure(figsize=(12, 8))
            
            # Get node colors
            node_colors = [
                nx_graph.nodes[node]["color"]
                for node in nx_graph.nodes
            ]
            
            # Draw nodes
            nx.draw_networkx_nodes(
                nx_graph,
                positions,
                node_color=node_colors,
                alpha=0.8,
                node_size=500
            )
            
            # Draw edges
            nx.draw_networkx_edges(
                nx_graph,
                positions,
                alpha=0.5,
                arrows=True
            )
            
            # Draw labels
            nx.draw_networkx_labels(
                nx_graph,
                positions,
                font_size=10,
                font_family="sans-serif"
            )
            
            # Save figure to bytes
            import io
            buf = io.BytesIO()
            plt.savefig(buf, format=format, bbox_inches="tight")
            buf.seek(0)
            
            # Convert to base64
            import base64
            image_data = base64.b64encode(buf.read()).decode("utf-8")
            
            # Add to result
            result["data"] = f"data:image/{format};base64,{image_data}"
            
            # Close figure
            plt.close()
        except Exception as e:
            logger.error(f"Error converting to {format} format: {e}")
            result["data"] = ""
        
        return result
    
    def export_graph(self, graph: DependencyGraph, format: str, output_path: str) -> bool:
        """
        Export a graph to a file.
        
        Args:
            graph: Dependency graph to export
            format: Output format (json, dot, png, svg)
            output_path: Path to output file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Visualize graph
            result = self.visualize_graph(graph, format=format)
            
            # Get data
            data = result.get("data", "")
            
            # Write to file
            if format == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            elif format == "dot":
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(data)
            elif format in ["png", "svg"]:
                # Remove data URL prefix
                import base64
                prefix = f"data:image/{format};base64,"
                if data.startswith(prefix):
                    data = data[len(prefix):]
                
                # Decode base64
                image_data = base64.b64decode(data)
                
                # Write to file
                with open(output_path, "wb") as f:
                    f.write(image_data)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return True
        except Exception as e:
            logger.error(f"Error exporting graph: {e}")
            return False
    
    def create_visualization_data(self, graph: DependencyGraph,
                                include_node_types: Optional[List[str]] = None,
                                include_edge_types: Optional[List[str]] = None,
                                group_by: Optional[str] = None,
                                max_nodes: int = 100) -> Dict[str, Any]:
        """
        Create visualization data for a dependency graph.
        
        Args:
            graph: Dependency graph to visualize
            include_node_types: List of node types to include
            include_edge_types: List of edge types to include
            group_by: Attribute to group nodes by
            max_nodes: Maximum number of nodes to include
            
        Returns:
            Dictionary containing visualization data
        """
        # Filter graph
        filtered_graph = self._filter_graph(
            graph,
            include_node_types,
            include_edge_types,
            max_nodes
        )
        
        # Convert to NetworkX graph
        nx_graph = self._to_networkx(filtered_graph, group_by)
        
        # Apply layout
        positions = self._apply_layout(nx_graph, "spring")
        
        # Convert to JSON
        result = self._to_json(filtered_graph, nx_graph, positions)
        
        # Add stats
        result["stats"] = {
            "total_nodes": len(graph.get_all_nodes()),
            "total_edges": len(graph.get_all_edges()),
            "visible_nodes": len(filtered_graph.get_all_nodes()),
            "visible_edges": len(filtered_graph.get_all_edges())
        }
        
        # Add node type counts
        node_types = {}
        for node_id, node_attrs in filtered_graph.get_all_nodes().items():
            node_type = node_attrs.get("type", NodeType.CUSTOM)
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        result["stats"]["nodeTypes"] = node_types
        
        # Add edge type counts
        edge_types = {}
        for source_id, target_id, edge_attrs in filtered_graph.get_all_edges():
            edge_type = edge_attrs.get("type", "unknown")
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        result["stats"]["edgeTypes"] = edge_types
        
        return result
