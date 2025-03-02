"""
Package Analyzer service for analyzing package dependencies.
This module provides functionality to analyze dependencies between packages.
"""

import os
import logging
import json
import subprocess
import re
from typing import Dict, List, Set, Any, Optional, Tuple, Union
from pathlib import Path

from ..models.dependency_graph import DependencyGraph, NodeMetadata, DependencyMetadata, NodeType, DependencyType

logger = logging.getLogger(__name__)

class PackageAnalyzerService:
    """
    Service for analyzing package dependencies.
    """
    
    def __init__(self):
        """Initialize the package analyzer service."""
        # Map of package manager to file patterns
        self.package_manager_patterns = {
            "pip": ["requirements.txt", "setup.py", "pyproject.toml"],
            "npm": ["package.json"],
            "yarn": ["package.json", "yarn.lock"],
            "maven": ["pom.xml"],
            "gradle": ["build.gradle", "build.gradle.kts"],
            "composer": ["composer.json"],
            "cargo": ["Cargo.toml"],
            "nuget": ["*.csproj", "packages.config"],
            "go": ["go.mod"],
            "bundler": ["Gemfile"],
        }
    
    def analyze_project_dependencies(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze package dependencies in a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary containing package dependencies
        """
        logger.info(f"Analyzing package dependencies: {project_path}")
        
        # Initialize result
        result = {
            "dependency_graphs": {},
            "package_managers": [],
            "direct_dependencies": {},
            "transitive_dependencies": {},
            "dev_dependencies": {}
        }
        
        # Detect package managers
        package_managers = self._detect_package_managers(project_path)
        result["package_managers"] = package_managers
        
        logger.info(f"Detected package managers: {package_managers}")
        
        # Analyze dependencies for each package manager
        for manager in package_managers:
            try:
                # Get analyzer method
                analyzer_method = getattr(self, f"_analyze_{manager}_dependencies", None)
                
                if analyzer_method:
                    # Analyze dependencies
                    manager_result = analyzer_method(project_path)
                    
                    # Add to result
                    if manager_result:
                        result["dependency_graphs"][manager] = manager_result.get("dependency_graph", {})
                        result["direct_dependencies"][manager] = manager_result.get("direct_dependencies", {})
                        result["transitive_dependencies"][manager] = manager_result.get("transitive_dependencies", {})
                        result["dev_dependencies"][manager] = manager_result.get("dev_dependencies", {})
            except Exception as e:
                logger.error(f"Error analyzing {manager} dependencies: {e}")
        
        logger.info(f"Package analysis complete: {len(result['dependency_graphs'])} dependency graphs")
        
        return result
    
    def _detect_package_managers(self, project_path: str) -> List[str]:
        """
        Detect package managers used in a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of package managers
        """
        # Initialize result
        package_managers = []
        
        # Check for each package manager
        for manager, patterns in self.package_manager_patterns.items():
            for pattern in patterns:
                # Find matching files
                matching_files = list(Path(project_path).glob(f"**/{pattern}"))
                
                # If any matching files found, add package manager
                if matching_files:
                    package_managers.append(manager)
                    break
        
        return package_managers
    
    def _analyze_pip_dependencies(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze pip dependencies.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary containing pip dependencies
        """
        # Initialize result
        result = {
            "dependency_graph": {
                "nodes": {},
                "edges": []
            },
            "direct_dependencies": {},
            "transitive_dependencies": {},
            "dev_dependencies": {}
        }
        
        # Find requirements files
        requirements_files = list(Path(project_path).glob("**/requirements*.txt"))
        setup_files = list(Path(project_path).glob("**/setup.py"))
        pyproject_files = list(Path(project_path).glob("**/pyproject.toml"))
        
        # Add project node
        result["dependency_graph"]["nodes"]["package:project"] = {
            "type": "package",
            "attributes": {
                "name": os.path.basename(project_path),
                "type": "project"
            }
        }
        
        # Process requirements files
        for req_file in requirements_files:
            try:
                # Read file
                with open(req_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Parse requirements
                dependencies = self._parse_requirements_txt(content)
                
                # Add to result
                for dep_name, dep_version in dependencies.items():
                    # Add node
                    node_id = f"package:{dep_name}"
                    result["dependency_graph"]["nodes"][node_id] = {
                        "type": "package",
                        "attributes": {
                            "name": dep_name,
                            "version": dep_version,
                            "type": "pip"
                        }
                    }
                    
                    # Add edge
                    result["dependency_graph"]["edges"].append({
                        "source": "package:project",
                        "target": node_id,
                        "metadata": {
                            "type": "package",
                            "is_direct": True,
                            "attributes": {
                                "version": dep_version,
                                "source": str(req_file)
                            }
                        }
                    })
                    
                    # Add to direct dependencies
                    result["direct_dependencies"][dep_name] = {
                        "version": dep_version,
                        "source": str(req_file)
                    }
            except Exception as e:
                logger.error(f"Error parsing requirements file {req_file}: {e}")
        
        # Try to use pipdeptree if available
        try:
            # Run pipdeptree
            process = subprocess.run(
                ["pipdeptree", "--json-tree"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False
            )
            
            if process.returncode == 0:
                # Parse output
                tree = json.loads(process.stdout)
                
                # Process tree
                for package in tree:
                    package_name = package.get("package", {}).get("key")
                    package_version = package.get("package", {}).get("installed_version")
                    
                    if package_name:
                        # Add node
                        node_id = f"package:{package_name}"
                        result["dependency_graph"]["nodes"][node_id] = {
                            "type": "package",
                            "attributes": {
                                "name": package_name,
                                "version": package_version,
                                "type": "pip"
                            }
                        }
                        
                        # Process dependencies
                        for dep in package.get("dependencies", []):
                            dep_name = dep.get("key")
                            dep_version = dep.get("installed_version")
                            
                            if dep_name:
                                # Add node
                                dep_node_id = f"package:{dep_name}"
                                result["dependency_graph"]["nodes"][dep_node_id] = {
                                    "type": "package",
                                    "attributes": {
                                        "name": dep_name,
                                        "version": dep_version,
                                        "type": "pip"
                                    }
                                }
                                
                                # Add edge
                                result["dependency_graph"]["edges"].append({
                                    "source": node_id,
                                    "target": dep_node_id,
                                    "metadata": {
                                        "type": "package",
                                        "is_direct": True,
                                        "attributes": {
                                            "version": dep_version
                                        }
                                    }
                                })
                                
                                # Add to transitive dependencies
                                result["transitive_dependencies"][dep_name] = {
                                    "version": dep_version,
                                    "parent": package_name
                                }
        except Exception as e:
            logger.error(f"Error running pipdeptree: {e}")
        
        return result
    
    def _parse_requirements_txt(self, content: str) -> Dict[str, str]:
        """
        Parse requirements.txt content.
        
        Args:
            content: Content of requirements.txt
            
        Returns:
            Dictionary mapping package names to versions
        """
        # Initialize result
        dependencies = {}
        
        # Parse lines
        for line in content.splitlines():
            # Skip comments and empty lines
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # Skip options
            if line.startswith("-"):
                continue
            
            # Parse package
            match = re.match(r"([^=<>~!]+)(?:[=<>~!]=?)?([^;]*)", line)
            if match:
                package_name = match.group(1).strip()
                package_version = match.group(2).strip()
                
                dependencies[package_name] = package_version
        
        return dependencies
    
    def _analyze_npm_dependencies(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze npm dependencies.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary containing npm dependencies
        """
        # Initialize result
        result = {
            "dependency_graph": {
                "nodes": {},
                "edges": []
            },
            "direct_dependencies": {},
            "transitive_dependencies": {},
            "dev_dependencies": {}
        }
        
        # Find package.json files
        package_files = list(Path(project_path).glob("**/package.json"))
        
        # Add project node
        result["dependency_graph"]["nodes"]["package:project"] = {
            "type": "package",
            "attributes": {
                "name": os.path.basename(project_path),
                "type": "project"
            }
        }
        
        # Process package.json files
        for pkg_file in package_files:
            try:
                # Read file
                with open(pkg_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Parse package.json
                package_json = json.loads(content)
                
                # Process dependencies
                dependencies = package_json.get("dependencies", {})
                for dep_name, dep_version in dependencies.items():
                    # Add node
                    node_id = f"package:{dep_name}"
                    result["dependency_graph"]["nodes"][node_id] = {
                        "type": "package",
                        "attributes": {
                            "name": dep_name,
                            "version": dep_version,
                            "type": "npm"
                        }
                    }
                    
                    # Add edge
                    result["dependency_graph"]["edges"].append({
                        "source": "package:project",
                        "target": node_id,
                        "metadata": {
                            "type": "package",
                            "is_direct": True,
                            "attributes": {
                                "version": dep_version,
                                "source": str(pkg_file)
                            }
                        }
                    })
                    
                    # Add to direct dependencies
                    result["direct_dependencies"][dep_name] = {
                        "version": dep_version,
                        "source": str(pkg_file)
                    }
                
                # Process dev dependencies
                dev_dependencies = package_json.get("devDependencies", {})
                for dep_name, dep_version in dev_dependencies.items():
                    # Add node
                    node_id = f"package:{dep_name}"
                    result["dependency_graph"]["nodes"][node_id] = {
                        "type": "package",
                        "attributes": {
                            "name": dep_name,
                            "version": dep_version,
                            "type": "npm",
                            "dev": True
                        }
                    }
                    
                    # Add edge
                    result["dependency_graph"]["edges"].append({
                        "source": "package:project",
                        "target": node_id,
                        "metadata": {
                            "type": "package",
                            "is_direct": True,
                            "attributes": {
                                "version": dep_version,
                                "source": str(pkg_file),
                                "dev": True
                            }
                        }
                    })
                    
                    # Add to dev dependencies
                    result["dev_dependencies"][dep_name] = {
                        "version": dep_version,
                        "source": str(pkg_file)
                    }
            except Exception as e:
                logger.error(f"Error parsing package.json file {pkg_file}: {e}")
        
        # Try to use npm list if available
        try:
            # Run npm list
            process = subprocess.run(
                ["npm", "list", "--json"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False
            )
            
            if process.returncode == 0:
                # Parse output
                npm_list = json.loads(process.stdout)
                
                # Process dependencies
                self._process_npm_dependencies(
                    npm_list.get("dependencies", {}),
                    "package:project",
                    result["dependency_graph"],
                    result["transitive_dependencies"]
                )
        except Exception as e:
            logger.error(f"Error running npm list: {e}")
        
        return result
    
    def _process_npm_dependencies(self, dependencies: Dict[str, Any],
                                parent_id: str,
                                dependency_graph: Dict[str, Any],
                                transitive_dependencies: Dict[str, Any]) -> None:
        """
        Process npm dependencies recursively.
        
        Args:
            dependencies: Dictionary of dependencies
            parent_id: ID of the parent node
            dependency_graph: Dependency graph to update
            transitive_dependencies: Transitive dependencies to update
        """
        for dep_name, dep_info in dependencies.items():
            # Get version
            dep_version = dep_info.get("version", "")
            
            # Add node
            node_id = f"package:{dep_name}"
            dependency_graph["nodes"][node_id] = {
                "type": "package",
                "attributes": {
                    "name": dep_name,
                    "version": dep_version,
                    "type": "npm"
                }
            }
            
            # Add edge
            dependency_graph["edges"].append({
                "source": parent_id,
                "target": node_id,
                "metadata": {
                    "type": "package",
                    "is_direct": parent_id == "package:project",
                    "attributes": {
                        "version": dep_version
                    }
                }
            })
            
            # Add to transitive dependencies if not direct
            if parent_id != "package:project":
                parent_name = parent_id.split(":")[-1]
                transitive_dependencies[dep_name] = {
                    "version": dep_version,
                    "parent": parent_name
                }
            
            # Process nested dependencies
            nested_deps = dep_info.get("dependencies", {})
            if nested_deps:
                self._process_npm_dependencies(
                    nested_deps,
                    node_id,
                    dependency_graph,
                    transitive_dependencies
                )
    
    def _analyze_maven_dependencies(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze Maven dependencies.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary containing Maven dependencies
        """
        # Initialize result
        result = {
            "dependency_graph": {
                "nodes": {},
                "edges": []
            },
            "direct_dependencies": {},
            "transitive_dependencies": {},
            "dev_dependencies": {}
        }
        
        # Find pom.xml files
        pom_files = list(Path(project_path).glob("**/pom.xml"))
        
        # Add project node
        result["dependency_graph"]["nodes"]["package:project"] = {
            "type": "package",
            "attributes": {
                "name": os.path.basename(project_path),
                "type": "project"
            }
        }
        
        # Process pom.xml files
        for pom_file in pom_files:
            try:
                # Read file
                with open(pom_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Parse dependencies using regex
                dependencies = self._parse_maven_dependencies(content)
                
                # Add to result
                for dep in dependencies:
                    group_id = dep.get("groupId", "")
                    artifact_id = dep.get("artifactId", "")
                    version = dep.get("version", "")
                    scope = dep.get("scope", "compile")
                    
                    # Create node ID
                    node_id = f"package:{group_id}:{artifact_id}"
                    
                    # Add node
                    result["dependency_graph"]["nodes"][node_id] = {
                        "type": "package",
                        "attributes": {
                            "name": f"{group_id}:{artifact_id}",
                            "groupId": group_id,
                            "artifactId": artifact_id,
                            "version": version,
                            "type": "maven",
                            "scope": scope
                        }
                    }
                    
                    # Add edge
                    result["dependency_graph"]["edges"].append({
                        "source": "package:project",
                        "target": node_id,
                        "metadata": {
                            "type": "package",
                            "is_direct": True,
                            "attributes": {
                                "version": version,
                                "source": str(pom_file),
                                "scope": scope
                            }
                        }
                    })
                    
                    # Add to direct dependencies
                    result["direct_dependencies"][f"{group_id}:{artifact_id}"] = {
                        "version": version,
                        "source": str(pom_file),
                        "scope": scope
                    }
                    
                    # Add to dev dependencies if scope is test
                    if scope == "test":
                        result["dev_dependencies"][f"{group_id}:{artifact_id}"] = {
                            "version": version,
                            "source": str(pom_file),
                            "scope": scope
                        }
            except Exception as e:
                logger.error(f"Error parsing pom.xml file {pom_file}: {e}")
        
        # Try to use mvn dependency:tree if available
        try:
            # Run mvn dependency:tree
            process = subprocess.run(
                ["mvn", "dependency:tree", "-DoutputType=dot"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False
            )
            
            if process.returncode == 0:
                # Parse output
                dot_output = process.stdout
                
                # Extract dependencies
                self._parse_maven_dependency_tree(dot_output, result)
        except Exception as e:
            logger.error(f"Error running mvn dependency:tree: {e}")
        
        return result
    
    def _parse_maven_dependencies(self, content: str) -> List[Dict[str, str]]:
        """
        Parse Maven dependencies from pom.xml content.
        
        Args:
            content: Content of pom.xml
            
        Returns:
            List of dependencies
        """
        # Initialize result
        dependencies = []
        
        # Find dependencies section
        dependencies_match = re.search(r"<dependencies>(.*?)</dependencies>", content, re.DOTALL)
        if dependencies_match:
            dependencies_content = dependencies_match.group(1)
            
            # Find individual dependencies
            dependency_matches = re.finditer(r"<dependency>(.*?)</dependency>", dependencies_content, re.DOTALL)
            for dep_match in dependency_matches:
                dep_content = dep_match.group(1)
                
                # Extract dependency info
                group_id_match = re.search(r"<groupId>(.*?)</groupId>", dep_content)
                artifact_id_match = re.search(r"<artifactId>(.*?)</artifactId>", dep_content)
                version_match = re.search(r"<version>(.*?)</version>", dep_content)
                scope_match = re.search(r"<scope>(.*?)</scope>", dep_content)
                
                # Create dependency object
                dependency = {}
                if group_id_match:
                    dependency["groupId"] = group_id_match.group(1).strip()
                if artifact_id_match:
                    dependency["artifactId"] = artifact_id_match.group(1).strip()
                if version_match:
                    dependency["version"] = version_match.group(1).strip()
                if scope_match:
                    dependency["scope"] = scope_match.group(1).strip()
                
                # Add to result
                if "groupId" in dependency and "artifactId" in dependency:
                    dependencies.append(dependency)
        
        return dependencies
    
    def _parse_maven_dependency_tree(self, dot_output: str, result: Dict[str, Any]) -> None:
        """
        Parse Maven dependency tree in DOT format.
        
        Args:
            dot_output: DOT output from mvn dependency:tree
            result: Result dictionary to update
        """
        # Find edges
        edge_pattern = r'"([^"]+)" -> "([^"]+)"'
        for match in re.finditer(edge_pattern, dot_output):
            source, target = match.groups()
            
            # Parse source and target
            source_parts = source.split(":")
            target_parts = target.split(":")
            
            if len(source_parts) >= 4 and len(target_parts) >= 4:
                source_group_id = source_parts[0]
                source_artifact_id = source_parts[1]
                source_version = source_parts[3]
                
                target_group_id = target_parts[0]
                target_artifact_id = target_parts[1]
                target_version = target_parts[3]
                
                # Create node IDs
                source_id = f"package:{source_group_id}:{source_artifact_id}"
                target_id = f"package:{target_group_id}:{target_artifact_id}"
                
                # Add nodes if not exists
                if source_id not in result["dependency_graph"]["nodes"]:
                    result["dependency_graph"]["nodes"][source_id] = {
                        "type": "package",
                        "attributes": {
                            "name": f"{source_group_id}:{source_artifact_id}",
                            "groupId": source_group_id,
                            "artifactId": source_artifact_id,
                            "version": source_version,
                            "type": "maven"
                        }
                    }
                
                if target_id not in result["dependency_graph"]["nodes"]:
                    result["dependency_graph"]["nodes"][target_id] = {
                        "type": "package",
                        "attributes": {
                            "name": f"{target_group_id}:{target_artifact_id}",
                            "groupId": target_group_id,
                            "artifactId": target_artifact_id,
                            "version": target_version,
                            "type": "maven"
                        }
                    }
                
                # Add edge
                result["dependency_graph"]["edges"].append({
                    "source": source_id,
                    "target": target_id,
                    "metadata": {
                        "type": "package",
                        "is_direct": source_id == "package:project",
                        "attributes": {
                            "version": target_version
                        }
                    }
                })
                
                # Add to transitive dependencies if not direct
                if source_id != "package:project":
                    result["transitive_dependencies"][f"{target_group_id}:{target_artifact_id}"] = {
                        "version": target_version,
                        "parent": f"{source_group_id}:{source_artifact_id}"
                    }
    
    def create_dependency_graph(self, package_dependencies: Dict[str, Any]) -> DependencyGraph:
        """
        Create a dependency graph from package dependencies.
        
        Args:
            package_dependencies: Package dependencies
            
        Returns:
            Dependency graph
        """
        # Create dependency graph
        graph = DependencyGraph()
        
        # Process dependency graphs
        for manager, manager_graph in package_dependencies.get("dependency_graphs", {}).items():
            # Process nodes
            for node_id, node_attrs in manager_graph.get("nodes", {}).items():
                graph.add_node(node_id, node_attrs)
            
            # Process edges
            for edge in manager_graph.get("edges", []):
                source_id = edge.get("source")
                target_id = edge.get("target")
                metadata = edge.get("metadata", {})
                
                if source_id and target_id:
                    graph.add_edge(source_id, target_id, metadata)
        
        return graph
