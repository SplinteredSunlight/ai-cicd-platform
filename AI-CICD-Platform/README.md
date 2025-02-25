# AI CI/CD Platform

An intelligent continuous integration and delivery platform that leverages artificial intelligence to automate and optimize your development workflow.

## Features

- 🤖 **AI Pipeline Generator**: Automatically generates and optimizes CI/CD pipelines based on your project structure
- 🛡️ **Security Enforcement**: Continuous security scanning and vulnerability detection
- 🔧 **Self-Healing Debugger**: Automated error detection and resolution
- 📊 **Real-time Analytics**: Comprehensive metrics and performance insights
- 🚀 **Modern Frontend**: React-based dashboard with Material UI

## Architecture

The platform consists of several microservices:

- **Frontend Dashboard**: React/TypeScript web interface
- **API Gateway**: Central entry point for all services
- **AI Pipeline Generator**: ML-powered pipeline creation
- **Security Enforcement**: Vulnerability scanning and security checks
- **Self-Healing Debugger**: Automated debugging and patching

## Prerequisites

- Node.js >= 18
- Python >= 3.9
- Docker
- Git

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/splinteredsunlight/ai-cicd-platform.git
   cd ai-cicd-platform
   ```

2. Set up the frontend dashboard:
   ```bash
   cd services/frontend-dashboard
   cp .env.example .env
   npm install
   npm run dev
   ```

3. Set up the backend services:
   ```bash
   # API Gateway
   cd ../api-gateway
   cp .env.example .env
   pip install -r requirements.txt
   python main.py

   # AI Pipeline Generator
   cd ../ai-pipeline-generator
   cp .env.example .env
   pip install -r requirements.txt
   python main.py

   # Security Enforcement
   cd ../security-enforcement
   cp .env.example .env
   pip install -r requirements.txt
   python main.py

   # Self-Healing Debugger
   cd ../self-healing-debugger
   cp .env.example .env
   pip install -r requirements.txt
   python main.py
   ```

## Development Credentials

For the frontend dashboard (development only):
- Email: admin@example.com
- Password: admin123

## Next Steps

1. **Set Up Backend Services**:
   - Configure environment variables in each service's `.env` file
   - Set up required API keys and credentials
   - Start each service in development mode

2. **Configure Security Settings**:
   - Set up vulnerability scanning thresholds
   - Configure security policies
   - Add custom security rules

3. **Customize Pipeline Generation**:
   - Train the AI model with your specific requirements
   - Add custom pipeline templates
   - Configure pipeline validation rules

4. **Set Up Monitoring**:
   - Configure metrics collection
   - Set up alerting thresholds
   - Customize dashboard views

5. **Production Deployment**:
   - Set up Docker containers
   - Configure production environment variables
   - Set up CI/CD for the platform itself
   - Configure SSL/TLS
   - Set up proper authentication

## API Documentation

Each service includes its own API documentation:

- API Gateway: http://localhost:8000/docs
- AI Pipeline Generator: http://localhost:8001/docs
- Security Enforcement: http://localhost:8002/docs
- Self-Healing Debugger: http://localhost:8003/docs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.
