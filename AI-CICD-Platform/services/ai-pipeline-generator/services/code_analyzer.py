"""
Code Analyzer service for analyzing code dependencies.
This module provides functionality to analyze dependencies between files, classes, and functions.
"""

import os
import logging
import ast
import re
import glob
from typing import Dict, List, Set, Any, Optional, Tuple, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class CodeAnalyzerService:
    """
    Service for analyzing code dependencies.
    """
    
    def __init__(self):
        """Initialize the code analyzer service."""
        # Map of language to file extensions
        self.language_to_extensions = {
            "python": [".py"],
            "javascript": [".js", ".jsx"],
            "typescript": [".ts", ".tsx"],
            "java": [".java"],
            "c": [".c", ".h"],
            "cpp": [".cpp", ".hpp"],
            "csharp": [".cs"],
            "go": [".go"],
            "ruby": [".rb"],
            "php": [".php"],
            "swift": [".swift"],
            "kotlin": [".kt"],
            "rust": [".rs"],
        }
        
        # Map of language to analyzers
        self.language_analyzers = {
            "python": self._analyze_python_file,
            "javascript": self._analyze_javascript_file,
            "typescript": self._analyze_typescript_file,
        }
    
    def analyze_code_dependencies(self, project_path: str,
                                languages: Optional[List[str]] = None,
                                include_patterns: Optional[List[str]] = None,
                                exclude_patterns: Optional[List[str]] = None,
                                analyze_imports: bool = True,
                                analyze_function_calls: bool = True,
                                analyze_class_hierarchy: bool = True,
                                max_depth: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze code dependencies in a project.
        
        Args:
            project_path: Path to the project directory
            languages: List of languages to analyze
            include_patterns: List of glob patterns to include
            exclude_patterns: List of glob patterns to exclude
            analyze_imports: Whether to analyze imports
            analyze_function_calls: Whether to analyze function calls
            analyze_class_hierarchy: Whether to analyze class hierarchy
            max_depth: Maximum depth to analyze
            
        Returns:
            Dictionary containing code dependencies
        """
        logger.info(f"Analyzing code dependencies: {project_path}")
        
        # Initialize result
        result = {
            "imports": {},
            "function_calls": {},
            "class_hierarchy": {}
        }
        
        # Get file extensions to analyze
        extensions = self._get_extensions_for_languages(languages)
        
        # Find files to analyze
        files = self._find_files_to_analyze(
            project_path,
            extensions,
            include_patterns,
            exclude_patterns,
            max_depth
        )
        
        logger.info(f"Found {len(files)} files to analyze")
        
        # Analyze each file
        for file_path in files:
            try:
                # Get relative path
                rel_path = os.path.relpath(file_path, project_path)
                
                # Get language
                language = self._get_language_from_file(file_path)
                
                if language and language in self.language_analyzers:
                    # Analyze file
                    file_result = self.language_analyzers[language](
                        file_path,
                        analyze_imports,
                        analyze_function_calls,
                        analyze_class_hierarchy
                    )
                    
                    # Add to result
                    if analyze_imports and file_result.get("imports"):
                        result["imports"][rel_path] = file_result["imports"]
                    
                    if analyze_function_calls and file_result.get("function_calls"):
                        result["function_calls"][rel_path] = file_result["function_calls"]
                    
                    if analyze_class_hierarchy and file_result.get("classes"):
                        # Add classes to class hierarchy
                        for class_info in file_result["classes"]:
                            class_name = class_info["name"]
                            result["class_hierarchy"][class_name] = {
                                "file": rel_path,
                                "parents": class_info.get("parents", [])
                            }
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {e}")
        
        logger.info(f"Code analysis complete: {len(result['imports'])} files with imports, "
                   f"{len(result['function_calls'])} files with function calls, "
                   f"{len(result['class_hierarchy'])} classes")
        
        return result
    
    def _get_extensions_for_languages(self, languages: Optional[List[str]]) -> List[str]:
        """
        Get file extensions for the specified languages.
        
        Args:
            languages: List of languages
            
        Returns:
            List of file extensions
        """
        if not languages:
            # If no languages specified, use all supported languages
            extensions = []
            for exts in self.language_to_extensions.values():
                extensions.extend(exts)
            return extensions
        
        # Get extensions for specified languages
        extensions = []
        for language in languages:
            if language in self.language_to_extensions:
                extensions.extend(self.language_to_extensions[language])
        
        return extensions
    
    def _find_files_to_analyze(self, project_path: str,
                             extensions: List[str],
                             include_patterns: Optional[List[str]],
                             exclude_patterns: Optional[List[str]],
                             max_depth: Optional[int]) -> List[str]:
        """
        Find files to analyze in a project.
        
        Args:
            project_path: Path to the project directory
            extensions: List of file extensions to include
            include_patterns: List of glob patterns to include
            exclude_patterns: List of glob patterns to exclude
            max_depth: Maximum depth to analyze
            
        Returns:
            List of file paths
        """
        # Initialize result
        files = []
        
        # Create glob patterns for extensions
        if not include_patterns:
            include_patterns = [f"**/*{ext}" for ext in extensions]
        
        # Find files matching include patterns
        for pattern in include_patterns:
            # Create absolute pattern
            abs_pattern = os.path.join(project_path, pattern)
            
            # Find matching files
            matching_files = glob.glob(abs_pattern, recursive=True)
            
            # Add to result
            files.extend(matching_files)
        
        # Filter by extension if include patterns were provided
        if include_patterns:
            files = [f for f in files if any(f.endswith(ext) for ext in extensions)]
        
        # Filter by exclude patterns
        if exclude_patterns:
            for pattern in exclude_patterns:
                # Create absolute pattern
                abs_pattern = os.path.join(project_path, pattern)
                
                # Find matching files
                matching_files = glob.glob(abs_pattern, recursive=True)
                
                # Remove from result
                files = [f for f in files if f not in matching_files]
        
        # Filter by depth
        if max_depth is not None:
            # Get project path as Path object
            project_path_obj = Path(project_path)
            
            # Filter files by depth
            files = [f for f in files if len(Path(f).relative_to(project_path_obj).parts) <= max_depth]
        
        return files
    
    def _get_language_from_file(self, file_path: str) -> Optional[str]:
        """
        Get the programming language from a file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Programming language, or None if unknown
        """
        # Get file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        # Find language for extension
        for language, extensions in self.language_to_extensions.items():
            if ext in extensions:
                return language
        
        return None
    
    def _analyze_python_file(self, file_path: str,
                           analyze_imports: bool,
                           analyze_function_calls: bool,
                           analyze_class_hierarchy: bool) -> Dict[str, Any]:
        """
        Analyze a Python file.
        
        Args:
            file_path: Path to the file
            analyze_imports: Whether to analyze imports
            analyze_function_calls: Whether to analyze function calls
            analyze_class_hierarchy: Whether to analyze class hierarchy
            
        Returns:
            Dictionary containing analysis results
        """
        # Initialize result
        result = {
            "imports": [],
            "function_calls": [],
            "classes": []
        }
        
        try:
            # Read file
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content, filename=file_path)
            
            # Analyze imports
            if analyze_imports:
                result["imports"] = self._analyze_python_imports(tree, file_path)
            
            # Analyze function calls
            if analyze_function_calls:
                result["function_calls"] = self._analyze_python_function_calls(tree, file_path)
            
            # Analyze class hierarchy
            if analyze_class_hierarchy:
                result["classes"] = self._analyze_python_classes(tree, file_path)
        except Exception as e:
            logger.error(f"Error analyzing Python file {file_path}: {e}")
        
        return result
    
    def _analyze_python_imports(self, tree: ast.AST, file_path: str) -> List[Dict[str, Any]]:
        """
        Analyze imports in a Python AST.
        
        Args:
            tree: AST of the file
            file_path: Path to the file
            
        Returns:
            List of import information
        """
        imports = []
        
        # Get directory of the file
        file_dir = os.path.dirname(file_path)
        
        # Visit all import nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                # Process regular imports
                for name in node.names:
                    imports.append({
                        "name": name.name,
                        "alias": name.asname,
                        "type": "import"
                    })
                    
                    # Try to find the imported file
                    imported_file = self._find_python_module(name.name, file_dir)
                    if imported_file:
                        imports[-1]["file"] = imported_file
            
            elif isinstance(node, ast.ImportFrom):
                # Process from imports
                module = node.module or ""
                for name in node.names:
                    imports.append({
                        "name": f"{module}.{name.name}" if module else name.name,
                        "alias": name.asname,
                        "type": "from_import",
                        "module": module
                    })
                    
                    # Try to find the imported file
                    imported_file = self._find_python_module(module, file_dir)
                    if imported_file:
                        imports[-1]["file"] = imported_file
        
        return imports
    
    def _find_python_module(self, module_name: str, file_dir: str) -> Optional[str]:
        """
        Find the file path for a Python module.
        
        Args:
            module_name: Name of the module
            file_dir: Directory of the importing file
            
        Returns:
            Path to the module file, or None if not found
        """
        # Split module name into parts
        parts = module_name.split(".")
        
        # Try to find the module in the same directory
        module_path = os.path.join(file_dir, *parts)
        
        # Check if it's a file
        if os.path.isfile(f"{module_path}.py"):
            return f"{module_path}.py"
        
        # Check if it's a directory with __init__.py
        if os.path.isdir(module_path) and os.path.isfile(os.path.join(module_path, "__init__.py")):
            return os.path.join(module_path, "__init__.py")
        
        # Try to find the module in parent directories
        parent_dir = os.path.dirname(file_dir)
        if parent_dir and parent_dir != file_dir:
            return self._find_python_module(module_name, parent_dir)
        
        return None
    
    def _analyze_python_function_calls(self, tree: ast.AST, file_path: str) -> List[Dict[str, Any]]:
        """
        Analyze function calls in a Python AST.
        
        Args:
            tree: AST of the file
            file_path: Path to the file
            
        Returns:
            List of function call information
        """
        function_calls = []
        
        # Visit all call nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Get function name
                if isinstance(node.func, ast.Name):
                    # Simple function call
                    function_name = node.func.id
                    function_calls.append({
                        "name": function_name,
                        "type": "function"
                    })
                
                elif isinstance(node.func, ast.Attribute):
                    # Method call or qualified function call
                    function_name = node.func.attr
                    
                    # Get the value (object or module)
                    if isinstance(node.func.value, ast.Name):
                        value_name = node.func.value.id
                        function_calls.append({
                            "name": f"{value_name}.{function_name}",
                            "type": "method",
                            "object": value_name
                        })
        
        return function_calls
    
    def _analyze_python_classes(self, tree: ast.AST, file_path: str) -> List[Dict[str, Any]]:
        """
        Analyze classes in a Python AST.
        
        Args:
            tree: AST of the file
            file_path: Path to the file
            
        Returns:
            List of class information
        """
        classes = []
        
        # Visit all class nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Get class name
                class_name = node.name
                
                # Get parent classes
                parents = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        parents.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        if isinstance(base.value, ast.Name):
                            parents.append(f"{base.value.id}.{base.attr}")
                
                classes.append({
                    "name": class_name,
                    "parents": parents
                })
        
        return classes
    
    def _analyze_javascript_file(self, file_path: str,
                               analyze_imports: bool,
                               analyze_function_calls: bool,
                               analyze_class_hierarchy: bool) -> Dict[str, Any]:
        """
        Analyze a JavaScript file.
        
        Args:
            file_path: Path to the file
            analyze_imports: Whether to analyze imports
            analyze_function_calls: Whether to analyze function calls
            analyze_class_hierarchy: Whether to analyze class hierarchy
            
        Returns:
            Dictionary containing analysis results
        """
        # Initialize result
        result = {
            "imports": [],
            "function_calls": [],
            "classes": []
        }
        
        try:
            # Read file
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Analyze imports
            if analyze_imports:
                result["imports"] = self._analyze_javascript_imports(content, file_path)
            
            # Analyze function calls and classes are more complex for JavaScript
            # and would require a proper parser like esprima or babel
            # This is a simplified version using regex
            if analyze_function_calls:
                result["function_calls"] = self._analyze_javascript_function_calls(content, file_path)
            
            if analyze_class_hierarchy:
                result["classes"] = self._analyze_javascript_classes(content, file_path)
        except Exception as e:
            logger.error(f"Error analyzing JavaScript file {file_path}: {e}")
        
        return result
    
    def _analyze_javascript_imports(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Analyze imports in a JavaScript file.
        
        Args:
            content: Content of the file
            file_path: Path to the file
            
        Returns:
            List of import information
        """
        imports = []
        
        # Get directory of the file
        file_dir = os.path.dirname(file_path)
        
        # Find ES6 imports
        es6_import_pattern = r'import\s+(?:{([^}]*)}\s+from\s+)?(?:([^\s;]+)\s+from\s+)?[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(es6_import_pattern, content):
            named_imports, default_import, module_path = match.groups()
            
            if default_import:
                imports.append({
                    "name": module_path,
                    "alias": default_import,
                    "type": "import_default"
                })
            
            if named_imports:
                for named_import in re.finditer(r'([^\s,]+)(?:\s+as\s+([^\s,]+))?', named_imports):
                    name, alias = named_import.groups()
                    imports.append({
                        "name": f"{module_path}.{name}",
                        "alias": alias,
                        "type": "import_named"
                    })
            
            # If no default or named imports, it's a side-effect import
            if not default_import and not named_imports:
                imports.append({
                    "name": module_path,
                    "type": "import_side_effect"
                })
            
            # Try to find the imported file
            imported_file = self._find_javascript_module(module_path, file_dir)
            if imported_file:
                for imp in imports:
                    if imp["name"].startswith(module_path):
                        imp["file"] = imported_file
        
        # Find CommonJS requires
        require_pattern = r'(?:const|let|var)\s+(?:{([^}]*)}\s*=\s*)?(?:([^\s=]+)\s*=\s*)?require\([\'"]([^\'"]+)[\'"]\)'
        for match in re.finditer(require_pattern, content):
            named_imports, default_import, module_path = match.groups()
            
            if default_import:
                imports.append({
                    "name": module_path,
                    "alias": default_import,
                    "type": "require"
                })
            
            if named_imports:
                for named_import in re.finditer(r'([^\s,]+)(?:\s*:\s*([^\s,]+))?', named_imports):
                    name, alias = named_import.groups()
                    imports.append({
                        "name": f"{module_path}.{name}",
                        "alias": alias or name,
                        "type": "require_destructure"
                    })
            
            # Try to find the imported file
            imported_file = self._find_javascript_module(module_path, file_dir)
            if imported_file:
                for imp in imports:
                    if imp["name"].startswith(module_path):
                        imp["file"] = imported_file
        
        return imports
    
    def _find_javascript_module(self, module_path: str, file_dir: str) -> Optional[str]:
        """
        Find the file path for a JavaScript module.
        
        Args:
            module_path: Path to the module
            file_dir: Directory of the importing file
            
        Returns:
            Path to the module file, or None if not found
        """
        # If it's a relative path
        if module_path.startswith("."):
            # Resolve the path
            resolved_path = os.path.normpath(os.path.join(file_dir, module_path))
            
            # Check if it's a file
            for ext in [".js", ".jsx", ".ts", ".tsx"]:
                if os.path.isfile(f"{resolved_path}{ext}"):
                    return f"{resolved_path}{ext}"
            
            # Check if it's a directory with index.js
            for ext in [".js", ".jsx", ".ts", ".tsx"]:
                if os.path.isdir(resolved_path) and os.path.isfile(os.path.join(resolved_path, f"index{ext}")):
                    return os.path.join(resolved_path, f"index{ext}")
        
        # If it's a node module, we can't resolve it without knowing the node_modules directory
        return None
    
    def _analyze_javascript_function_calls(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Analyze function calls in a JavaScript file.
        
        Args:
            content: Content of the file
            file_path: Path to the file
            
        Returns:
            List of function call information
        """
        function_calls = []
        
        # Find function calls
        function_call_pattern = r'(?:([^\s.()]+)\.)?([^\s.()]+)\('
        for match in re.finditer(function_call_pattern, content):
            object_name, function_name = match.groups()
            
            if object_name:
                function_calls.append({
                    "name": f"{object_name}.{function_name}",
                    "type": "method",
                    "object": object_name
                })
            else:
                function_calls.append({
                    "name": function_name,
                    "type": "function"
                })
        
        return function_calls
    
    def _analyze_javascript_classes(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Analyze classes in a JavaScript file.
        
        Args:
            content: Content of the file
            file_path: Path to the file
            
        Returns:
            List of class information
        """
        classes = []
        
        # Find ES6 classes
        class_pattern = r'class\s+([^\s{]+)(?:\s+extends\s+([^\s{]+))?'
        for match in re.finditer(class_pattern, content):
            class_name, parent_name = match.groups()
            
            classes.append({
                "name": class_name,
                "parents": [parent_name] if parent_name else []
            })
        
        return classes
    
    def _analyze_typescript_file(self, file_path: str,
                               analyze_imports: bool,
                               analyze_function_calls: bool,
                               analyze_class_hierarchy: bool) -> Dict[str, Any]:
        """
        Analyze a TypeScript file.
        
        Args:
            file_path: Path to the file
            analyze_imports: Whether to analyze imports
            analyze_function_calls: Whether to analyze function calls
            analyze_class_hierarchy: Whether to analyze class hierarchy
            
        Returns:
            Dictionary containing analysis results
        """
        # TypeScript analysis is similar to JavaScript
        return self._analyze_javascript_file(
            file_path,
            analyze_imports,
            analyze_function_calls,
            analyze_class_hierarchy
        )
