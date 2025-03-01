# AI Pipeline Generator

The AI Pipeline Generator is a service that uses natural language processing to automatically generate CI/CD pipeline configurations for various platforms.

## Features

- **Natural Language Processing**: Describe your pipeline requirements in plain English, and the service will generate the appropriate configuration.
- **Multi-Platform Support**: Generate pipeline configurations for multiple CI/CD platforms:
  - GitHub Actions
  - GitLab CI
  - Azure Pipelines
  - CircleCI
  - Jenkins
  - Travis CI
  - Bitbucket Pipelines
  - AWS CodeBuild
- **Platform-Specific Best Practices**: Automatically applies best practices for each supported platform.
- **Security Recommendations**: Incorporates security best practices specific to each platform.
- **Predefined Templates**: Choose from a library of predefined templates for common CI/CD workflows.
- **Template Customization**: Customize predefined templates with your own variables.
- **Hybrid Generation**: Use AI-generated pipelines or predefined templates based on your needs.
- **Pipeline Optimization**: Automatically optimize pipelines for performance, efficiency, and best practices:
  - Dependency caching for faster builds
  - Matrix builds for testing across multiple environments
  - Parallel job execution for reduced build times
  - Resource optimization for cost-effective CI/CD
  - Artifact management for efficient workflows
  - Dependency analysis for optimized job dependencies

## API Endpoints

### Health Check

```
GET /
```

Returns the service health status.

### Get Supported Platforms

```
GET /api/v1/platforms
```

Returns a list of all supported CI/CD platforms.

### Get Available Templates

```
GET /api/v1/templates/{platform}
```

Returns a list of available templates for a specific platform.

### Get Template Variables

```
GET /api/v1/templates/{platform}/{template_name}/variables
```

Returns the customizable variables for a specific template.

### Generate Pipeline

```
POST /api/v1/generate
```

Generate a CI/CD pipeline configuration based on a natural language description or using a predefined template.

#### Request Body

```json
{
  "description": "Run tests on push to main branch, build a Docker image, and deploy to production",
  "platform": "github-actions",
  "template_vars": {
    "node_version": "16",
    "docker_registry": "ghcr.io"
  },
  "template_name": "docker-build-push",
  "optimize": true,
  "optimizations": ["caching", "matrix-builds"]
}
```

- `description` (required): Natural language description of the desired pipeline
- `platform` (optional): Target CI/CD platform (default: "github-actions")
- `template_vars` (optional): Additional variables for pipeline customization
- `template_name` (optional): Name of the predefined template to use (if not provided, AI generation will be used)
- `optimize` (optional): Whether to optimize the generated pipeline (default: false)
- `optimizations` (optional): Specific optimizations to apply (if not provided, all recommended optimizations will be applied)

#### Response

When using AI generation:

```json
{
  "status": "success",
  "platform": "github-actions",
  "pipeline_config": {
    "name": "Build and Deploy",
    "on": {
      "push": {
        "branches": ["main"]
      }
    },
    "jobs": {
      "test": {
        "runs-on": "ubuntu-latest",
        "steps": [...]
      },
      "build": {
        "runs-on": "ubuntu-latest",
        "steps": [...]
      },
      "deploy": {
        "runs-on": "ubuntu-latest",
        "steps": [...]
      }
    }
  },
  "raw_content": "name: Build and Deploy\non:\n  push:\n    branches: [main]\n...",
  "metadata": {
    "source": "ai",
    "model": "gpt-4",
    "tokens_used": 1250
  }
}
```

When using a predefined template:

```json
{
  "status": "success",
  "platform": "github-actions",
  "pipeline_config": {
    "name": "Docker Build and Push",
    "on": {
      "push": {
        "branches": ["main"]
      }
    },
    "jobs": {
      "build": {
        "runs-on": "ubuntu-latest",
        "permissions": {
          "contents": "read",
          "packages": "write"
        },
        "steps": [...]
      }
    }
  },
  "raw_content": "name: Docker Build and Push\non:\n  push:\n    branches: [main]\n...",
  "template_used": "docker-build-push",
  "metadata": {
    "source": "template",
    "template_name": "docker-build-push",
    "description": "Run tests on push to main branch, build a Docker image, and deploy to production"
  }
}
```

## Configuration

The service can be configured using environment variables:

- `OPENAI_API_KEY`: OpenAI API key (required)
- `OPENAI_MODEL`: OpenAI model to use (default: "gpt-4")
- `ENVIRONMENT`: Environment (development, production, etc.)
- `DEBUG`: Enable debug mode (true/false)

## Development

### Prerequisites

- Python 3.9+
- FastAPI
- OpenAI API key

### Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your OpenAI API key
4. Run the service: `python main.py`

### Testing

Run tests with pytest:

```
pytest
```

### Optimize Pipeline

```
POST /api/v1/optimize
```

Optimize an existing pipeline configuration.

#### Request Body

```json
{
  "platform": "github-actions",
  "pipeline_config": {
    "name": "Build and Test",
    "on": {
      "push": {
        "branches": ["main"]
      }
    },
    "jobs": {
      "test": {
        "runs-on": "ubuntu-latest",
        "steps": [
          {
            "uses": "actions/checkout@v3"
          },
          {
            "name": "Set up Node.js",
            "uses": "actions/setup-node@v3",
            "with": {
              "node-version": "16"
            }
          },
          {
            "name": "Install dependencies",
            "run": "npm ci"
          },
          {
            "name": "Run tests",
            "run": "npm test"
          }
        ]
      }
    }
  },
  "optimizations": ["caching", "matrix-builds"]
}
```

- `platform` (required): Target CI/CD platform
- `pipeline_config` (required): Pipeline configuration to optimize
- `optimizations` (optional): Specific optimizations to apply (if not provided, all recommended optimizations will be applied)

#### Response

```json
{
  "status": "success",
  "platform": "github-actions",
  "pipeline_config": {
    "name": "Build and Test",
    "on": {
      "push": {
        "branches": ["main"]
      }
    },
    "jobs": {
      "test": {
        "runs-on": "ubuntu-latest",
        "strategy": {
          "matrix": {
            "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
            "node-version": ["14.x", "16.x", "18.x"]
          }
        },
        "steps": [
          {
            "uses": "actions/checkout@v3"
          },
          {
            "name": "Cache Node.js dependencies",
            "uses": "actions/cache@v3",
            "with": {
              "path": "~/.npm",
              "key": "${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}",
              "restore-keys": "${{ runner.os }}-node-"
            }
          },
          {
            "name": "Set up Node.js",
            "uses": "actions/setup-node@v3",
            "with": {
              "node-version": "16"
            }
          },
          {
            "name": "Install dependencies",
            "run": "npm ci"
          },
          {
            "name": "Run tests",
            "run": "npm test"
          }
        ]
      }
    }
  },
  "raw_content": "...",
  "optimizations": [
    {
      "name": "caching",
      "description": "Added Node.js dependency caching to job 'test'",
      "details": "Added caching step after checkout"
    },
    {
      "name": "matrix-builds",
      "description": "Added matrix build strategy to job 'test'",
      "details": "Added matrix configuration for multiple environments"
    }
  ],
  "metadata": {
    "source": "user",
    "optimized": true
  }
}
```

### Analyze Pipeline

```
POST /api/v1/analyze
```

Analyze a pipeline configuration and identify potential optimizations.

#### Request Body

```json
{
  "platform": "github-actions",
  "pipeline_config": {
    "name": "Build and Test",
    "on": {
      "push": {
        "branches": ["main"]
      }
    },
    "jobs": {
      "test": {
        "runs-on": "ubuntu-latest",
        "steps": [
          {
            "uses": "actions/checkout@v3"
          },
          {
            "name": "Set up Node.js",
            "uses": "actions/setup-node@v3",
            "with": {
              "node-version": "16"
            }
          },
          {
            "name": "Install dependencies",
            "run": "npm ci"
          },
          {
            "name": "Run tests",
            "run": "npm test"
          }
        ]
      }
    }
  }
}
```

- `platform` (required): Target CI/CD platform
- `pipeline_config` (required): Pipeline configuration to analyze

#### Response

```json
{
  "recommendations": [
    {
      "name": "caching",
      "description": "Add Node.js dependency caching to speed up builds",
      "applies_to": "node",
      "priority": "high",
      "job_id": "test"
    },
    {
      "name": "matrix-builds",
      "description": "Use matrix builds for testing across multiple environments",
      "applies_to": "testing",
      "priority": "medium",
      "job_id": "test"
    }
  ]
}
```

### Analyze Dependencies

```
POST /api/v1/analyze-dependencies
```

Analyze dependencies between jobs in a pipeline configuration and identify optimization opportunities.

#### Request Body

```json
{
  "platform": "github-actions",
  "pipeline_config": {
    "name": "Build and Test",
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
        "needs": ["test", "lint", "build"],
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
  }
}
```

- `platform` (required): Target CI/CD platform (supported platforms: github-actions, gitlab-ci, azure-pipelines, circle-ci, jenkins, travis-ci, bitbucket-pipelines, aws-codebuild)
- `pipeline_config` (required): Pipeline configuration to analyze

#### Response

```json
{
  "dependencies": {
    "build": [],
    "test": ["build"],
    "lint": ["build"],
    "deploy": ["test", "lint", "build"]
  },
  "dependency_graph": {
    "build": {
      "dependencies": [],
      "dependents": ["test", "lint", "deploy"]
    },
    "test": {
      "dependencies": ["build"],
      "dependents": ["deploy"]
    },
    "lint": {
      "dependencies": ["build"],
      "dependents": ["deploy"]
    },
    "deploy": {
      "dependencies": ["test", "lint", "build"],
      "dependents": []
    }
  },
  "critical_path": ["build", "test", "deploy"],
  "parallel_groups": [
    ["build"],
    ["test", "lint"],
    ["deploy"]
  ],
  "optimization_opportunities": [
    {
      "type": "redundant_dependency",
      "job_id": "deploy",
      "redundant_dependencies": ["build"],
      "description": "Job 'deploy' has redundant dependencies: build"
    }
  ]
}
```

### Optimize Dependencies

```
POST /api/v1/optimize-dependencies
```

Optimize dependencies between jobs in a pipeline configuration.

#### Request Body

```json
{
  "platform": "github-actions",
  "pipeline_config": {
    "name": "Build and Test",
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
        "needs": ["test", "lint", "build"],
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
  }
}
```

- `platform` (required): Target CI/CD platform (supported platforms: github-actions, gitlab-ci, azure-pipelines, circle-ci, jenkins, travis-ci, bitbucket-pipelines, aws-codebuild)
- `pipeline_config` (required): Pipeline configuration to optimize

#### Response

```json
{
  "status": "success",
  "platform": "github-actions",
  "pipeline_config": {
    "name": "Build and Test",
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
        "needs": ["test", "lint"],
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
  "raw_content": "...",
  "applied_optimizations": [
    {
      "type": "redundant_dependency_removal",
      "job_id": "deploy",
      "removed_dependencies": ["build"],
      "description": "Removed redundant dependencies from job 'deploy': build"
    }
  ],
  "metadata": {
    "source": "user",
    "optimized": true
  }
}
```

### Get Optimization Strategies

```
GET /api/v1/optimization-strategies/{platform}
```

Get available optimization strategies for a specific platform.

#### Response

```json
{
  "strategies": [
    {
      "name": "caching",
      "description": "Add dependency caching to speed up builds",
      "applies_to": ["node", "python", "java", "ruby", "go"],
      "priority": "high"
    },
    {
      "name": "matrix-builds",
      "description": "Use matrix builds for testing across multiple environments",
      "applies_to": ["testing", "multi-environment"],
      "priority": "medium"
    },
    {
      "name": "concurrent-jobs",
      "description": "Run independent jobs concurrently",
      "applies_to": ["build", "test", "lint"],
      "priority": "medium"
    }
  ]
}
```

## Architecture

The AI Pipeline Generator consists of the following components:

- **FastAPI Application**: Handles HTTP requests and responses
- **Pipeline Generator Service**: Core service that generates pipeline configurations
- **Pipeline Optimizer Service**: Service that analyzes and optimizes pipeline configurations
- **Dependency Analyzer Service**: Service that analyzes and optimizes dependencies between jobs in pipeline configurations
- **Platform Templates**: Platform-specific templates and guidance for CI/CD pipelines
