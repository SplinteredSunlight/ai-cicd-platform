# Security Enforcement Service

The Security Enforcement service is responsible for continuous security scanning, vulnerability detection, security policy enforcement, and compliance reporting in the AI CI/CD Platform.

## Features

- **Vulnerability Scanning**: Detect vulnerabilities in code, dependencies, and container images
- **Security Policy Enforcement**: Define and enforce security policies for your CI/CD pipelines
- **SBOM Generation**: Generate Software Bill of Materials (SBOM) for your applications
- **Vulnerability Database**: Comprehensive vulnerability intelligence from multiple sources
- **Security Reporting**: Generate detailed security reports for your applications
- **Compliance Reporting**: Generate compliance reports for various standards (PCI DSS, HIPAA, GDPR, etc.)
- **Automated Remediation**: Automatically generate and apply remediation plans for detected vulnerabilities

## Vulnerability Database Integration

The Security Enforcement service integrates with multiple vulnerability databases to provide comprehensive vulnerability intelligence:

### Core Vulnerability Sources

- **NVD (National Vulnerability Database)**: The U.S. government repository of standards-based vulnerability management data
- **GitHub Security Advisories**: Security vulnerabilities from GitHub's advisory database
- **Snyk Vulnerability Database**: Commercial vulnerability database with a focus on open source packages

### Enhanced OSINT Sources

- **MITRE CVE Database**: Direct integration with the authoritative MITRE CVE database, which is the source of truth for CVE identifiers
- **OSV (Open Source Vulnerabilities)**: Integration with Google's OSV database, which provides vulnerability information for open source packages across multiple ecosystems
- **VulnDB**: Integration with Risk Based Security's VulnDB, a comprehensive commercial vulnerability intelligence database
- **Exploit-DB**: Database of exploits and vulnerable software
- **VulDB**: Database of security vulnerabilities

### Additional Compliance Sources

- **NIST SCAP (Security Content Automation Protocol)**: Standardized security data and automated configuration, vulnerability, and patch checking
- **OVAL (Open Vulnerability and Assessment Language)**: A community standard for security content, assessment, and reporting
- **CAPEC (Common Attack Pattern Enumeration and Classification)**: A comprehensive dictionary of known attack patterns
- **EPSS (Exploit Prediction Scoring System)**: Provides a probability score for whether a vulnerability will be exploited
- **CERT/CC Vulnerability Notes Database**: Provides information about vulnerabilities reported to the CERT Coordination Center

### Remediation Sources

- **NIST National Checklist Program (NCP)**: Provides security checklists for various platforms and applications
- **CERT Coordination Center Vulnerability Notes**: Provides detailed remediation steps for vulnerabilities
- **OVAL (Open Vulnerability and Assessment Language)**: Provides standardized vulnerability assessment and remediation
- **EPSS (Exploit Prediction Scoring System)**: Helps prioritize vulnerabilities based on likelihood of exploitation
- **SCAP (Security Content Automation Protocol)**: Provides automated vulnerability management and remediation

## Configuration

The Security Enforcement service can be configured using environment variables or a `.env` file:

```
# Environment Configuration
ENVIRONMENT=development
DEBUG=true

# Security Scanner API Keys
SNYK_API_KEY=your-snyk-api-key
SNYK_ORG_ID=your-snyk-org-id

# OWASP ZAP Configuration
ZAP_API_KEY=your-zap-api-key
ZAP_PROXY_URL=http://localhost:8080

# Trivy Configuration
TRIVY_SERVER_URL=http://localhost:8080

# Vulnerability Database
VULN_DB_UPDATE_INTERVAL=86400  # 24 hours
VULN_DB_PATH=/tmp/artifacts/vulnerability_database.sqlite
VULN_DB_AUTO_UPDATE=true
VULN_DB_SOURCES=NVD,GITHUB,SNYK,OSINT

# External Vulnerability Database API Keys
NVD_API_KEY=your-nvd-api-key
GITHUB_TOKEN=your-github-token
VULDB_API_KEY=your-vuldb-api-key
MITRE_CVE_API_KEY=your-mitre-cve-api-key
OSV_API_KEY=your-osv-api-key

# Additional Vulnerability Database API Keys
NCP_API_KEY=your-ncp-api-key
CERT_API_KEY=your-cert-api-key
OVAL_API_KEY=your-oval-api-key
EPSS_API_KEY=your-epss-api-key
SCAP_API_KEY=your-scap-api-key

# Automated Remediation Configuration
AUTO_REMEDIATION_ENABLED=false
AUTO_REMEDIATION_SEVERITY_THRESHOLD=HIGH
AUTO_REMEDIATION_CONFIDENCE_THRESHOLD=0.8
```

## Compliance Standards

The Security Enforcement service supports compliance reporting for the following standards:

- **PCI DSS (Payment Card Industry Data Security Standard)**: Security standard for organizations that handle credit card data
- **HIPAA (Health Insurance Portability and Accountability Act)**: Regulations for protecting sensitive patient health information
- **GDPR (General Data Protection Regulation)**: Data protection and privacy regulations for individuals in the EU
- **SOC2 (Service Organization Control 2)**: Framework for managing customer data based on five trust principles
- **ISO27001**: International standard for information security management
- **NIST 800-53**: Security and privacy controls for federal information systems and organizations
- **NIST CSF (Cybersecurity Framework)**: Framework for improving cybersecurity risk management
- **CIS (Center for Internet Security)**: Best practices for securing IT systems and data
- **OWASP Top 10**: Standard awareness document for web application security risks

## API Endpoints

The Security Enforcement service provides the following API endpoints:

### Vulnerability Scanning and Management

- `POST /api/v1/scan`: Scan a repository or artifact for vulnerabilities
- `GET /api/v1/vulnerabilities`: Query the vulnerability database
- `GET /api/v1/vulnerabilities/{id}`: Get details for a specific vulnerability
- `POST /api/v1/vulnerabilities/update`: Update the vulnerability database
- `GET /api/v1/vulnerabilities/stats`: Get statistics about the vulnerability database
- `POST /api/v1/sbom/generate`: Generate an SBOM for a repository or artifact
- `POST /api/v1/sbom/validate`: Validate an SBOM
- `POST /api/v1/sbom/sign`: Sign an SBOM using Sigstore

### Compliance Reporting

- `POST /api/v1/compliance/report`: Generate a compliance report for a repository
- `GET /api/v1/compliance/report/{id}`: Get a compliance report by ID
- `POST /api/v1/compliance/update-sources`: Update vulnerability database from additional sources for compliance reporting

### Automated Remediation

- `POST /api/v1/remediation/plan`: Generate a remediation plan for vulnerabilities
- `GET /api/v1/remediation/plan/{plan_id}`: Get a remediation plan by ID
- `GET /api/v1/remediation/plans`: Get all remediation plans
- `POST /api/v1/remediation/plan/{plan_id}/apply`: Apply a remediation plan
- `GET /api/v1/remediation/actions/{vulnerability_id}`: Get remediation actions for a vulnerability

## Usage

### Scanning a Repository

```bash
curl -X POST http://localhost:8002/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/example/repo",
    "commit_sha": "1234567890abcdef",
    "scan_types": ["trivy", "snyk", "zap"]
  }'
```

### Querying the Vulnerability Database

```bash
curl -X GET http://localhost:8002/api/v1/vulnerabilities \
  -H "Content-Type: application/json" \
  -d '{
    "cve_id": "CVE-2021-44228",
    "severity": ["CRITICAL", "HIGH"],
    "limit": 10
  }'
```

### Updating the Vulnerability Database

```bash
curl -X POST http://localhost:8002/api/v1/vulnerabilities/update \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["NVD", "GITHUB", "SNYK", "OSINT"],
    "force_update": true
  }'
```

### Generating a Compliance Report

```bash
curl -X POST http://localhost:8002/api/v1/compliance/report \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/example/repo",
    "commit_sha": "1234567890abcdef",
    "standards": ["PCI_DSS", "OWASP_TOP_10"],
    "include_vulnerabilities": true
  }'
```

### Getting a Compliance Report

```bash
curl -X GET http://localhost:8002/api/v1/compliance/report/CR-20250225-12345678
```

### Updating Additional Vulnerability Sources for Compliance

```bash
curl -X POST http://localhost:8002/api/v1/compliance/update-sources?days_back=30
```

### Generating a Remediation Plan

```bash
curl -X POST http://localhost:8002/api/v1/remediation/plan \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/example/repo",
    "commit_sha": "1234567890abcdef",
    "vulnerability_ids": ["CVE-2021-44228"],
    "auto_apply": false
  }'
```

### Getting a Remediation Plan

```bash
curl -X GET http://localhost:8002/api/v1/remediation/plan/PLAN-20250225-12345678
```

### Applying a Remediation Plan

```bash
curl -X POST http://localhost:8002/api/v1/remediation/plan/PLAN-20250225-12345678/apply
```

### Getting Remediation Actions for a Vulnerability

```bash
curl -X GET http://localhost:8002/api/v1/remediation/actions/CVE-2021-44228
```

## Development

### Prerequisites

- Python 3.9+
- SQLite 3
- API keys for vulnerability databases (optional)

### Setup

1. Clone the repository
2. Create a virtual environment
3. Install dependencies
4. Create a `.env` file from `.env.example`
5. Run the service

```bash
cd services/security-enforcement
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env to add your API keys
python main.py
```

### Testing

```bash
pytest
pytest --cov=.
```

## Architecture

The Security Enforcement service consists of the following components:

- **Security Coordinator**: Coordinates security scans, vulnerability management, compliance reporting, and remediation
- **Vulnerability Database**: Stores and manages vulnerability data from multiple sources
- **Security Scanners**: Integrations with security scanning tools (Trivy, Snyk, ZAP)
- **SBOM Generator**: Generates and validates SBOMs
- **Sigstore Integration**: Signs and verifies artifacts using Sigstore
- **Compliance Reporting Service**: Generates compliance reports based on vulnerability data and compliance standards
- **Remediation Service**: Generates and applies remediation plans for vulnerabilities
- **Vulnerability Database Integrations**:
  - Core sources: NVD, GitHub, Snyk
  - Enhanced OSINT sources: MITRE CVE, OSV, VulnDB, Exploit-DB, VulDB
  - Compliance sources: NIST SCAP, OVAL, CAPEC, EPSS, CERT/CC
  - Remediation sources: NCP, CERT, OVAL, EPSS, SCAP

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Development Guidelines

- Write tests for all new features
- Maintain code coverage above 80%
- Follow the code style guidelines
- Update documentation as needed
