"""
Dependency Analysis service for CI/CD pipelines.
This module provides dependency analysis capabilities for pipeline configurations.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import copy
import re

class DependencyAnalyzerService:
    """
    Service for analyzing and optimizing dependencies in CI/CD pipelines.
    """
    
    def __init__(self):
        """Initialize the dependency analyzer service."""
        pass
    
    def analyze_dependencies(self, platform: str, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze dependencies between jobs in a pipeline configuration.
        
        Args:
            platform (str): The CI/CD platform name
            pipeline_config (Dict[str, Any]): The pipeline configuration
            
        Returns:
            Dict containing dependency analysis results
        """
        if platform == "github-actions":
            return self._analyze_github_actions_dependencies(pipeline_config)
        elif platform == "gitlab-ci":
            return self._analyze_gitlab_ci_dependencies(pipeline_config)
        elif platform == "azure-pipelines":
            return self._analyze_azure_pipelines_dependencies(pipeline_config)
        elif platform == "circle-ci":
            return self._analyze_circle_ci_dependencies(pipeline_config)
        elif platform == "jenkins":
            return self._analyze_jenkins_dependencies(pipeline_config)
        elif platform == "travis-ci":
            return self._analyze_travis_ci_dependencies(pipeline_config)
        elif platform == "bitbucket-pipelines":
            return self._analyze_bitbucket_pipelines_dependencies(pipeline_config)
        elif platform == "aws-codebuild":
            return self._analyze_aws_codebuild_dependencies(pipeline_config)
        else:
            return {"error": f"Unsupported platform: {platform}"}
    
    def optimize_dependencies(self, platform: str, pipeline_config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Optimize dependencies between jobs in a pipeline configuration.
        
        Args:
            platform (str): The CI/CD platform name
            pipeline_config (Dict[str, Any]): The pipeline configuration
            
        Returns:
            Tuple containing:
            - The optimized pipeline configuration
            - List of applied optimizations
        """
        # Create a deep copy of the pipeline config to avoid modifying the original
        optimized_config = copy.deepcopy(pipeline_config)
        applied_optimizations = []
        
        if platform == "github-actions":
            optimized_config, applied_optimizations = self._optimize_github_actions_dependencies(optimized_config)
        elif platform == "gitlab-ci":
            optimized_config, applied_optimizations = self._optimize_gitlab_ci_dependencies(optimized_config)
        elif platform == "azure-pipelines":
            optimized_config, applied_optimizations = self._optimize_azure_pipelines_dependencies(optimized_config)
        elif platform == "circle-ci":
            optimized_config, applied_optimizations = self._optimize_circle_ci_dependencies(optimized_config)
        elif platform == "jenkins":
            optimized_config, applied_optimizations = self._optimize_jenkins_dependencies(optimized_config)
        elif platform == "travis-ci":
            optimized_config, applied_optimizations = self._optimize_travis_ci_dependencies(optimized_config)
        elif platform == "bitbucket-pipelines":
            optimized_config, applied_optimizations = self._optimize_bitbucket_pipelines_dependencies(optimized_config)
        elif platform == "aws-codebuild":
            optimized_config, applied_optimizations = self._optimize_aws_codebuild_dependencies(optimized_config)
        
        return optimized_config, applied_optimizations
    
    def _analyze_github_actions_dependencies(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze dependencies between jobs in a GitHub Actions workflow.
        
        Args:
            pipeline_config (Dict[str, Any]): The GitHub Actions workflow configuration
            
        Returns:
            Dict containing dependency analysis results
        """
        result = {
            "dependencies": {},
            "dependency_graph": {},
            "critical_path": [],
            "parallel_groups": [],
            "optimization_opportunities": []
        }
        
        jobs = pipeline_config.get("jobs", {})
        
        # Build dependency graph
        for job_id, job in jobs.items():
            needs = job.get("needs", [])
            if isinstance(needs, str):
                needs = [needs]
            
            result["dependencies"][job_id] = needs
            result["dependency_graph"][job_id] = {
                "dependencies": needs,
                "dependents": []
            }
        
        # Populate dependents
        for job_id, deps in result["dependencies"].items():
            for dep in deps:
                if dep in result["dependency_graph"]:
                    result["dependency_graph"][dep]["dependents"].append(job_id)
        
        # Find root jobs (no dependencies)
        root_jobs = [job_id for job_id, deps in result["dependencies"].items() if not deps]
        result["root_jobs"] = root_jobs
        
        # Find leaf jobs (no dependents)
        leaf_jobs = [job_id for job_id, info in result["dependency_graph"].items() if not info["dependents"]]
        result["leaf_jobs"] = leaf_jobs
        
        # Identify parallel groups (jobs that can run in parallel)
        visited = set()
        
        def get_level(job_id, level_map):
            if job_id in level_map:
                return level_map[job_id]
            
            if not result["dependencies"][job_id]:
                level_map[job_id] = 0
                return 0
            
            max_dep_level = max(get_level(dep, level_map) for dep in result["dependencies"][job_id])
            level_map[job_id] = max_dep_level + 1
            return level_map[job_id]
        
        # Calculate level for each job
        level_map = {}
        for job_id in jobs:
            get_level(job_id, level_map)
        
        # Group jobs by level
        level_groups = {}
        for job_id, level in level_map.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(job_id)
        
        result["parallel_groups"] = [jobs for level, jobs in sorted(level_groups.items())]
        
        # Find critical path (longest path from root to leaf)
        critical_path = []
        max_level = max(level_map.values()) if level_map else 0
        
        for level in range(max_level + 1):
            if level in level_groups:
                # For simplicity, just take the first job at each level for the critical path
                # In a real implementation, you would calculate job durations and find the actual critical path
                if level_groups[level]:
                    critical_path.append(level_groups[level][0])
        
        result["critical_path"] = critical_path
        
        # Identify optimization opportunities
        
        # 1. Unnecessary dependencies
        for job_id, deps in result["dependencies"].items():
            transitive_deps = set()
            for dep in deps:
                transitive_deps.update(result["dependencies"].get(dep, []))
            
            redundant_deps = [dep for dep in deps if dep in transitive_deps]
            if redundant_deps:
                result["optimization_opportunities"].append({
                    "type": "redundant_dependency",
                    "job_id": job_id,
                    "redundant_dependencies": redundant_deps,
                    "description": f"Job '{job_id}' has redundant dependencies: {', '.join(redundant_deps)}"
                })
        
        # 2. Parallel execution opportunities
        for level, jobs in level_groups.items():
            if len(jobs) > 1:
                result["optimization_opportunities"].append({
                    "type": "parallel_execution",
                    "level": level,
                    "jobs": jobs,
                    "description": f"Level {level} has {len(jobs)} jobs that can run in parallel"
                })
        
        # 3. Long dependency chains
        long_chains = []
        for job_id in leaf_jobs:
            chain_length = level_map.get(job_id, 0)
            if chain_length > 2:  # Consider chains of length > 2 as "long"
                long_chains.append({
                    "job_id": job_id,
                    "chain_length": chain_length + 1  # +1 to include the job itself
                })
        
        if long_chains:
            result["optimization_opportunities"].append({
                "type": "long_dependency_chains",
                "chains": long_chains,
                "description": f"Found {len(long_chains)} long dependency chains that might benefit from restructuring"
            })
        
        return result
    
    def _optimize_github_actions_dependencies(self, pipeline_config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Optimize dependencies between jobs in a GitHub Actions workflow.
        
        Args:
            pipeline_config (Dict[str, Any]): The GitHub Actions workflow configuration
            
        Returns:
            Tuple containing:
            - The optimized pipeline configuration
            - List of applied optimizations
        """
        optimized_config = copy.deepcopy(pipeline_config)
        applied_optimizations = []
        
        # Analyze dependencies
        analysis = self._analyze_github_actions_dependencies(pipeline_config)
        
        # Apply optimizations based on analysis
        
        # 1. Remove redundant dependencies
        for opportunity in analysis.get("optimization_opportunities", []):
            if opportunity["type"] == "redundant_dependency":
                job_id = opportunity["job_id"]
                redundant_deps = set(opportunity["redundant_dependencies"])
                
                if job_id in optimized_config.get("jobs", {}):
                    current_needs = optimized_config["jobs"][job_id].get("needs", [])
                    if isinstance(current_needs, str):
                        current_needs = [current_needs]
                    
                    # Remove redundant dependencies
                    optimized_needs = [dep for dep in current_needs if dep not in redundant_deps]
                    
                    if optimized_needs:
                        optimized_config["jobs"][job_id]["needs"] = optimized_needs
                    elif "needs" in optimized_config["jobs"][job_id]:
                        del optimized_config["jobs"][job_id]["needs"]
                    
                    applied_optimizations.append({
                        "type": "redundant_dependency_removal",
                        "job_id": job_id,
                        "removed_dependencies": list(redundant_deps),
                        "description": f"Removed redundant dependencies from job '{job_id}': {', '.join(redundant_deps)}"
                    })
        
        # 2. Optimize parallel execution
        # For GitHub Actions, jobs run in parallel by default unless they have dependencies
        # So we don't need to do anything special here
        
        return optimized_config, applied_optimizations
    
    def _analyze_gitlab_ci_dependencies(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze dependencies between jobs in a GitLab CI pipeline.
        
        Args:
            pipeline_config (Dict[str, Any]): The GitLab CI pipeline configuration
            
        Returns:
            Dict containing dependency analysis results
        """
        result = {
            "dependencies": {},
            "dependency_graph": {},
            "critical_path": [],
            "parallel_groups": [],
            "optimization_opportunities": []
        }
        
        # Extract stages
        stages = pipeline_config.get("stages", [])
        stage_jobs = {stage: [] for stage in stages}
        
        # Build dependency graph
        for job_id, job in pipeline_config.items():
            if isinstance(job, dict) and "stage" in job:
                stage = job.get("stage")
                needs = job.get("needs", [])
                
                if stage in stage_jobs:
                    stage_jobs[stage].append(job_id)
                
                result["dependencies"][job_id] = needs
                result["dependency_graph"][job_id] = {
                    "dependencies": needs,
                    "dependents": [],
                    "stage": stage
                }
        
        # Populate dependents
        for job_id, deps in result["dependencies"].items():
            for dep in deps:
                if dep in result["dependency_graph"]:
                    result["dependency_graph"][dep]["dependents"].append(job_id)
        
        # Find root jobs (no explicit dependencies, first stage)
        first_stage = stages[0] if stages else None
        root_jobs = [job_id for job_id, info in result["dependency_graph"].items() 
                    if not info["dependencies"] and info["stage"] == first_stage]
        result["root_jobs"] = root_jobs
        
        # Find leaf jobs (no dependents, last stage)
        last_stage = stages[-1] if stages else None
        leaf_jobs = [job_id for job_id, info in result["dependency_graph"].items() 
                    if not info["dependents"] and info["stage"] == last_stage]
        result["leaf_jobs"] = leaf_jobs
        
        # Identify parallel groups (jobs in the same stage)
        result["parallel_groups"] = [jobs for stage, jobs in stage_jobs.items() if jobs]
        
        # Identify optimization opportunities
        
        # 1. Redundant dependencies (transitive dependencies)
        for job_id, deps in result["dependencies"].items():
            transitive_deps = set()
            for dep in deps:
                transitive_deps.update(result["dependencies"].get(dep, []))
            
            redundant_deps = [dep for dep in deps if dep in transitive_deps]
            if redundant_deps:
                result["optimization_opportunities"].append({
                    "type": "redundant_dependency",
                    "job_id": job_id,
                    "redundant_dependencies": redundant_deps,
                    "description": f"Job '{job_id}' has redundant dependencies: {', '.join(redundant_deps)}"
                })
        
        # 2. Unnecessary dependencies
        for job_id, deps in result["dependencies"].items():
            job_stage = result["dependency_graph"][job_id]["stage"]
            stage_index = stages.index(job_stage) if job_stage in stages else -1
            
            if stage_index > 0:
                prev_stage = stages[stage_index - 1]
                prev_stage_jobs = stage_jobs.get(prev_stage, [])
                
                # Check if job depends on all jobs from previous stage
                if set(deps) == set(prev_stage_jobs) and len(deps) > 1:
                    result["optimization_opportunities"].append({
                        "type": "stage_dependency",
                        "job_id": job_id,
                        "stage": job_stage,
                        "previous_stage": prev_stage,
                        "description": f"Job '{job_id}' depends on all jobs from previous stage '{prev_stage}'. Consider using stage dependencies instead of explicit job dependencies."
                    })
        
        # 3. Cross-stage dependencies
        for job_id, deps in result["dependencies"].items():
            job_stage = result["dependency_graph"][job_id]["stage"]
            job_stage_index = stages.index(job_stage) if job_stage in stages else -1
            
            for dep in deps:
                if dep in result["dependency_graph"]:
                    dep_stage = result["dependency_graph"][dep]["stage"]
                    dep_stage_index = stages.index(dep_stage) if dep_stage in stages else -1
                    
                    if dep_stage_index < job_stage_index - 1:
                        result["optimization_opportunities"].append({
                            "type": "cross_stage_dependency",
                            "job_id": job_id,
                            "dependency": dep,
                            "job_stage": job_stage,
                            "dependency_stage": dep_stage,
                            "description": f"Job '{job_id}' in stage '{job_stage}' depends on job '{dep}' from non-adjacent stage '{dep_stage}'. This might indicate a suboptimal stage structure."
                        })
        
        return result
    
    def _optimize_gitlab_ci_dependencies(self, pipeline_config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Optimize dependencies between jobs in a GitLab CI pipeline.
        
        Args:
            pipeline_config (Dict[str, Any]): The GitLab CI pipeline configuration
            
        Returns:
            Tuple containing:
            - The optimized pipeline configuration
            - List of applied optimizations
        """
        optimized_config = copy.deepcopy(pipeline_config)
        applied_optimizations = []
        
        # Analyze dependencies
        analysis = self._analyze_gitlab_ci_dependencies(pipeline_config)
        
        # Apply optimizations based on analysis
        
        # 1. Remove redundant dependencies
        for opportunity in analysis.get("optimization_opportunities", []):
            if opportunity["type"] == "redundant_dependency":
                job_id = opportunity["job_id"]
                redundant_deps = set(opportunity["redundant_dependencies"])
                
                if job_id in optimized_config:
                    current_needs = optimized_config[job_id].get("needs", [])
                    
                    # Remove redundant dependencies
                    optimized_needs = [dep for dep in current_needs if dep not in redundant_deps]
                    
                    if optimized_needs:
                        optimized_config[job_id]["needs"] = optimized_needs
                    elif "needs" in optimized_config[job_id]:
                        del optimized_config[job_id]["needs"]
                    
                    applied_optimizations.append({
                        "type": "redundant_dependency_removal",
                        "job_id": job_id,
                        "removed_dependencies": list(redundant_deps),
                        "description": f"Removed redundant dependencies from job '{job_id}': {', '.join(redundant_deps)}"
                    })
        
        # 2. Replace full stage dependencies with stage dependencies
        for opportunity in analysis.get("optimization_opportunities", []):
            if opportunity["type"] == "stage_dependency":
                job_id = opportunity["job_id"]
                
                if job_id in optimized_config:
                    # Remove explicit dependencies
                    if "needs" in optimized_config[job_id]:
                        del optimized_config[job_id]["needs"]
                    
                    applied_optimizations.append({
                        "type": "stage_dependency_optimization",
                        "job_id": job_id,
                        "description": f"Removed explicit dependencies from job '{job_id}' to rely on stage dependencies instead"
                    })
        
        return optimized_config, applied_optimizations
    
    def _analyze_azure_pipelines_dependencies(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze dependencies between jobs in an Azure Pipelines configuration.
        
        Args:
            pipeline_config (Dict[str, Any]): The Azure Pipelines configuration
            
        Returns:
            Dict containing dependency analysis results
        """
        result = {
            "dependencies": {},
            "dependency_graph": {},
            "critical_path": [],
            "parallel_groups": [],
            "optimization_opportunities": []
        }
        
        # Extract jobs from the pipeline configuration
        # Azure Pipelines can have jobs defined in different ways:
        # 1. In the 'jobs' section
        # 2. In the 'stages' section, where each stage has jobs
        # 3. Directly as 'steps' at the root level (single job)
        
        jobs = {}
        
        # Case 1: Jobs defined in 'jobs' section
        if "jobs" in pipeline_config:
            for job in pipeline_config["jobs"]:
                job_id = job.get("job", job.get("name", f"job_{len(jobs)}"))
                jobs[job_id] = job
                
                # Extract dependencies (dependsOn)
                depends_on = job.get("dependsOn", [])
                if isinstance(depends_on, str):
                    depends_on = [depends_on]
                
                result["dependencies"][job_id] = depends_on
                result["dependency_graph"][job_id] = {
                    "dependencies": depends_on,
                    "dependents": []
                }
        
        # Case 2: Jobs defined in stages
        if "stages" in pipeline_config:
            for stage_index, stage in enumerate(pipeline_config["stages"]):
                stage_id = stage.get("stage", f"stage_{stage_index}")
                stage_jobs = stage.get("jobs", [])
                
                for job in stage_jobs:
                    job_id = job.get("job", job.get("name", f"{stage_id}_job_{len(jobs)}"))
                    jobs[job_id] = job
                    
                    # Extract dependencies (dependsOn)
                    depends_on = job.get("dependsOn", [])
                    if isinstance(depends_on, str):
                        depends_on = [depends_on]
                    
                    # Add implicit stage dependency if not specified
                    if stage_index > 0 and not depends_on:
                        # Jobs in a stage implicitly depend on the previous stage
                        prev_stage_id = pipeline_config["stages"][stage_index - 1].get(
                            "stage", f"stage_{stage_index - 1}")
                        depends_on = [f"{prev_stage_id}"]
                    
                    result["dependencies"][job_id] = depends_on
                    result["dependency_graph"][job_id] = {
                        "dependencies": depends_on,
                        "dependents": [],
                        "stage": stage_id
                    }
        
        # Case 3: Single job with steps at root level
        if "steps" in pipeline_config and not jobs:
            job_id = "default_job"
            jobs[job_id] = pipeline_config
            result["dependencies"][job_id] = []
            result["dependency_graph"][job_id] = {
                "dependencies": [],
                "dependents": []
            }
        
        # Populate dependents
        for job_id, deps in result["dependencies"].items():
            for dep in deps:
                if dep in result["dependency_graph"]:
                    result["dependency_graph"][dep]["dependents"].append(job_id)
        
        # Find root jobs (no dependencies)
        root_jobs = [job_id for job_id, deps in result["dependencies"].items() if not deps]
        result["root_jobs"] = root_jobs
        
        # Find leaf jobs (no dependents)
        leaf_jobs = [job_id for job_id, info in result["dependency_graph"].items() if not info["dependents"]]
        result["leaf_jobs"] = leaf_jobs
        
        # Identify parallel groups (jobs that can run in parallel)
        visited = set()
        
        def get_level(job_id, level_map):
            if job_id in level_map:
                return level_map[job_id]
            
            if not result["dependencies"][job_id]:
                level_map[job_id] = 0
                return 0
            
            max_dep_level = max(get_level(dep, level_map) for dep in result["dependencies"][job_id])
            level_map[job_id] = max_dep_level + 1
            return level_map[job_id]
        
        # Calculate level for each job
        level_map = {}
        for job_id in jobs:
            get_level(job_id, level_map)
        
        # Group jobs by level
        level_groups = {}
        for job_id, level in level_map.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(job_id)
        
        result["parallel_groups"] = [jobs for level, jobs in sorted(level_groups.items())]
        
        # Find critical path (longest path from root to leaf)
        critical_path = []
        max_level = max(level_map.values()) if level_map else 0
        
        for level in range(max_level + 1):
            if level in level_groups:
                # For simplicity, just take the first job at each level for the critical path
                if level_groups[level]:
                    critical_path.append(level_groups[level][0])
        
        result["critical_path"] = critical_path
        
        # Identify optimization opportunities
        
        # 1. Unnecessary dependencies
        for job_id, deps in result["dependencies"].items():
            transitive_deps = set()
            for dep in deps:
                transitive_deps.update(result["dependencies"].get(dep, []))
            
            redundant_deps = [dep for dep in deps if dep in transitive_deps]
            if redundant_deps:
                result["optimization_opportunities"].append({
                    "type": "redundant_dependency",
                    "job_id": job_id,
                    "redundant_dependencies": redundant_deps,
                    "description": f"Job '{job_id}' has redundant dependencies: {', '.join(redundant_deps)}"
                })
        
        # 2. Parallel execution opportunities
        for level, jobs_list in level_groups.items():
            if len(jobs_list) > 1:
                result["optimization_opportunities"].append({
                    "type": "parallel_execution",
                    "level": level,
                    "jobs": jobs_list,
                    "description": f"Level {level} has {len(jobs_list)} jobs that can run in parallel"
                })
        
        # 3. Long dependency chains
        long_chains = []
        for job_id in leaf_jobs:
            chain_length = level_map.get(job_id, 0)
            if chain_length > 2:  # Consider chains of length > 2 as "long"
                long_chains.append({
                    "job_id": job_id,
                    "chain_length": chain_length + 1  # +1 to include the job itself
                })
        
        if long_chains:
            result["optimization_opportunities"].append({
                "type": "long_dependency_chains",
                "chains": long_chains,
                "description": f"Found {len(long_chains)} long dependency chains that might benefit from restructuring"
            })
        
        return result
    
    def _optimize_azure_pipelines_dependencies(self, pipeline_config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Optimize dependencies between jobs in an Azure Pipelines configuration.
        
        Args:
            pipeline_config (Dict[str, Any]): The Azure Pipelines configuration
            
        Returns:
            Tuple containing:
            - The optimized pipeline configuration
            - List of applied optimizations
        """
        optimized_config = copy.deepcopy(pipeline_config)
        applied_optimizations = []
        
        # Analyze dependencies
        analysis = self._analyze_azure_pipelines_dependencies(pipeline_config)
        
        # Apply optimizations based on analysis
        
        # 1. Remove redundant dependencies
        for opportunity in analysis.get("optimization_opportunities", []):
            if opportunity["type"] == "redundant_dependency":
                job_id = opportunity["job_id"]
                redundant_deps = set(opportunity["redundant_dependencies"])
                
                # Find the job in the pipeline configuration
                if "jobs" in optimized_config:
                    for job_index, job in enumerate(optimized_config["jobs"]):
                        if job.get("job") == job_id or job.get("name") == job_id:
                            # Remove redundant dependencies
                            current_deps = job.get("dependsOn", [])
                            if isinstance(current_deps, str):
                                current_deps = [current_deps]
                            
                            optimized_deps = [dep for dep in current_deps if dep not in redundant_deps]
                            
                            if optimized_deps:
                                optimized_config["jobs"][job_index]["dependsOn"] = optimized_deps
                            elif "dependsOn" in optimized_config["jobs"][job_index]:
                                del optimized_config["jobs"][job_index]["dependsOn"]
                            
                            applied_optimizations.append({
                                "type": "redundant_dependency_removal",
                                "job_id": job_id,
                                "removed_dependencies": list(redundant_deps),
                                "description": f"Removed redundant dependencies from job '{job_id}': {', '.join(redundant_deps)}"
                            })
                
                # Check in stages
                if "stages" in optimized_config:
                    for stage in optimized_config["stages"]:
                        if "jobs" in stage:
                            for job_index, job in enumerate(stage["jobs"]):
                                if job.get("job") == job_id or job.get("name") == job_id:
                                    # Remove redundant dependencies
                                    current_deps = job.get("dependsOn", [])
                                    if isinstance(current_deps, str):
                                        current_deps = [current_deps]
                                    
                                    optimized_deps = [dep for dep in current_deps if dep not in redundant_deps]
                                    
                                    if optimized_deps:
                                        stage["jobs"][job_index]["dependsOn"] = optimized_deps
                                    elif "dependsOn" in stage["jobs"][job_index]:
                                        del stage["jobs"][job_index]["dependsOn"]
                                    
                                    applied_optimizations.append({
                                        "type": "redundant_dependency_removal",
                                        "job_id": job_id,
                                        "removed_dependencies": list(redundant_deps),
                                        "description": f"Removed redundant dependencies from job '{job_id}': {', '.join(redundant_deps)}"
                                    })
        
        return optimized_config, applied_optimizations
    
    def _analyze_circle_ci_dependencies(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze dependencies between jobs in a CircleCI configuration.
        
        Args:
            pipeline_config (Dict[str, Any]): The CircleCI configuration
            
        Returns:
            Dict containing dependency analysis results
        """
        result = {
            "dependencies": {},
            "dependency_graph": {},
            "critical_path": [],
            "parallel_groups": [],
            "optimization_opportunities": []
        }
        
        # Extract jobs and workflows
        jobs = pipeline_config.get("jobs", {})
        workflows = pipeline_config.get("workflows", {})
        
        # Build dependency graph from workflows
        for workflow_name, workflow in workflows.items():
            if isinstance(workflow, dict) and "jobs" in workflow:
                workflow_jobs = workflow["jobs"]
                
                # Process workflow jobs
                for job_item in workflow_jobs:
                    # Job can be a string or a dictionary with requires
                    if isinstance(job_item, str):
                        job_id = job_item
                        requires = []
                    else:
                        job_id = job_item.get("job", "")
                        requires = job_item.get("requires", [])
                    
                    if job_id:
                        result["dependencies"][job_id] = requires
                        result["dependency_graph"][job_id] = {
                            "dependencies": requires,
                            "dependents": [],
                            "workflow": workflow_name
                        }
        
        # Populate dependents
        for job_id, deps in result["dependencies"].items():
            for dep in deps:
                if dep in result["dependency_graph"]:
                    result["dependency_graph"][dep]["dependents"].append(job_id)
        
        # Find root jobs (no dependencies)
        root_jobs = [job_id for job_id, deps in result["dependencies"].items() if not deps]
        result["root_jobs"] = root_jobs
        
        # Find leaf jobs (no dependents)
        leaf_jobs = [job_id for job_id, info in result["dependency_graph"].items() if not info["dependents"]]
        result["leaf_jobs"] = leaf_jobs
        
        # Identify parallel groups (jobs that can run in parallel)
        visited = set()
        
        def get_level(job_id, level_map):
            if job_id in level_map:
                return level_map[job_id]
            
            if not result["dependencies"][job_id]:
                level_map[job_id] = 0
                return 0
            
            max_dep_level = max(get_level(dep, level_map) for dep in result["dependencies"][job_id])
            level_map[job_id] = max_dep_level + 1
            return level_map[job_id]
        
        # Calculate level for each job
        level_map = {}
        for job_id in result["dependencies"]:
            get_level(job_id, level_map)
        
        # Group jobs by level
        level_groups = {}
        for job_id, level in level_map.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(job_id)
        
        result["parallel_groups"] = [jobs for level, jobs in sorted(level_groups.items())]
        
        # Find critical path (longest path from root to leaf)
        critical_path = []
        max_level = max(level_map.values()) if level_map else 0
        
        for level in range(max_level + 1):
            if level in level_groups:
                # For simplicity, just take the first job at each level for the critical path
                if level_groups[level]:
                    critical_path.append(level_groups[level][0])
        
        result["critical_path"] = critical_path
        
        # Identify optimization opportunities
        
        # 1. Unnecessary dependencies
        for job_id, deps in result["dependencies"].items():
            transitive_deps = set()
            for dep in deps:
                transitive_deps.update(result["dependencies"].get(dep, []))
            
            redundant_deps = [dep for dep in deps if dep in transitive_deps]
            if redundant_deps:
                result["optimization_opportunities"].append({
                    "type": "redundant_dependency",
                    "job_id": job_id,
                    "redundant_dependencies": redundant_deps,
                    "description": f"Job '{job_id}' has redundant dependencies: {', '.join(redundant_deps)}"
                })
        
        # 2. Parallel execution opportunities
        for level, jobs_list in level_groups.items():
            if len(jobs_list) > 1:
                result["optimization_opportunities"].append({
                    "type": "parallel_execution",
                    "level": level,
                    "jobs": jobs_list,
                    "description": f"Level {level} has {len(jobs_list)} jobs that can run in parallel"
                })
        
        # 3. Long dependency chains
        long_chains = []
        for job_id in leaf_jobs:
            chain_length = level_map.get(job_id, 0)
            if chain_length > 2:  # Consider chains of length > 2 as "long"
                long_chains.append({
                    "job_id": job_id,
                    "chain_length": chain_length + 1  # +1 to include the job itself
                })
        
        if long_chains:
            result["optimization_opportunities"].append({
                "type": "long_dependency_chains",
                "chains": long_chains,
                "description": f"Found {len(long_chains)} long dependency chains that might benefit from restructuring"
            })
        
        return result
    
    def _optimize_circle_ci_dependencies(self, pipeline_config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Optimize dependencies between jobs in a CircleCI configuration.
        
        Args:
            pipeline_config (Dict[str, Any]): The CircleCI configuration
            
        Returns:
            Tuple containing:
            - The optimized pipeline configuration
            - List of applied optimizations
        """
        optimized_config = copy.deepcopy(pipeline_config)
        applied_optimizations = []
        
        # Analyze dependencies
        analysis = self._analyze_circle_ci_dependencies(pipeline_config)
        
        # Apply optimizations based on analysis
        
        # 1. Remove redundant dependencies
        for opportunity in analysis.get("optimization_opportunities", []):
            if opportunity["type"] == "redundant_dependency":
                job_id = opportunity["job_id"]
                redundant_deps = set(opportunity["redundant_dependencies"])
                
                # Find the job in workflows
                for workflow_name, workflow in optimized_config.get("workflows", {}).items():
                    if isinstance(workflow, dict) and "jobs" in workflow:
                        for job_index, job_item in enumerate(workflow["jobs"]):
                            if isinstance(job_item, dict) and job_item.get("job") == job_id:
                                # Remove redundant dependencies
                                current_requires = job_item.get("requires", [])
                                optimized_requires = [dep for dep in current_requires if dep not in redundant_deps]
                                
                                if optimized_requires:
                                    optimized_config["workflows"][workflow_name]["jobs"][job_index]["requires"] = optimized_requires
                                elif "requires" in optimized_config["workflows"][workflow_name]["jobs"][job_index]:
                                    del optimized_config["workflows"][workflow_name]["jobs"][job_index]["requires"]
                                
                                applied_optimizations.append({
                                    "type": "redundant_dependency_removal",
                                    "job_id": job_id,
                                    "removed_dependencies": list(redundant_deps),
                                    "description": f"Removed redundant dependencies from job '{job_id}': {', '.join(redundant_deps)}"
                                })
        
        return optimized_config, applied_optimizations
    
    def _analyze_jenkins_dependencies(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze dependencies between stages in a Jenkins pipeline.
        
        Args:
            pipeline_config (Dict[str, Any]): The Jenkins pipeline configuration
            
        Returns:
            Dict containing dependency analysis results
        """
        result = {
            "dependencies": {},
            "dependency_graph": {},
            "critical_path": [],
            "parallel_groups": [],
            "optimization_opportunities": []
        }
        
        # Note: Jenkins pipelines are typically defined in Groovy, not YAML
        # This implementation assumes a JSON/YAML representation of a Jenkins pipeline
        # with stages and parallel stages
        
        # Extract stages from the pipeline configuration
        stages = pipeline_config.get("stages", [])
        
        # Build dependency graph based on stage order
        # In Jenkins, stages typically run sequentially unless explicitly defined as parallel
        for stage_index, stage in enumerate(stages):
            stage_id = stage.get("name", f"stage_{stage_index}")
            
            # Check if this is a parallel stage
            if "parallel" in stage:
                parallel_stages = stage["parallel"]
                
                # Add each parallel stage to the dependency graph
                for parallel_index, parallel_stage in enumerate(parallel_stages):
                    parallel_stage_id = parallel_stage.get("name", f"{stage_id}_parallel_{parallel_index}")
                    
                    # Parallel stages depend on the previous sequential stage
                    dependencies = []
                    if stage_index > 0:
                        prev_stage = stages[stage_index - 1]
                        prev_stage_id = prev_stage.get("name", f"stage_{stage_index - 1}")
                        dependencies = [prev_stage_id]
                    
                    result["dependencies"][parallel_stage_id] = dependencies
                    result["dependency_graph"][parallel_stage_id] = {
                        "dependencies": dependencies,
                        "dependents": [],
                        "stage_index": stage_index,
                        "parallel": True
                    }
                
                # Add a virtual "end of parallel" stage that depends on all parallel stages
                end_parallel_id = f"{stage_id}_end_parallel"
                parallel_stage_ids = [
                    parallel_stage.get("name", f"{stage_id}_parallel_{i}")
                    for i, parallel_stage in enumerate(parallel_stages)
                ]
                
                result["dependencies"][end_parallel_id] = parallel_stage_ids
                result["dependency_graph"][end_parallel_id] = {
                    "dependencies": parallel_stage_ids,
                    "dependents": [],
                    "stage_index": stage_index,
                    "virtual": True
                }
            else:
                # Regular sequential stage
                dependencies = []
                if stage_index > 0:
                    prev_stage = stages[stage_index - 1]
                    
                    # If previous stage was parallel, depend on the virtual "end of parallel" stage
                    if "parallel" in prev_stage:
                        prev_stage_id = f"{prev_stage.get('name', f'stage_{stage_index - 1}')}_end_parallel"
                    else:
                        prev_stage_id = prev_stage.get("name", f"stage_{stage_index - 1}")
                    
                    dependencies = [prev_stage_id]
                
                result["dependencies"][stage_id] = dependencies
                result["dependency_graph"][stage_id] = {
                    "dependencies": dependencies,
                    "dependents": [],
                    "stage_index": stage_index,
                    "parallel": False
                }
        
        # Populate dependents
        for stage_id, deps in result["dependencies"].items():
            for dep in deps:
                if dep in result["dependency_graph"]:
                    result["dependency_graph"][dep]["dependents"].append(stage_id)
        
        # Find root stages (no dependencies)
        root_stages = [stage_id for stage_id, deps in result["dependencies"].items() if not deps]
        result["root_jobs"] = root_stages  # Using "root_jobs" for consistency with other platforms
        
        # Find leaf stages (no dependents)
        leaf_stages = [stage_id for stage_id, info in result["dependency_graph"].items() if not info["dependents"]]
        result["leaf_jobs"] = leaf_stages  # Using "leaf_jobs" for consistency with other platforms
        
        # Identify parallel groups (stages that can run in parallel)
        parallel_groups = []
        current_parallel_group = []
        
        for stage_index, stage in enumerate(stages):
            if "parallel" in stage:
                # Add all parallel stages as a group
                parallel_group = [
                    parallel_stage.get("name", f"{stage.get('name', f'stage_{stage_index}')}_parallel_{i}")
                    for i, parallel_stage in enumerate(stage["parallel"])
                ]
                parallel_groups.append(parallel_group)
            else:
                # Each sequential stage is its own group
                stage_id = stage.get("name", f"stage_{stage_index}")
                parallel_groups.append([stage_id])
        
        result["parallel_groups"] = parallel_groups
        
        # Find critical path (in Jenkins, this is typically the sequential path)
        critical_path = []
        for stage_index, stage in enumerate(stages):
            if "parallel" in stage:
                # For parallel stages, add the longest parallel stage to the critical path
                # In a real implementation, you would calculate durations and find the longest path
                # For simplicity, just add the first parallel stage
                if stage["parallel"]:
                    parallel_stage = stage["parallel"][0]
                    parallel_stage_id = parallel_stage.get("name", f"{stage.get('name', f'stage_{stage_index}')}_parallel_0")
                    critical_path.append(parallel_stage_id)
            else:
                # Add sequential stage to critical path
                stage_id = stage.get("name", f"stage_{stage_index}")
                critical_path.append(stage_id)
        
        result["critical_path"] = critical_path
        
        # Identify optimization opportunities
        
        # 1. Sequential stages that could be parallelized
        for stage_index in range(len(stages)):
            if stage_index > 0 and stage_index < len(stages) - 1:
                # Check if this stage and the next stage could be parallelized
                current_stage = stages[stage_index]
                next_stage = stages[stage_index + 1]
                
                # Skip if either stage is already parallel
                if "parallel" in current_stage or "parallel" in next_stage:
                    continue
                
                current_stage_id = current_stage.get("name", f"stage_{stage_index}")
                next_stage_id = next_stage.get("name", f"stage_{stage_index + 1}")
                
                # Check if these stages have independent operations
                # This is a simplified check - in a real implementation, you would analyze the stage contents
                result["optimization_opportunities"].append({
                    "type": "potential_parallelization",
                    "stages": [current_stage_id, next_stage_id],
                    "description": f"Stages '{current_stage_id}' and '{next_stage_id}' might be candidates for parallelization"
                })
        
        # 2. Parallel stages with uneven workloads
        for stage_index, stage in enumerate(stages):
            if "parallel" in stage and len(stage["parallel"]) > 1:
                stage_id = stage.get("name", f"stage_{stage_index}")
                
                # In a real implementation, you would analyze the workload of each parallel stage
                # For simplicity, just flag parallel stages with more than 2 branches
                if len(stage["parallel"]) > 2:
                    result["optimization_opportunities"].append({
                        "type": "uneven_parallel_workload",
                        "stage_id": stage_id,
                        "parallel_count": len(stage["parallel"]),
                        "description": f"Parallel stage '{stage_id}' has {len(stage['parallel'])} branches which might have uneven workloads"
                    })
        
        return result
    
    def _optimize_jenkins_dependencies(self, pipeline_config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Optimize dependencies between stages in a Jenkins pipeline.
        
        Args:
            pipeline_config (Dict[str, Any]): The Jenkins pipeline configuration
            
        Returns:
            Tuple containing:
            - The optimized pipeline configuration
            - List of applied optimizations
        """
        optimized_config = copy.deepcopy(pipeline_config)
        applied_optimizations = []
        
        # Analyze dependencies
        analysis = self._analyze_jenkins_dependencies(pipeline_config)
        
        # Apply optimizations based on analysis
        
        # 1. Parallelize sequential stages that could be run in parallel
        for opportunity in analysis.get("optimization_opportunities", []):
            if opportunity["type"] == "potential_parallelization":
                stages = opportunity["stages"]
                
                if len(stages) >= 2:
                    # Find the stages in the pipeline configuration
                    stage_indices = []
                    for stage_index, stage in enumerate(optimized_config.get("stages", [])):
                        stage_id = stage.get("name", f"stage_{stage_index}")
                        if stage_id in stages:
                            stage_indices.append(stage_index)
                    
                    if len(stage_indices) >= 2 and stage_indices[1] == stage_indices[0] + 1:
                        # Create a new parallel stage to replace the sequential stages
                        parallel_stages = []
                        
                        for idx in stage_indices:
                            if idx < len(optimized_config["stages"]):
                                parallel_stages.append(optimized_config["stages"][idx])
                        
                        # Create a new stage with parallel branches
                        new_stage = {
                            "name": f"parallel_{stages[0]}_{stages[1]}",
                            "parallel": parallel_stages
                        }
                        
                        # Replace the sequential stages with the parallel stage
                        optimized_config["stages"] = (
                            optimized_config["stages"][:stage_indices[0]] +
                            [new_stage] +
                            optimized_config["stages"][stage_indices[1] + 1:]
                        )
                        
                        applied_optimizations.append({
                            "type": "parallelization",
                            "stages": stages,
                            "description": f"Parallelized stages {', '.join(stages)}"
                        })
        
        # 2. Balance parallel stage workloads
        # This would require more detailed analysis of stage contents
        # For now, we just acknowledge the opportunity but don't implement it
        
        return optimized_config, applied_optimizations
    
    def _analyze_travis_ci_dependencies(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze dependencies between jobs in a Travis CI configuration.
        
        Args:
            pipeline_config (Dict[str, Any]): The Travis CI configuration
            
        Returns:
            Dict containing dependency analysis results
        """
        result = {
            "dependencies": {},
            "dependency_graph": {},
            "critical_path": [],
            "parallel_groups": [],
            "optimization_opportunities": []
        }
        
        # Travis CI has a different structure than other CI/CD platforms
        # It uses build stages to define dependencies between jobs
        
        # Extract jobs and stages
        jobs = []
        stages = []
        
        # Case 1: Jobs defined in 'jobs' section with 'stage' property
        if "jobs" in pipeline_config and "include" in pipeline_config["jobs"]:
            for job in pipeline_config["jobs"]["include"]:
                job_id = job.get("name", f"job_{len(jobs)}")
                stage = job.get("stage", "test")  # Default stage is "test"
                
                if stage not in stages:
                    stages.append(stage)
                
                jobs.append({
                    "id": job_id,
                    "stage": stage
                })
        
        # Case 2: Jobs defined in 'matrix' section
        elif "matrix" in pipeline_config and "include" in pipeline_config["matrix"]:
            for job in pipeline_config["matrix"]["include"]:
                job_id = job.get("name", f"job_{len(jobs)}")
                stage = job.get("stage", "test")  # Default stage is "test"
                
                if stage not in stages:
                    stages.append(stage)
                
                jobs.append({
                    "id": job_id,
                    "stage": stage
                })
        
        # Case 3: Simple configuration without explicit jobs
        else:
            # Create a single job for the default "test" stage
            job_id = "default_job"
            stage = "test"
            
            if stage not in stages:
                stages.append(stage)
            
            jobs.append({
                "id": job_id,
                "stage": stage
            })
        
        # Extract stages from 'stages' section if present
        if "stages" in pipeline_config:
            stages = pipeline_config["stages"]
        
        # Build dependency graph based on stage order
        # In Travis CI, stages run sequentially, and jobs within a stage run in parallel
        for job in jobs:
            job_id = job["id"]
            job_stage = job["stage"]
            stage_index = stages.index(job_stage) if job_stage in stages else -1
            
            # Jobs depend on all jobs from the previous stage
            dependencies = []
            if stage_index > 0:
                prev_stage = stages[stage_index - 1]
                prev_stage_jobs = [j["id"] for j in jobs if j["stage"] == prev_stage]
                dependencies = prev_stage_jobs
            
            result["dependencies"][job_id] = dependencies
            result["dependency_graph"][job_id] = {
                "dependencies": dependencies,
                "dependents": [],
                "stage": job_stage,
                "stage_index": stage_index
            }
        
        # Populate dependents
        for job_id, deps in result["dependencies"].items():
            for dep in deps:
                if dep in result["dependency_graph"]:
                    result["dependency_graph"][dep]["dependents"].append(job_id)
        
        # Find root jobs (no dependencies, first stage)
        first_stage = stages[0] if stages else None
        root_jobs = [job["id"] for job in jobs if job["stage"] == first_stage]
        result["root_jobs"] = root_jobs
        
        # Find leaf jobs (no dependents, last stage)
        last_stage = stages[-1] if stages else None
        leaf_jobs = [job["id"] for job in jobs if job["stage"] == last_stage]
        result["leaf_jobs"] = leaf_jobs
        
        # Identify parallel groups (jobs in the same stage)
        parallel_groups = []
        for stage in stages:
            stage_jobs = [job["id"] for job in jobs if job["stage"] == stage]
            if stage_jobs:
                parallel_groups.append(stage_jobs)
        
        result["parallel_groups"] = parallel_groups
        
        # Find critical path (in Travis CI, this is typically one job from each stage)
        critical_path = []
        for stage in stages:
            stage_jobs = [job["id"] for job in jobs if job["stage"] == stage]
            if stage_jobs:
                # For simplicity, just take the first job in each stage
                critical_path.append(stage_jobs[0])
        
        result["critical_path"] = critical_path
        
        # Identify optimization opportunities
        
        # 1. Unnecessary stage dependencies
        # In Travis CI, stages run sequentially, but not all stages may need to depend on the previous stage
        for stage_index in range(1, len(stages)):
            stage = stages[stage_index]
            prev_stage = stages[stage_index - 1]
            
            stage_jobs = [job["id"] for job in jobs if job["stage"] == stage]
            prev_stage_jobs = [job["id"] for job in jobs if job["stage"] == prev_stage]
            
            # Check if all jobs in this stage depend on all jobs in the previous stage
            # This might be unnecessary and could be optimized
            if stage_jobs and prev_stage_jobs and len(prev_stage_jobs) > 1:
                result["optimization_opportunities"].append({
                    "type": "stage_dependency",
                    "stage": stage,
                    "previous_stage": prev_stage,
                    "description": f"Stage '{stage}' depends on all jobs from previous stage '{prev_stage}'. Consider using selective dependencies."
                })
        
        # 2. Parallel execution opportunities
        for stage in stages:
            stage_jobs = [job["id"] for job in jobs if job["stage"] == stage]
            if len(stage_jobs) > 1:
                result["optimization_opportunities"].append({
                    "type": "parallel_execution",
                    "stage": stage,
                    "jobs": stage_jobs,
                    "description": f"Stage '{stage}' has {len(stage_jobs)} jobs that run in parallel"
                })
        
        # 3. Build matrix optimization
        # Check if the configuration could benefit from using build matrix instead of explicit jobs
        if "jobs" in pipeline_config and "include" in pipeline_config["jobs"]:
            jobs_list = pipeline_config["jobs"]["include"]
            if len(jobs_list) > 2:
                # Look for patterns in job configurations that could be expressed as a matrix
                # This is a simplified check - in a real implementation, you would analyze job properties
                result["optimization_opportunities"].append({
                    "type": "build_matrix",
                    "job_count": len(jobs_list),
                    "description": f"Configuration has {len(jobs_list)} explicit jobs. Consider using build matrix for more efficient configuration."
                })
        
        return result
    
    def _optimize_travis_ci_dependencies(self, pipeline_config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Optimize dependencies between jobs in a Travis CI configuration.
        
        Args:
            pipeline_config (Dict[str, Any]): The Travis CI configuration
            
        Returns:
            Tuple containing:
            - The optimized pipeline configuration
            - List of applied optimizations
        """
        optimized_config = copy.deepcopy(pipeline_config)
        applied_optimizations = []
        
        # Analyze dependencies
        analysis = self._analyze_travis_ci_dependencies(pipeline_config)
        
        # Apply optimizations based on analysis
        
        # 1. Convert explicit jobs to build matrix where possible
        for opportunity in analysis.get("optimization_opportunities", []):
            if opportunity["type"] == "build_matrix" and "jobs" in optimized_config and "include" in optimized_config["jobs"]:
                jobs_list = optimized_config["jobs"]["include"]
                
                # Look for common properties across jobs that could be expressed as matrix variables
                # This is a simplified implementation - in a real scenario, you would analyze job properties more thoroughly
                
                # Example: If jobs differ only by environment variables, convert to matrix
                env_vars = {}
                common_props = {}
                
                # Extract common properties and environment variables
                for job in jobs_list:
                    for key, value in job.items():
                        if key == "env":
                            # Parse environment variables
                            if isinstance(value, str):
                                # Single env var
                                var_name = value.split("=")[0] if "=" in value else value
                                if var_name not in env_vars:
                                    env_vars[var_name] = []
                                env_vars[var_name].append(value)
                            elif isinstance(value, list):
                                # Multiple env vars
                                for env in value:
                                    var_name = env.split("=")[0] if "=" in env else env
                                    if var_name not in env_vars:
                                        env_vars[var_name] = []
                                    env_vars[var_name].append(env)
                        else:
                            # Track common properties
                            if key not in common_props:
                                common_props[key] = []
                            if value not in common_props[key]:
                                common_props[key].append(value)
                
                # Identify properties that could be used for matrix expansion
                matrix_props = {}
                for key, values in common_props.items():
                    if len(values) > 1 and len(values) < len(jobs_list):
                        matrix_props[key] = values
                
                # If we found properties for matrix expansion, create a matrix configuration
                if matrix_props:
                    # Create matrix configuration
                    matrix = {}
                    for key, values in matrix_props.items():
                        matrix[key] = values
                    
                    # Create common job configuration
                    common_job = {}
                    for key, values in common_props.items():
                        if len(values) == 1:
                            common_job[key] = values[0]
                    
                    # Update configuration with matrix
                    if "matrix" not in optimized_config:
                        optimized_config["matrix"] = {}
                    
                    optimized_config["matrix"]["include"] = [common_job]
                    
                    # Add matrix expansion
                    for key, values in matrix_props.items():
                        if key not in optimized_config["matrix"]:
                            optimized_config["matrix"][key] = values
                    
                    # Remove original jobs section if it's now empty
                    if len(optimized_config["jobs"]["include"]) == 0:
                        del optimized_config["jobs"]
                    
                    applied_optimizations.append({
                        "type": "build_matrix_optimization",
                        "properties": list(matrix_props.keys()),
                        "description": f"Converted explicit jobs to build matrix using properties: {', '.join(matrix_props.keys())}"
                    })
        
        # 2. Optimize stage dependencies
        # Travis CI doesn't support selective stage dependencies, so we can't optimize this directly
        # We could suggest restructuring stages, but that would require more complex changes
        
        return optimized_config, applied_optimizations
    
    def _analyze_bitbucket_pipelines_dependencies(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze dependencies between steps in a Bitbucket Pipelines configuration.
        
        Args:
            pipeline_config (Dict[str, Any]): The Bitbucket Pipelines configuration
            
        Returns:
            Dict containing dependency analysis results
        """
        result = {
            "dependencies": {},
            "dependency_graph": {},
            "critical_path": [],
            "parallel_groups": [],
            "optimization_opportunities": []
        }
        
        # Bitbucket Pipelines has a different structure than other CI/CD platforms
        # It uses pipelines with steps, and steps can have parallel steps
        
        # Extract pipelines and steps
        pipelines = pipeline_config.get("pipelines", {})
        
        # Process default pipeline
        default_steps = pipelines.get("default", [])
        
        # Process branch-specific pipelines
        branches = pipelines.get("branches", {})
        
        # Process pull request pipelines
        pull_requests = pipelines.get("pull-requests", {})
        
        # Process custom pipelines
        custom = pipelines.get("custom", {})
        
        # Build dependency graph
        step_counter = 0
        
        # Helper function to process steps
        def process_steps(steps, pipeline_name):
            nonlocal step_counter
            
            step_ids = []
            
            for step_index, step in enumerate(steps):
                # Generate a unique ID for this step
                step_id = f"{pipeline_name}_step_{step_index}"
                step_ids.append(step_id)
                
                # Check if this is a parallel step
                if "parallel" in step:
                    parallel_steps = step["parallel"]
                    parallel_step_ids = []
                    
                    for parallel_index, parallel_step in enumerate(parallel_steps):
                        parallel_step_id = f"{step_id}_parallel_{parallel_index}"
                        parallel_step_ids.append(parallel_step_id)
                        
                        # Parallel steps depend on the previous sequential step
                        dependencies = []
                        if step_index > 0:
                            dependencies = [step_ids[step_index - 1]]
                        
                        result["dependencies"][parallel_step_id] = dependencies
                        result["dependency_graph"][parallel_step_id] = {
                            "dependencies": dependencies,
                            "dependents": [],
                            "pipeline": pipeline_name,
                            "step_index": step_index,
                            "parallel": True
                        }
                    
                    # Add a virtual "end of parallel" step that depends on all parallel steps
                    end_parallel_id = f"{step_id}_end_parallel"
                    
                    result["dependencies"][end_parallel_id] = parallel_step_ids
                    result["dependency_graph"][end_parallel_id] = {
                        "dependencies": parallel_step_ids,
                        "dependents": [],
                        "pipeline": pipeline_name,
                        "step_index": step_index,
                        "virtual": True
                    }
                    
                    # Update step_id to the end_parallel_id for dependency tracking
                    step_ids[step_index] = end_parallel_id
                else:
                    # Regular sequential step
                    dependencies = []
                    if step_index > 0:
                        dependencies = [step_ids[step_index - 1]]
                    
                    result["dependencies"][step_id] = dependencies
                    result["dependency_graph"][step_id] = {
                        "dependencies": dependencies,
                        "dependents": [],
                        "pipeline": pipeline_name,
                        "step_index": step_index,
                        "parallel": False
                    }
            
            return step_ids
        
        # Process all pipelines
        all_steps = []
        
        # Process default pipeline
        if default_steps:
            default_step_ids = process_steps(default_steps, "default")
            all_steps.extend(default_step_ids)
        
        # Process branch-specific pipelines
        for branch, steps in branches.items():
            branch_step_ids = process_steps(steps, f"branch_{branch}")
            all_steps.extend(branch_step_ids)
        
        # Process pull request pipelines
        for pr, steps in pull_requests.items():
            pr_step_ids = process_steps(steps, f"pr_{pr}")
            all_steps.extend(pr_step_ids)
        
        # Process custom pipelines
        for custom_name, steps in custom.items():
            custom_step_ids = process_steps(steps, f"custom_{custom_name}")
            all_steps.extend(custom_step_ids)
        
        # Populate dependents
        for step_id, deps in result["dependencies"].items():
            for dep in deps:
                if dep in result["dependency_graph"]:
                    result["dependency_graph"][dep]["dependents"].append(step_id)
        
        # Find root steps (no dependencies)
        root_steps = [step_id for step_id, deps in result["dependencies"].items() if not deps]
        result["root_jobs"] = root_steps  # Using "root_jobs" for consistency with other platforms
        
        # Find leaf steps (no dependents)
        leaf_steps = [step_id for step_id, info in result["dependency_graph"].items() if not info["dependents"]]
        result["leaf_jobs"] = leaf_steps  # Using "leaf_jobs" for consistency with other platforms
        
        # Identify parallel groups (steps that can run in parallel)
        parallel_groups = []
        
        for step_id, info in result["dependency_graph"].items():
            if info.get("parallel", False):
                # Find all parallel steps with the same parent
                step_index = info["step_index"]
                pipeline = info["pipeline"]
                
                parallel_group = [
                    s_id for s_id, s_info in result["dependency_graph"].items()
                    if s_info.get("parallel", False) and s_info["step_index"] == step_index and s_info["pipeline"] == pipeline
                ]
                
                if parallel_group and parallel_group not in parallel_groups:
                    parallel_groups.append(parallel_group)
        
        result["parallel_groups"] = parallel_groups
        
        # Find critical path (longest path from root to leaf)
        # For simplicity, just use the default pipeline's steps
        if default_steps:
            critical_path = []
            for step_index, step in enumerate(default_steps):
                if "parallel" in step:
                    # For parallel steps, add the first parallel step to the critical path
                    # In a real implementation, you would calculate durations and find the longest path
                    critical_path.append(f"default_step_{step_index}_parallel_0")
                else:
                    critical_path.append(f"default_step_{step_index}")
            
            result["critical_path"] = critical_path
        
        # Identify optimization opportunities
        
        # 1. Sequential steps that could be parallelized
        for pipeline_name in ["default"] + [f"branch_{branch}" for branch in branches.keys()]:
            pipeline_steps = [
                step_id for step_id, info in result["dependency_graph"].items()
                if info["pipeline"] == pipeline_name and not info.get("parallel", False) and not info.get("virtual", False)
            ]
            
            # Group steps by index
            steps_by_index = {}
            for step_id in pipeline_steps:
                info = result["dependency_graph"][step_id]
                step_index = info["step_index"]
                if step_index not in steps_by_index:
                    steps_by_index[step_index] = []
                steps_by_index[step_index].append(step_id)
            
            # Look for consecutive steps that could be parallelized
            for i in range(len(steps_by_index) - 1):
                if i in steps_by_index and i + 1 in steps_by_index:
                    current_steps = steps_by_index[i]
                    next_steps = steps_by_index[i + 1]
                    
                    if len(current_steps) == 1 and len(next_steps) == 1:
                        # Check if these steps have independent operations
                        # This is a simplified check - in a real implementation, you would analyze the step contents
                        result["optimization_opportunities"].append({
                            "type": "potential_parallelization",
                            "steps": [current_steps[0], next_steps[0]],
                            "description": f"Steps '{current_steps[0]}' and '{next_steps[0]}' might be candidates for parallelization"
                        })
        
        # 2. Steps with long execution times
        # In a real implementation, you would analyze step execution times
        # For simplicity, just flag steps with many commands
        for step_id, info in result["dependency_graph"].items():
            if not info.get("virtual", False):
                # Find the step in the pipeline configuration
                pipeline_name = info["pipeline"]
                step_index = info["step_index"]
                
                # This is a simplified check - in a real implementation, you would analyze step contents more thoroughly
                result["optimization_opportunities"].append({
                    "type": "step_optimization",
                    "step_id": step_id,
                    "description": f"Step '{step_id}' might benefit from optimization (caching, script optimization, etc.)"
                })
        
        return result
    
    def _optimize_bitbucket_pipelines_dependencies(self, pipeline_config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Optimize dependencies between steps in a Bitbucket Pipelines configuration.
        
        Args:
            pipeline_config (Dict[str, Any]): The Bitbucket Pipelines configuration
            
        Returns:
            Tuple containing:
            - The optimized pipeline configuration
            - List of applied optimizations
        """
        optimized_config = copy.deepcopy(pipeline_config)
        applied_optimizations = []
        
        # Analyze dependencies
        analysis = self._analyze_bitbucket_pipelines_dependencies(pipeline_config)
        
        # Apply optimizations based on analysis
        
        # 1. Parallelize sequential steps that could be run in parallel
        for opportunity in analysis.get("optimization_opportunities", []):
            if opportunity["type"] == "potential_parallelization":
                steps = opportunity["steps"]
                
                if len(steps) >= 2:
                    # Extract pipeline name and step indices
                    step1_info = analysis["dependency_graph"].get(steps[0], {})
                    step2_info = analysis["dependency_graph"].get(steps[1], {})
                    
                    pipeline_name = step1_info.get("pipeline")
                    step1_index = step1_info.get("step_index")
                    step2_index = step2_info.get("step_index")
                    
                    if pipeline_name and step1_index is not None and step2_index is not None:
                        # Find the steps in the pipeline configuration
                        if pipeline_name == "default" and "pipelines" in optimized_config and "default" in optimized_config["pipelines"]:
                            steps_list = optimized_config["pipelines"]["default"]
                            
                            if step1_index < len(steps_list) and step2_index < len(steps_list) and step2_index == step1_index + 1:
                                # Create a new parallel step to replace the sequential steps
                                step1 = steps_list[step1_index]
                                step2 = steps_list[step2_index]
                                
                                # Create a new step with parallel branches
                                new_step = {
                                    "parallel": [
                                        step1,
                                        step2
                                    ]
                                }
                                
                                # Replace the sequential steps with the parallel step
                                optimized_config["pipelines"]["default"] = (
                                    steps_list[:step1_index] +
                                    [new_step] +
                                    steps_list[step2_index + 1:]
                                )
                                
                                applied_optimizations.append({
                                    "type": "parallelization",
                                    "steps": steps,
                                    "description": f"Parallelized steps {', '.join(steps)}"
                                })
                        
                        # Similar logic for branch-specific pipelines
                        elif pipeline_name.startswith("branch_") and "pipelines" in optimized_config and "branches" in optimized_config["pipelines"]:
                            branch_name = pipeline_name[len("branch_"):]
                            if branch_name in optimized_config["pipelines"]["branches"]:
                                steps_list = optimized_config["pipelines"]["branches"][branch_name]
                                
                                if step1_index < len(steps_list) and step2_index < len(steps_list) and step2_index == step1_index + 1:
                                    # Create a new parallel step to replace the sequential steps
                                    step1 = steps_list[step1_index]
                                    step2 = steps_list[step2_index]
                                    
                                    # Create a new step with parallel branches
                                    new_step = {
                                        "parallel": [
                                            step1,
                                            step2
                                        ]
                                    }
                                    
                                    # Replace the sequential steps with the parallel step
                                    optimized_config["pipelines"]["branches"][branch_name] = (
                                        steps_list[:step1_index] +
                                        [new_step] +
                                        steps_list[step2_index + 1:]
                                    )
                                    
                                    applied_optimizations.append({
                                        "type": "parallelization",
                                        "steps": steps,
                                        "description": f"Parallelized steps {', '.join(steps)}"
                                    })
        
        # 2. Optimize step execution
        # This would require more detailed analysis of step contents
        # For now, we just acknowledge the opportunity but don't implement it
        
        return optimized_config, applied_optimizations
    
    def _analyze_aws_codebuild_dependencies(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze dependencies between phases in an AWS CodeBuild buildspec.
        
        Args:
            pipeline_config (Dict[str, Any]): The AWS CodeBuild buildspec
            
        Returns:
            Dict containing dependency analysis results
        """
        result = {
            "dependencies": {},
            "dependency_graph": {},
            "critical_path": [],
            "parallel_groups": [],
            "optimization_opportunities": []
        }
        
        # AWS CodeBuild buildspec has a different structure than other CI/CD platforms
        # It uses phases that run sequentially: install, pre_build, build, post_build
        
        # Standard phase order in AWS CodeBuild
        standard_phases = ["install", "pre_build", "build", "post_build"]
        
        # Extract phases from the buildspec
        phases = {}
        if "phases" in pipeline_config:
            for phase_name, phase_config in pipeline_config["phases"].items():
                if phase_name in standard_phases:
                    phases[phase_name] = phase_config
        
        # Build dependency graph based on phase order
        # In AWS CodeBuild, phases run sequentially in a predefined order
        for phase_index, phase_name in enumerate(standard_phases):
            if phase_name in phases:
                # Phases depend on the previous phase
                dependencies = []
                if phase_index > 0:
                    prev_phase = standard_phases[phase_index - 1]
                    if prev_phase in phases:
                        dependencies = [prev_phase]
                
                result["dependencies"][phase_name] = dependencies
                result["dependency_graph"][phase_name] = {
                    "dependencies": dependencies,
                    "dependents": [],
                    "phase_index": phase_index
                }
        
        # Populate dependents
        for phase_name, deps in result["dependencies"].items():
            for dep in deps:
                if dep in result["dependency_graph"]:
                    result["dependency_graph"][dep]["dependents"].append(phase_name)
        
        # Find root phases (no dependencies)
        root_phases = [phase_name for phase_name, deps in result["dependencies"].items() if not deps]
        result["root_jobs"] = root_phases  # Using "root_jobs" for consistency with other platforms
        
        # Find leaf phases (no dependents)
        leaf_phases = [phase_name for phase_name, info in result["dependency_graph"].items() if not info["dependents"]]
        result["leaf_jobs"] = leaf_phases  # Using "leaf_jobs" for consistency with other platforms
        
        # In AWS CodeBuild, phases run sequentially, so each phase is its own "parallel group"
        result["parallel_groups"] = [[phase_name] for phase_name in result["dependencies"].keys()]
        
        # Find critical path (in AWS CodeBuild, this is simply the sequence of phases)
        critical_path = [phase_name for phase_name in standard_phases if phase_name in phases]
        result["critical_path"] = critical_path
        
        # Identify optimization opportunities
        
        # 1. Unnecessary phases
        # Check if any phases have minimal or no commands
        for phase_name, phase_config in phases.items():
            commands = phase_config.get("commands", [])
            if len(commands) == 0:
                result["optimization_opportunities"].append({
                    "type": "empty_phase",
                    "phase": phase_name,
                    "description": f"Phase '{phase_name}' has no commands and could be removed."
                })
            elif len(commands) == 1 and commands[0].strip() == "":
                result["optimization_opportunities"].append({
                    "type": "empty_phase",
                    "phase": phase_name,
                    "description": f"Phase '{phase_name}' has an empty command and could be removed."
                })
        
        # 2. Command optimization
        # Check for commands that could be optimized
        for phase_name, phase_config in phases.items():
            commands = phase_config.get("commands", [])
            
            # Check for multiple package installation commands that could be combined
            install_commands = [cmd for cmd in commands if "install" in cmd.lower() or "pip" in cmd.lower() or "npm" in cmd.lower()]
            if len(install_commands) > 1:
                result["optimization_opportunities"].append({
                    "type": "command_optimization",
                    "phase": phase_name,
                    "commands": install_commands,
                    "description": f"Multiple installation commands in phase '{phase_name}' could be combined for efficiency."
                })
            
            # Check for commands that could benefit from caching
            cache_candidates = [
                cmd for cmd in commands 
                if any(keyword in cmd.lower() for keyword in ["pip", "npm", "mvn", "gradle", "bundler", "yarn"])
            ]
            if cache_candidates:
                result["optimization_opportunities"].append({
                    "type": "caching_opportunity",
                    "phase": phase_name,
                    "commands": cache_candidates,
                    "description": f"Commands in phase '{phase_name}' could benefit from dependency caching."
                })
        
        # 3. Phase consolidation
        # Check if adjacent phases could be consolidated
        for i in range(len(standard_phases) - 1):
            phase1 = standard_phases[i]
            phase2 = standard_phases[i + 1]
            
            if phase1 in phases and phase2 in phases:
                commands1 = phases[phase1].get("commands", [])
                commands2 = phases[phase2].get("commands", [])
                
                # If both phases have few commands, they might be candidates for consolidation
                if 0 < len(commands1) <= 2 and 0 < len(commands2) <= 2:
                    result["optimization_opportunities"].append({
                        "type": "phase_consolidation",
                        "phases": [phase1, phase2],
                        "description": f"Phases '{phase1}' and '{phase2}' have few commands and could potentially be consolidated."
                    })
        
        return result
    
    def _optimize_aws_codebuild_dependencies(self, pipeline_config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Optimize dependencies between phases in an AWS CodeBuild buildspec.
        
        Args:
            pipeline_config (Dict[str, Any]): The AWS CodeBuild buildspec
            
        Returns:
            Tuple containing:
            - The optimized pipeline configuration
            - List of applied optimizations
        """
        optimized_config = copy.deepcopy(pipeline_config)
        applied_optimizations = []
        
        # Analyze dependencies
        analysis = self._analyze_aws_codebuild_dependencies(pipeline_config)
        
        # Apply optimizations based on analysis
        
        # 1. Remove empty phases
        for opportunity in analysis.get("optimization_opportunities", []):
            if opportunity["type"] == "empty_phase":
                phase_name = opportunity["phase"]
                
                if "phases" in optimized_config and phase_name in optimized_config["phases"]:
                    del optimized_config["phases"][phase_name]
                    
                    applied_optimizations.append({
                        "type": "empty_phase_removal",
                        "phase": phase_name,
                        "description": f"Removed empty phase '{phase_name}'"
                    })
        
        # 2. Combine multiple installation commands
        for opportunity in analysis.get("optimization_opportunities", []):
            if opportunity["type"] == "command_optimization":
                phase_name = opportunity["phase"]
                commands = opportunity["commands"]
                
                if "phases" in optimized_config and phase_name in optimized_config["phases"]:
                    phase_config = optimized_config["phases"][phase_name]
                    
                    if "commands" in phase_config:
                        # Get all commands
                        all_commands = phase_config["commands"]
                        
                        # Filter out the installation commands
                        non_install_commands = [cmd for cmd in all_commands if cmd not in commands]
                        
                        # Create a combined installation command
                        if all(("pip" in cmd) for cmd in commands):
                            # Combine pip install commands
                            packages = []
                            for cmd in commands:
                                # Extract package names from pip install commands
                                match = re.search(r'pip\s+install\s+(.*)', cmd)
                                if match:
                                    packages.append(match.group(1))
                            
                            if packages:
                                combined_command = f"pip install {' '.join(packages)}"
                                new_commands = [combined_command] + non_install_commands
                                optimized_config["phases"][phase_name]["commands"] = new_commands
                                
                                applied_optimizations.append({
                                    "type": "command_optimization",
                                    "phase": phase_name,
                                    "original_commands": commands,
                                    "optimized_command": combined_command,
                                    "description": f"Combined multiple pip install commands in phase '{phase_name}'"
                                })
                        
                        elif all(("npm" in cmd) for cmd in commands):
                            # Combine npm install commands
                            packages = []
                            for cmd in commands:
                                # Extract package names from npm install commands
                                match = re.search(r'npm\s+install\s+(.*)', cmd)
                                if match:
                                    packages.append(match.group(1))
                            
                            if packages:
                                combined_command = f"npm install {' '.join(packages)}"
                                new_commands = [combined_command] + non_install_commands
                                optimized_config["phases"][phase_name]["commands"] = new_commands
                                
                                applied_optimizations.append({
                                    "type": "command_optimization",
                                    "phase": phase_name,
                                    "original_commands": commands,
                                    "optimized_command": combined_command,
                                    "description": f"Combined multiple npm install commands in phase '{phase_name}'"
                                })
        
        # 3. Add caching configuration
        for opportunity in analysis.get("optimization_opportunities", []):
            if opportunity["type"] == "caching_opportunity":
                # Add cache configuration if not already present
                if "cache" not in optimized_config:
                    # Determine the type of caching needed based on commands
                    commands = opportunity["commands"]
                    
                    if any("pip" in cmd for cmd in commands):
                        # Add Python dependency caching
                        optimized_config["cache"] = {
                            "paths": [
                                "/root/.cache/pip"
                            ]
                        }
                        
                        applied_optimizations.append({
                            "type": "caching_added",
                            "cache_type": "pip",
                            "description": "Added pip dependency caching configuration"
                        })
                    
                    elif any("npm" in cmd for cmd in commands):
                        # Add Node.js dependency caching
                        optimized_config["cache"] = {
                            "paths": [
                                "/root/.npm"
                            ]
                        }
                        
                        applied_optimizations.append({
                            "type": "caching_added",
                            "cache_type": "npm",
                            "description": "Added npm dependency caching configuration"
                        })
                    
                    elif any("mvn" in cmd for cmd in commands):
                        # Add Maven dependency caching
                        optimized_config["cache"] = {
                            "paths": [
                                "/root/.m2/**/*"
                            ]
                        }
                        
                        applied_optimizations.append({
                            "type": "caching_added",
                            "cache_type": "maven",
                            "description": "Added Maven dependency caching configuration"
                        })
                    
                    elif any("gradle" in cmd for cmd in commands):
                        # Add Gradle dependency caching
                        optimized_config["cache"] = {
                            "paths": [
                                "/root/.gradle/caches/**/*",
                                "/root/.gradle/wrapper/**/*"
                            ]
                        }
                        
                        applied_optimizations.append({
                            "type": "caching_added",
                            "cache_type": "gradle",
                            "description": "Added Gradle dependency caching configuration"
                        })
        
        # 4. Consolidate phases
        for opportunity in analysis.get("optimization_opportunities", []):
            if opportunity["type"] == "phase_consolidation":
                phases = opportunity["phases"]
                
                if len(phases) == 2 and "phases" in optimized_config:
                    phase1, phase2 = phases
                    
                    if phase1 in optimized_config["phases"] and phase2 in optimized_config["phases"]:
                        # Get commands from both phases
                        commands1 = optimized_config["phases"][phase1].get("commands", [])
                        commands2 = optimized_config["phases"][phase2].get("commands", [])
                        
                        # Combine commands in the first phase
                        optimized_config["phases"][phase1]["commands"] = commands1 + commands2
                        
                        # Remove the second phase
                        del optimized_config["phases"][phase2]
                        
                        applied_optimizations.append({
                            "type": "phase_consolidation",
                            "phases": phases,
                            "description": f"Consolidated phases '{phase1}' and '{phase2}' into '{phase1}'"
                        })
        
        return optimized_config, applied_optimizations
