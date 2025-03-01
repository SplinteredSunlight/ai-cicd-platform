# Self-Healing Debugger Service

An AI-powered pipeline debugging and auto-patching service for CI/CD pipelines.

## Overview

The Self-Healing Debugger Service is designed to automatically detect, analyze, and fix errors in CI/CD pipelines. It uses a combination of rule-based pattern matching and AI-powered analysis to identify errors in pipeline logs, generate patch solutions, and apply them to fix the issues.

## Recent Enhancements

### ML-Based Error Classification

The service now includes a machine learning-based error classification system that:

- **Automatically Classifies Errors**: Uses ML models to classify errors by category, severity, and pipeline stage
- **Learns from Historical Data**: Trains on historical error data to improve classification accuracy over time
- **Provides Confidence Scores**: Includes confidence scores with each classification for better decision-making
- **Supports Multiple Model Types**: Includes support for Random Forest, Naive Bayes, and other ML algorithms
- **Offers API and WebSocket Integration**: Exposes ML classification capabilities through both REST API and WebSocket

### Expanded Error Pattern Recognition

The error pattern recognition system has been significantly enhanced with:

- **Comprehensive Pattern Library**: Added over 100 new error patterns across multiple categories:
  - Dependency errors (Python, Node.js, Java/Maven, Docker, Go, Ruby)
  - Permission errors (file system, Docker, Git, CI/CD platforms, Kubernetes/Cloud)
  - Configuration errors (environment variables, CI/CD platforms, Docker, Kubernetes)
  - Network errors (connectivity, DNS, proxy, SSL/TLS)
  - Resource errors (memory, disk space, CPU, file descriptors)
  - Build errors (compilation, syntax, type, linker)
  - Test errors (assertions, timeouts, framework-specific)
  - Deployment errors (Kubernetes, cloud providers, container registries)
  - Security errors (vulnerabilities, authentication, authorization)

- **Multi-Platform Support**: Added patterns for various CI/CD platforms and environments:
  - GitHub Actions
  - GitLab CI
  - Jenkins
  - CircleCI
  - Azure DevOps
  - AWS CodeBuild

- **Improved Categorization**: Enhanced error categorization logic for more accurate classification

### Advanced Auto-Patching

The auto-patching system has been enhanced with:

- **New Patch Templates**: Added templates for fixing:
  - Network issues (proxy configuration, DNS resolution, SSL/TLS certificate problems)
  - Resource constraints (memory limits, disk space, file descriptor limits)
  - Test failures (timeout issues, assertion failures)
  - Security vulnerabilities (npm and pip package vulnerabilities)

- **Intelligent Patch Generation**: Improved patch generation logic for more effective and safer patches
- **Comprehensive Validation**: Enhanced validation steps to ensure patches are applied correctly

## Features

- **Automated Error Detection**: Analyzes pipeline logs to identify errors using pattern matching and AI.
- **ML-Based Error Classification**: Uses machine learning to classify errors by category, severity, and pipeline stage.
- **Root Cause Analysis**: Determines the root cause of errors and provides detailed analysis.
- **Auto-Patching**: Generates and applies patches to fix common pipeline errors.
- **Batch Patch Application**: Apply patches to multiple errors at once for efficient debugging.
- **Interactive Debugging**: Provides an enhanced interactive CLI interface for debugging sessions.
- **WebSocket Support**: Enables real-time debugging sessions through WebSocket connections.
- **Rollback Capability**: Allows rolling back applied patches if needed.
- **Session Export**: Export debug sessions to JSON, Markdown, or text reports for documentation.
- **Command History**: Maintains history of commands for quick access to previous operations.
- **Enhanced Visualization**: Improved error and analysis visualization with detailed metrics.

## Architecture

The service consists of the following components:

- **LogAnalyzer**: Analyzes pipeline logs to identify errors.
- **AutoPatcher**: Generates and applies patches for identified errors.
- **CLIDebugger**: Provides an interactive CLI interface for debugging sessions.
- **MLClassifier**: Classifies errors using machine learning models.
- **MLClassifierService**: Provides ML-based error classification services.
- **API Endpoints**: Exposes RESTful API endpoints for integration with other services.

## API Endpoints

### Root Endpoint

```
GET /
```

Returns the service status and version.

### Analyze Pipeline

```
POST /api/v1/debug/analyze
```

Analyzes pipeline logs and identifies errors.

**Parameters**:
- `pipeline_id`: ID of the pipeline run
- `log_content`: Pipeline log content to analyze

### Generate Patch

```
POST /api/v1/debug/patch
```

Generates a patch solution for an error.

**Parameters**:
- `error`: PipelineError object
- `context` (optional): Additional context for patch generation

### Apply Patch

```
POST /api/v1/debug/apply-patch
```

Applies a patch solution.

**Parameters**:
- `patch`: PatchSolution object
- `dry_run` (optional): Whether to simulate patch application (default: true)

### Batch Apply Patches

```
POST /api/v1/debug/batch-apply-patches
```

Apply patches to multiple errors in batch.

**Parameters**:
- `error_ids`: List of error IDs to patch
- `pipeline_id`: ID of the pipeline run
- `dry_run` (optional): Whether to simulate patch application (default: true)

### Rollback Patch

```
POST /api/v1/debug/rollback
```

Rolls back a previously applied patch.

**Parameters**:
- `patch_id`: ID of the patch to roll back

### Export Debug Session

```
POST /api/v1/debug/export-session
```

Export a debug session to a file.

**Parameters**:
- `pipeline_id`: ID of the pipeline run
- `format`: Export format (json, markdown, or text)

### Classify Error (ML)

```
POST /api/v1/ml/classify-error
```

Classify an error using ML models.

**Parameters**:
- `error`: PipelineError object
- `model_types` (optional): Dictionary mapping targets to model types

### Train ML Models

```
POST /api/v1/ml/train-models
```

Train ML models using historical error data.

**Parameters**:
- `pipeline_id` (optional): ID of the pipeline run to filter errors
- `limit` (optional): Maximum number of errors to use for training (default: 1000)
- `model_types` (optional): List of model types to train (default: ["random_forest"])

### Get ML Model Info

```
GET /api/v1/ml/model-info
```

Get information about trained ML models.

### Generate Training Data

```
POST /api/v1/ml/generate-training-data
```

Generate training data from historical errors.

**Parameters**:
- `output_file` (optional): Path to output file (default: "training_data.json")
- `limit` (optional): Maximum number of errors to include (default: 1000)

### WebSocket Debug Session

```
WebSocket /ws/debug-session
```

Establishes an interactive WebSocket debug session.

**Initial Parameters**:
- `pipeline_id`: ID of the pipeline run
- `log_content`: Pipeline log content to analyze

**Commands**:
- `analyze_error`: Analyzes a specific error
- `generate_patch`: Generates a patch for an error
- `apply_patch`: Applies a patch
- `apply_all_patches`: Batch generates and applies patches for multiple errors
- `rollback_patch`: Rolls back a patch
- `export_session`: Exports the debug session to a specified format
- `get_session_summary`: Gets session summary with detailed metrics
- `classify_error_ml`: Classifies an error using ML models
- `train_ml_models`: Trains ML models using historical error data
- `get_ml_model_info`: Gets information about trained ML models
- `exit`: Ends the session

## CLI Debugger

The CLI Debugger provides an interactive command-line interface for debugging pipeline errors. It has been enhanced with the following features:

### Command History and Auto-completion

The CLI Debugger now maintains a history of commands, allowing you to quickly access and reuse previous commands. Auto-completion is also available for commands, making it easier to navigate through the debugging process.

### Enhanced Error Visualization

Errors are now displayed with more detailed information, including:
- Error severity distribution
- Error category distribution
- Analysis status indicators
- Detailed session metrics

### Analysis Summary Visualization

The CLI Debugger now provides a comprehensive analysis summary panel that displays:
- Total number of errors detected
- Severity distribution (High, Medium, Low)
- Category distribution (Dependency, Permission, Configuration, etc.)
- Stage distribution (Build, Test, Deploy, etc.)
- Color-coded indicators for better readability

### Batch Patch Application

You can now apply patches to multiple errors at once using the "Apply all patches" command. This is useful for efficiently fixing multiple related issues.

### Session Export

Debug sessions can be exported to various formats:
- **JSON**: For programmatic access and integration with other tools
- **Markdown**: For documentation and sharing with team members
- **Text**: For simple text-based reports

### Help Command

A new "Help" command provides detailed information about available commands and usage tips.

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables (see `.env.example`)
4. Run the service:
   ```
   uvicorn main:app --host 0.0.0.0 --port 8003 --reload
   ```

## Configuration

The service can be configured using environment variables or a `.env` file. See `.env.example` for available configuration options.

## Testing

Run tests using pytest:

```
pytest
```

For specific component tests:

```
# Test CLI Debugger
pytest tests/test_cli_debugger.py

# Test Log Analyzer
pytest tests/test_log_analyzer.py

# Test Auto Patcher
pytest tests/test_auto_patcher.py

# Test ML Classifier
pytest tests/test_ml_classifier.py

# Test ML Classifier Service
pytest tests/test_ml_classifier_service.py

# Test ML Integration
pytest tests/test_ml_integration.py
```

For coverage report:

```
pytest --cov=.
```

### Test Status

- ✅ CLI Debugger tests: All passing
- ✅ Log Analyzer tests: All passing
- ✅ Auto Patcher tests: All passing
- ✅ ML Classifier tests: All passing
- ✅ ML Classifier Service tests: All passing
- ✅ ML Integration tests: All passing
- ❌ API Endpoint tests: Some failing (datetime serialization issues)

## Integration

The Self-Healing Debugger Service can be integrated with CI/CD platforms like GitHub Actions, Jenkins, GitLab CI, etc. It can be used to:

1. Analyze pipeline logs after failures
2. Generate and apply patches automatically (individually or in batch)
3. Provide interactive debugging sessions for complex issues
4. Export debug reports for documentation and knowledge sharing

## License

MIT
