import pytest
from unittest.mock import Mock, patch
import copy
from services.dependency_analyzer import DependencyAnalyzerService

# Sample pipeline configurations for testing
SAMPLE_PIPELINES = {
    "github-actions": {
        "name": "Test Pipeline",
        "on": {
            "push": {
                "branches": ["main"]
            }
        },
        "jobs": {
            "build": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {
                        "uses": "actions/checkout@v3"
                    },
                    {
                        "name": "Build",
                        "run": "npm run build"
                    }
                ]
            },
            "test": {
                "runs-on": "ubuntu-latest",
                "needs": ["build"],
                "steps": [
                    {
                        "uses": "actions/checkout@v3"
                    },
                    {
                        "name": "Test",
                        "run": "npm test"
                    }
                ]
            },
            "lint": {
                "runs-on": "ubuntu-latest",
                "needs": ["build"],
                "steps": [
                    {
                        "uses": "actions/checkout@v3"
                    },
                    {
                        "name": "Lint",
                        "run": "npm run lint"
                    }
                ]
            },
            "deploy": {
                "runs-on": "ubuntu-latest",
                "needs": ["test", "lint", "build"],  # Redundant dependency on build
                "steps": [
                    {
                        "uses": "actions/checkout@v3"
                    },
                    {
                        "name": "Deploy",
                        "run": "npm run deploy"
                    }
                ]
            }
        }
    },
    "gitlab-ci": {
        "stages": ["build", "test", "deploy"],
        "build_job": {
            "stage": "build",
            "script": ["npm run build"]
        },
        "test_job": {
            "stage": "test",
            "script": ["npm test"],
            "needs": ["build_job"]
        },
        "lint_job": {
            "stage": "test",
            "script": ["npm run lint"],
            "needs": ["build_job"]
        },
        "deploy_job": {
            "stage": "deploy",
            "script": ["npm run deploy"],
            "needs": ["test_job", "lint_job", "build_job"]  # Redundant dependency on build_job
        }
    }
}

@pytest.fixture
def analyzer():
    return DependencyAnalyzerService()

def test_analyze_github_actions_dependencies(analyzer):
    """Test analyzing dependencies in a GitHub Actions workflow."""
    pipeline_config = copy.deepcopy(SAMPLE_PIPELINES["github-actions"])
    analysis = analyzer._analyze_github_actions_dependencies(pipeline_config)
    
    # Check that the analysis contains the expected keys
    assert "dependencies" in analysis
    assert "dependency_graph" in analysis
    assert "root_jobs" in analysis
    assert "leaf_jobs" in analysis
    assert "parallel_groups" in analysis
    assert "critical_path" in analysis
    assert "optimization_opportunities" in analysis
    
    # Check dependencies
    assert analysis["dependencies"]["build"] == []
    assert analysis["dependencies"]["test"] == ["build"]
    assert analysis["dependencies"]["lint"] == ["build"]
    assert analysis["dependencies"]["deploy"] == ["test", "lint", "build"]
    
    # Check root and leaf jobs
    assert "build" in analysis["root_jobs"]
    assert "deploy" in analysis["leaf_jobs"]
    
    # Check optimization opportunities
    redundant_deps = [opp for opp in analysis["optimization_opportunities"] 
                     if opp["type"] == "redundant_dependency"]
    assert len(redundant_deps) > 0
    assert redundant_deps[0]["job_id"] == "deploy"
    assert "build" in redundant_deps[0]["redundant_dependencies"]

def test_analyze_gitlab_ci_dependencies(analyzer):
    """Test analyzing dependencies in a GitLab CI pipeline."""
    pipeline_config = copy.deepcopy(SAMPLE_PIPELINES["gitlab-ci"])
    analysis = analyzer._analyze_gitlab_ci_dependencies(pipeline_config)
    
    # Check that the analysis contains the expected keys
    assert "dependencies" in analysis
    assert "dependency_graph" in analysis
    assert "root_jobs" in analysis
    assert "leaf_jobs" in analysis
    assert "parallel_groups" in analysis
    assert "optimization_opportunities" in analysis
    
    # Check dependencies
    assert analysis["dependencies"]["build_job"] == []
    assert analysis["dependencies"]["test_job"] == ["build_job"]
    assert analysis["dependencies"]["lint_job"] == ["build_job"]
    assert analysis["dependencies"]["deploy_job"] == ["test_job", "lint_job", "build_job"]
    
    # Check root and leaf jobs
    assert "build_job" in analysis["root_jobs"]
    assert "deploy_job" in analysis["leaf_jobs"]
    
    # Check optimization opportunities
    redundant_deps = [opp for opp in analysis["optimization_opportunities"] 
                     if opp["type"] == "redundant_dependency"]
    assert len(redundant_deps) > 0
    assert redundant_deps[0]["job_id"] == "deploy_job"
    assert "build_job" in redundant_deps[0]["redundant_dependencies"]

def test_optimize_github_actions_dependencies(analyzer):
    """Test optimizing dependencies in a GitHub Actions workflow."""
    pipeline_config = copy.deepcopy(SAMPLE_PIPELINES["github-actions"])
    optimized_config, applied_optimizations = analyzer._optimize_github_actions_dependencies(pipeline_config)
    
    # Check that optimizations were applied
    assert len(applied_optimizations) > 0
    assert applied_optimizations[0]["type"] == "redundant_dependency_removal"
    assert applied_optimizations[0]["job_id"] == "deploy"
    assert "build" in applied_optimizations[0]["removed_dependencies"]
    
    # Check that the redundant dependency was removed
    assert "build" not in optimized_config["jobs"]["deploy"]["needs"]
    assert set(optimized_config["jobs"]["deploy"]["needs"]) == {"test", "lint"}

def test_optimize_gitlab_ci_dependencies(analyzer):
    """Test optimizing dependencies in a GitLab CI pipeline."""
    pipeline_config = copy.deepcopy(SAMPLE_PIPELINES["gitlab-ci"])
    optimized_config, applied_optimizations = analyzer._optimize_gitlab_ci_dependencies(pipeline_config)
    
    # Check that optimizations were applied
    assert len(applied_optimizations) > 0
    assert applied_optimizations[0]["type"] == "redundant_dependency_removal"
    assert applied_optimizations[0]["job_id"] == "deploy_job"
    assert "build_job" in applied_optimizations[0]["removed_dependencies"]
    
    # Check that the redundant dependency was removed
    assert "build_job" not in optimized_config["deploy_job"]["needs"]
    assert set(optimized_config["deploy_job"]["needs"]) == {"test_job", "lint_job"}

def test_analyze_dependencies(analyzer):
    """Test the analyze_dependencies method."""
    # Test GitHub Actions
    github_pipeline = copy.deepcopy(SAMPLE_PIPELINES["github-actions"])
    github_analysis = analyzer.analyze_dependencies("github-actions", github_pipeline)
    
    assert "dependencies" in github_analysis
    assert "optimization_opportunities" in github_analysis
    
    # Test GitLab CI
    gitlab_pipeline = copy.deepcopy(SAMPLE_PIPELINES["gitlab-ci"])
    gitlab_analysis = analyzer.analyze_dependencies("gitlab-ci", gitlab_pipeline)
    
    assert "dependencies" in gitlab_analysis
    assert "optimization_opportunities" in gitlab_analysis
    
    # Test unsupported platform
    unsupported_analysis = analyzer.analyze_dependencies("unsupported-platform", {})
    assert "error" in unsupported_analysis

def test_optimize_dependencies(analyzer):
    """Test the optimize_dependencies method."""
    # Test GitHub Actions
    github_pipeline = copy.deepcopy(SAMPLE_PIPELINES["github-actions"])
    optimized_github, applied_github = analyzer.optimize_dependencies("github-actions", github_pipeline)
    
    assert len(applied_github) > 0
    assert "build" not in optimized_github["jobs"]["deploy"]["needs"]
    
    # Test GitLab CI
    gitlab_pipeline = copy.deepcopy(SAMPLE_PIPELINES["gitlab-ci"])
    optimized_gitlab, applied_gitlab = analyzer.optimize_dependencies("gitlab-ci", gitlab_pipeline)
    
    assert len(applied_gitlab) > 0
    assert "build_job" not in optimized_gitlab["deploy_job"]["needs"]
    
    # Test unsupported platform
    optimized_unsupported, applied_unsupported = analyzer.optimize_dependencies("unsupported-platform", {})
    assert optimized_unsupported == {}
    assert applied_unsupported == []
