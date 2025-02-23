# AI-Powered CI/CD Automation & Security Platform

A cutting-edge platform that leverages artificial intelligence to automate and secure CI/CD pipelines, providing intelligent pipeline generation, security enforcement, and self-healing capabilities.

## 🚀 Features

- **AI Pipeline Generator**: Generates CI/CD pipelines from natural language using GPT-4
- **Security & Compliance Enforcement**: Automated security scanning and deployment blocking
- **Self-Healing Debugger**: AI-powered log analysis and automated failure recovery
- **Web Dashboard**: Real-time pipeline monitoring and management
- **API Gateway**: Unified access to all platform services
- **Kubernetes-Native**: Cloud-native architecture with Helm deployment

## 🏗️ Project Structure

```
ai-cicd-platform/
├── services/           # Microservices
│   ├── ai-pipeline-generator/
│   ├── security-enforcement/
│   ├── self-healing-debugger/
│   ├── api-gateway/
│   └── frontend-dashboard/
├── infra/             # Infrastructure as Code
│   └── kubernetes-configs/
├── docs/              # Documentation
├── tests/             # Test suites
└── scripts/           # Utility scripts
```

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React.js
- **AI/ML**: OpenAI GPT-4
- **Security**: Trivy, Snyk, OWASP ZAP
- **Infrastructure**: Kubernetes, Helm, Terraform
- **Authentication**: OAuth2
- **Artifact Signing**: Sigstore

## 🚦 Current Status

- ✅ Project initialization completed
- ✅ Repository structure established
- ✅ AI Pipeline Generator service implemented
- ✅ Security Enforcement service implemented
- ✅ Self-Healing Debugger service implemented
- ✅ API Gateway service implemented
- 🔄 Frontend Dashboard (in progress)
- 📝 Kubernetes deployment (planned)

## 🔧 Development Setup

### AI Pipeline Generator Service

1. Navigate to the service directory:
   ```bash
   cd services/ai-pipeline-generator
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

5. Run the service:
   ```bash
   uvicorn main:app --reload
   ```

6. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Security Enforcement Service

1. Navigate to the service directory:
   ```bash
   cd services/security-enforcement
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install security tools:
   ```bash
   # Install Trivy
   brew install aquasecurity/trivy/trivy  # macOS
   # For other OS, see: https://aquasecurity.github.io/trivy/latest/getting-started/installation/

   # Install Snyk CLI
   npm install -g snyk
   snyk auth  # Follow prompts to authenticate

   # Install OWASP ZAP
   brew install zap  # macOS
   # For other OS, download from: https://www.zaproxy.org/download/
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configurations
   ```

6. Run the service:
   ```bash
   uvicorn main:app --reload --port 8001
   ```

7. Access the API documentation:
   - Swagger UI: http://localhost:8001/docs
   - ReDoc: http://localhost:8001/redoc

### Self-Healing Debugger Service

1. Navigate to the service directory:
   ```bash
   cd services/self-healing-debugger
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install and configure Elasticsearch:
   ```bash
   # Using Docker (recommended for development)
   docker run -d --name elasticsearch \
     -p 9200:9200 -p 9300:9300 \
     -e "discovery.type=single-node" \
     elasticsearch:8.7.0
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key and other configurations
   ```

6. Run the service:
   ```bash
   uvicorn main:app --reload --port 8002
   ```

7. Access the API documentation:
   - Swagger UI: http://localhost:8002/docs
   - ReDoc: http://localhost:8002/redoc

8. Use the CLI debugger:
   ```bash
   # Example: Debug a pipeline run
   python -m cli_debugger debug-pipeline \
     --pipeline-id my-pipeline-123 \
     --log-file pipeline.log
   ```

### API Gateway Service

1. Navigate to the service directory:
   ```bash
   cd services/api-gateway
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install and configure Redis:
   ```bash
   # Using Docker (recommended for development)
   docker run -d --name redis \
     -p 6379:6379 \
     redis:7.0
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. Run the service:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

7. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

8. Test the gateway:
   ```bash
   # Get authentication token
   curl -X POST http://localhost:8000/api/v1/auth/token \
     -d "username=admin&password=admin"

   # Use token to access services
   curl -H "Authorization: Bearer {token}" \
     http://localhost:8000/api/v1/pipeline/generate
   ```

### Running Tests

```bash
# AI Pipeline Generator tests
cd services/ai-pipeline-generator
pytest tests/

# Security Enforcement tests
cd services/security-enforcement
pytest tests/

# Self-Healing Debugger tests
cd services/self-healing-debugger
pytest tests/

# API Gateway tests
cd services/api-gateway
pytest tests/
```

## 📝 Getting Started

Coming soon: Installation and setup instructions will be added as development progresses.

## 🤝 Contributing

This project is currently in early development. Contribution guidelines will be added soon.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
