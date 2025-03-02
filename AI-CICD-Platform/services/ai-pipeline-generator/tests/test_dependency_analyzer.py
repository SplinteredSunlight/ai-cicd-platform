"""
Tests for the dependency analyzer service.
"""

import os
import pytest
from unittest.mock import MagicMock, patch

from ..services.dependency_analyzer import DependencyAnalyzerService
from ..models.dependency_graph import DependencyGraph, NodeMetadata, DependencyMetadata, NodeType, DependencyType

class TestDependencyAnalyzerService:
    """Tests for the DependencyAnalyzerService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = DependencyAnalyzerService()
    
    def test_init(self):
        """Test initialization."""
        assert isinstance(self.service, DependencyAnalyzerService)
    
    def test_create_dependency_graph(self):
        """Test creating a dependency graph."""
        # Create mock data
        code_dependencies = {
            "imports": {
                "file1.py": [
                    {"name": "module1", "file": "module1.py"}
                ]
            },
            "function_calls": {
                "file1.py": [
                    {"name": "func1", "file": "module1.py"}
                ]
            },
            "class_hierarchy": {
                "Class1": {
                    "file": "file1.py",
                    "parents": ["BaseClass"]
                }
            }
        }
        
        package_dependencies = {
            "dependency_graphs": {
                "pip": {
                    "nodes": {
                        "package:pkg1": {
                            "type": "package",
                            "attributes": {"name": "pkg1"}
                        }
                    },
                    "edges": [
                        {
                            "source": "package:project",
                            "target": "package:pkg1",
                            "metadata": {
                                "type": "package",
                                "is_direct": True
                            }
                        }
                    ]
                }
            }
        }
        
        # Call the method
        graph = self.service.create_dependency_graph(code_dependencies, package_dependencies)
        
        # Check the result
        assert isinstance(graph, DependencyGraph)
        assert len(graph.get_all_nodes()) > 0
        assert len(graph.get_all_edges()) > 0
    
    @patch('services.ai-pipeline-generator.services.code_analyzer.CodeAnalyzerService')
    @patch('services.ai-pipeline-generator.services.package_analyzer.PackageAnalyzerService')
    def test_analyze_project(self, mock_package_analyzer, mock_code_analyzer):
        """Test analyzing a project."""
        # Create mock data
        project_path = "/path/to/project"
        languages = ["python"]
        include_patterns = ["**/*.py"]
        exclude_patterns = ["**/test_*.py"]
        
        # Configure mocks
        mock_code_analyzer_instance = MagicMock()
        mock_code_analyzer.return_value = mock_code_analyzer_instance
        mock_code_analyzer_instance.analyze_code_dependencies.return_value = {
            "imports": {},
            "function_calls": {},
            "class_hierarchy": {}
        }
        
        mock_package_analyzer_instance = MagicMock()
        mock_package_analyzer.return_value = mock_package_analyzer_instance
        mock_package_analyzer_instance.analyze_project_dependencies.return_value = {
            "dependency_graphs": {}
        }
        
        # Call the method
        with patch.object(self.service, 'create_dependency_graph') as mock_create_graph:
            mock_create_graph.return_value = DependencyGraph()
            graph = self.service.analyze_project(
                project_path,
                languages=languages,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns
            )
        
        # Check the result
        assert isinstance(graph, DependencyGraph)
        mock_code_analyzer_instance.analyze_code_dependencies.assert_called_once_with(
            project_path,
            languages=languages,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns
        )
        mock_package_analyzer_instance.analyze_project_dependencies.assert_called_once_with(
            project_path
        )
    
    def test_calculate_metrics(self):
        """Test calculating metrics."""
        # Create a test graph
        graph = DependencyGraph()
        
        # Add nodes
        graph.add_node("file:file1.py", NodeMetadata(type=NodeType.FILE, path="file1.py"))
        graph.add_node("file:file2.py", NodeMetadata(type=NodeType.FILE, path="file2.py"))
        graph.add_node("class:Class1", NodeMetadata(type=NodeType.CLASS, path="file1.py"))
        graph.add_node("package:pkg1", NodeMetadata(type=NodeType.PACKAGE))
        
        # Add edges
        graph.add_edge("file:file1.py", "file:file2.py", DependencyMetadata(type=DependencyType.IMPORT))
        graph.add_edge("file:file1.py", "class:Class1", DependencyMetadata(type=DependencyType.CUSTOM))
        graph.add_edge("class:Class1", "package:pkg1", DependencyMetadata(type=DependencyType.PACKAGE))
        
        # Call the method
        metrics = self.service.calculate_metrics(graph)
        
        # Check the result
        assert isinstance(metrics, dict)
        assert metrics["node_count"] == 4
        assert metrics["edge_count"] == 3
        assert "node_types" in metrics
        assert "edge_types" in metrics
        assert "connectivity" in metrics
        assert "complexity" in metrics
    
    def test_export_dependency_graph(self):
        """Test exporting a dependency graph."""
        # Create a test graph
        graph = DependencyGraph()
        
        # Add nodes
        graph.add_node("file:file1.py", NodeMetadata(type=NodeType.FILE, path="file1.py"))
        graph.add_node("file:file2.py", NodeMetadata(type=NodeType.FILE, path="file2.py"))
        
        # Add edges
        graph.add_edge("file:file1.py", "file:file2.py", DependencyMetadata(type=DependencyType.IMPORT))
        
        # Call the method with JSON format
        json_result = self.service.export_dependency_graph(graph, format="json")
        
        # Check the result
        assert isinstance(json_result, str)
        assert "nodes" in json_result
        assert "edges" in json_result
        
        # Call the method with DOT format
        dot_result = self.service.export_dependency_graph(graph, format="dot")
        
        # Check the result
        assert isinstance(dot_result, str)
        assert "digraph" in dot_result
        assert "file:file1.py" in dot_result
        assert "file:file2.py" in dot_result
        
        # Test with unsupported format
        with pytest.raises(ValueError):
            self.service.export_dependency_graph(graph, format="unsupported")
    
    def test_import_dependency_graph(self):
        """Test importing a dependency graph."""
        # Create a test graph
        graph = DependencyGraph()
        
        # Add nodes
        graph.add_node("file:file1.py", NodeMetadata(type=NodeType.FILE, path="file1.py"))
        graph.add_node("file:file2.py", NodeMetadata(type=NodeType.FILE, path="file2.py"))
        
        # Add edges
        graph.add_edge("file:file1.py", "file:file2.py", DependencyMetadata(type=DependencyType.IMPORT))
        
        # Export to JSON
        json_data = graph.to_json()
        
        # Call the method
        imported_graph = self.service.import_dependency_graph(json_data, format="json")
        
        # Check the result
        assert isinstance(imported_graph, DependencyGraph)
        assert len(imported_graph.get_all_nodes()) == 2
        assert len(imported_graph.get_all_edges()) == 1
        
        # Test with unsupported format
        with pytest.raises(ValueError):
            self.service.import_dependency_graph("{}", format="unsupported")
    
    def test_get_language_from_file(self):
        """Test getting language from file."""
        # Test with Python file
        assert self.service._get_language_from_file("file.py") == "python"
        
        # Test with JavaScript file
        assert self.service._get_language_from_file("file.js") == "javascript"
        
        # Test with TypeScript file
        assert self.service._get_language_from_file("file.ts") == "typescript"
        
        # Test with unknown extension
        assert self.service._get_language_from_file("file.xyz") is None
        
        # Test with no extension
        assert self.service._get_language_from_file("file") is None
        
        # Test with empty string
        assert self.service._get_language_from_file("") is None
        
        # Test with None
        assert self.service._get_language_from_file(None) is None
