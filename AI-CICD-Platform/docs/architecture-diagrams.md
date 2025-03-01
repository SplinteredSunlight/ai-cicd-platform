# AI CI/CD Platform Architecture Diagrams

This document contains all the architecture diagrams for the AI CI/CD Platform, providing a visual representation of the system's components, their relationships, and data flows.

## System Overview

The following diagram provides a high-level overview of the entire AI CI/CD Platform:

```mermaid
graph TD
    User[User/Developer] --> FE[Frontend Dashboard]
    FE --> AG[API Gateway]
    AG --> PG[AI Pipeline Generator]
    AG --> SE[Security Enforcement]
    AG --> SHD[Self-Healing Debugger]
    
    PG --> GH[GitHub/GitLab]
    PG --> Jenkins[Jenkins/CI Systems]
    
    SE --> Trivy[Trivy Scanner]
    SE --> Snyk[Snyk Scanner]
    SE --> ZAP[ZAP Scanner]
    
    SHD --> Logs[Pipeline Logs]
    SHD --> Patches[Auto Patches]
    
    Redis[Redis] --- AG
    
    subgraph External Services
        GH
        Jenkins
        Trivy
        Snyk
        ZAP
    end
    
    subgraph Core Platform
        FE
        AG
        PG
        SE
        SHD
        Redis
    end
    
    subgraph Data
        Logs
        Patches
    end
    
    style Core Platform fill:#f9f,stroke:#333,stroke-width:2px
    style External Services fill:#bbf,stroke:#333,stroke-width:1px
    style Data fill:#bfb,stroke:#333,stroke-width:1px
```

## Foundation and Architecture Components

The Foundation and Architecture layer provides the core infrastructure and services that support the entire platform:

```mermaid
graph TD
    subgraph "Foundation and Architecture"
        Redis[Redis Cache]
        DockerInfra[Docker Infrastructure]
        K8s[Kubernetes Orchestration]
        ConfigMgmt[Configuration Management]
        SecretsMgmt[Secrets Management]
        Logging[Centralized Logging]
        Monitoring[System Monitoring]
        APIGateway[API Gateway]
    end
    
    subgraph "Core Services"
        FE[Frontend Dashboard]
        PG[AI Pipeline Generator]
        SE[Security Enforcement]
        SHD[Self-Healing Debugger]
    end
    
    FE --> APIGateway
    PG --> APIGateway
    SE --> APIGateway
    SHD --> APIGateway
    
    APIGateway --> Redis
    APIGateway --> SecretsMgmt
    
    FE --> DockerInfra
    PG --> DockerInfra
    SE --> DockerInfra
    SHD --> DockerInfra
    
    DockerInfra --> K8s
    
    K8s --> ConfigMgmt
    K8s --> Logging
    K8s --> Monitoring
    
    style Foundation and Architecture fill:#f9f,stroke:#333,stroke-width:2px
    style Core Services fill:#bbf,stroke:#333,stroke-width:1px
```

## API Gateway Architecture

The API Gateway serves as the central entry point for all client requests and handles routing, authentication, rate limiting, and more:

```mermaid
graph TD
    Client[Client Applications] --> LB[Load Balancer]
    LB --> Gateway[API Gateway]
    
    subgraph "API Gateway Components"
        Gateway --> Auth[Authentication Service]
        Gateway --> RL[Rate Limiting Service]
        Gateway --> Cache[Cache Service]
        Gateway --> Router[Routing Service]
        Gateway --> Metrics[Metrics Service]
        Gateway --> Resilience[Resilience Service]
        Gateway --> Version[Version Service]
        Gateway --> WebSocket[WebSocket Service]
    end
    
    Auth --> TokenSvc[Token Service]
    Auth --> APIKeySvc[API Key Service]
    
    Router --> FE[Frontend Dashboard API]
    Router --> PG[AI Pipeline Generator API]
    Router --> SE[Security Enforcement API]
    Router --> SHD[Self-Healing Debugger API]
    
    Cache --> Redis[Redis Cache]
    RL --> Redis
    
    style API Gateway Components fill:#f9f,stroke:#333,stroke-width:2px
```

## Data Flow Architecture

This diagram illustrates how data flows through the system:

```mermaid
sequenceDiagram
    participant User as User/Developer
    participant FE as Frontend Dashboard
    participant AG as API Gateway
    participant PG as AI Pipeline Generator
    participant SE as Security Enforcement
    participant SHD as Self-Healing Debugger
    participant Ext as External Services
    
    User->>FE: Interact with UI
    FE->>AG: API Request
    
    alt Pipeline Generation
        AG->>PG: Forward Request
        PG->>Ext: Interact with CI/CD Systems
        Ext-->>PG: Response
        PG-->>AG: Results
    else Security Scanning
        AG->>SE: Forward Request
        SE->>Ext: Scan for Vulnerabilities
        Ext-->>SE: Scan Results
        SE-->>AG: Security Report
    else Debugging
        AG->>SHD: Forward Request
        SHD->>Ext: Analyze Pipeline Logs
        SHD->>Ext: Apply Patches
        Ext-->>SHD: Results
        SHD-->>AG: Debug Report
    end
    
    AG-->>FE: API Response
    FE-->>User: Display Results
```

## Deployment Architecture

The deployment architecture shows how the system is deployed in a containerized environment:

```mermaid
graph TD
    subgraph "Docker Host / Kubernetes Cluster"
        subgraph "Frontend Tier"
            FE[Frontend Dashboard Container]
            NGINX[NGINX Container]
        end
        
        subgraph "API Tier"
            AG[API Gateway Container]
        end
        
        subgraph "Service Tier"
            PG[AI Pipeline Generator Container]
            SE[Security Enforcement Container]
            SHD[Self-Healing Debugger Container]
        end
        
        subgraph "Data Tier"
            Redis[Redis Container]
            Logs[Log Storage]
        end
    end
    
    Internet[Internet] --> NGINX
    NGINX --> FE
    FE --> AG
    AG --> PG
    AG --> SE
    AG --> SHD
    
    PG --> Redis
    SE --> Redis
    SHD --> Redis
    
    PG --> Logs
    SE --> Logs
    SHD --> Logs
    
    style Frontend Tier fill:#bbf,stroke:#333,stroke-width:1px
    style API Tier fill:#f9f,stroke:#333,stroke-width:1px
    style Service Tier fill:#bfb,stroke:#333,stroke-width:1px
    style Data Tier fill:#fbf,stroke:#333,stroke-width:1px
```

## Security Architecture

The security architecture illustrates the security controls and data protection mechanisms:

```mermaid
graph TD
    subgraph "External"
        User[User/Developer]
        Internet[Internet]
    end
    
    subgraph "DMZ"
        WAF[Web Application Firewall]
        LB[Load Balancer]
    end
    
    subgraph "Application Layer"
        Auth[Authentication]
        RBAC[Role-Based Access Control]
        APIGateway[API Gateway]
    end
    
    subgraph "Service Layer"
        FE[Frontend Dashboard]
        PG[AI Pipeline Generator]
        SE[Security Enforcement]
        SHD[Self-Healing Debugger]
    end
    
    subgraph "Data Layer"
        Encryption[Data Encryption]
        Redis[Redis]
        Logs[Logs]
    end
    
    User --> Internet
    Internet --> WAF
    WAF --> LB
    LB --> Auth
    Auth --> RBAC
    RBAC --> APIGateway
    
    APIGateway --> FE
    APIGateway --> PG
    APIGateway --> SE
    APIGateway --> SHD
    
    FE --> Encryption
    PG --> Encryption
    SE --> Encryption
    SHD --> Encryption
    
    Encryption --> Redis
    Encryption --> Logs
    
    style External fill:#ddd,stroke:#333,stroke-width:1px
    style DMZ fill:#fbb,stroke:#333,stroke-width:1px
    style Application Layer fill:#bbf,stroke:#333,stroke-width:1px
    style Service Layer fill:#bfb,stroke:#333,stroke-width:1px
    style Data Layer fill:#fbf,stroke:#333,stroke-width:1px
```

## Self-Healing Debugger Architecture

The Self-Healing Debugger service has been enhanced with expanded error pattern recognition and advanced auto-patching capabilities:

```mermaid
graph TD
    API[API Endpoints] --> LA[Log Analyzer]
    API --> AP[Auto Patcher]
    API --> CD[CLI Debugger]
    
    LA --> EPR[Error Pattern Recognition]
    LA --> AIA[AI Analysis]
    LA --> EC[Error Categorization]
    
    AP --> TPG[Template-based Patch Generation]
    AP --> AIG[AI-based Patch Generation]
    AP --> PV[Patch Validation]
    AP --> PR[Patch Rollback]
    
    CD --> WS[WebSocket Interface]
    CD --> CLI[Command Line Interface]
    CD --> VIZ[Visualization]
    
    EPR --> Patterns[Error Patterns DB]
    AIA --> OpenAI[OpenAI API]
    
    subgraph Core Components
        LA
        AP
        CD
    end
    
    subgraph Log Analyzer Components
        EPR
        AIA
        EC
    end
    
    subgraph Auto Patcher Components
        TPG
        AIG
        PV
        PR
    end
    
    subgraph CLI Debugger Components
        WS
        CLI
        VIZ
    end
    
    subgraph External Dependencies
        Patterns
        OpenAI
    end
    
    style Core Components fill:#f9f,stroke:#333,stroke-width:2px
    style Log Analyzer Components fill:#bbf,stroke:#333,stroke-width:1px
    style Auto Patcher Components fill:#bfb,stroke:#333,stroke-width:1px
    style CLI Debugger Components fill:#fbf,stroke:#333,stroke-width:1px
    style External Dependencies fill:#fbb,stroke:#333,stroke-width:1px
```

## AI Pipeline Generator Architecture

The AI Pipeline Generator service creates and optimizes CI/CD pipelines using machine learning:

```mermaid
graph TD
    API[API Endpoints] --> DA[Dependency Analyzer]
    API --> PG[Pipeline Generator]
    API --> PO[Pipeline Optimizer]
    API --> PT[Platform Templates]
    
    DA --> DepDB[Dependency Database]
    PG --> ML[ML Models]
    PO --> Metrics[Performance Metrics]
    PT --> Templates[Template Repository]
    
    subgraph Core Components
        DA
        PG
        PO
        PT
    end
    
    subgraph External Dependencies
        DepDB
        ML
        Metrics
        Templates
    end
    
    style Core Components fill:#f9f,stroke:#333,stroke-width:2px
    style External Dependencies fill:#fbb,stroke:#333,stroke-width:1px
```

## Security Enforcement Architecture

The Security Enforcement service scans for vulnerabilities and enforces security policies:

```mermaid
graph TD
    API[API Endpoints] --> SC[Security Coordinator]
    API --> CR[Compliance Reporting]
    API --> RS[Remediation Service]
    API --> VDB[Vulnerability Database]
    
    SC --> TS[Trivy Scanner]
    SC --> SS[Snyk Scanner]
    SC --> ZS[ZAP Scanner]
    
    VDB --> CVE[CVE MITRE Integration]
    VDB --> OSV[OSV Integration]
    VDB --> OVAL[OVAL Integration]
    VDB --> EPSS[EPSS Integration]
    VDB --> NCP[NCP Integration]
    VDB --> SCAP[SCAP Integration]
    VDB --> CERT[CERT Integration]
    
    subgraph Core Components
        SC
        CR
        RS
        VDB
    end
    
    subgraph Scanner Integrations
        TS
        SS
        ZS
    end
    
    subgraph Vulnerability Data Sources
        CVE
        OSV
        OVAL
        EPSS
        NCP
        SCAP
        CERT
    end
    
    style Core Components fill:#f9f,stroke:#333,stroke-width:2px
    style Scanner Integrations fill:#bbf,stroke:#333,stroke-width:1px
    style Vulnerability Data Sources fill:#bfb,stroke:#333,stroke-width:1px
```

## Frontend Dashboard Architecture

The Frontend Dashboard provides a user interface for interacting with the platform:

```mermaid
graph TD
    App[App.tsx] --> Router[React Router]
    Router --> Auth[Auth Pages]
    Router --> Main[Main Pages]
    Router --> Docs[API Docs Pages]
    
    Main --> Dashboard[Dashboard Components]
    Main --> Visualizations[Visualization Components]
    
    Dashboard --> APIClient[API Client]
    Visualizations --> APIClient
    
    APIClient --> Redux[Redux Store]
    
    subgraph UI Components
        Auth
        Main
        Docs
        Dashboard
        Visualizations
    end
    
    subgraph State Management
        Redux
    end
    
    subgraph API Communication
        APIClient
    end
    
    style UI Components fill:#bbf,stroke:#333,stroke-width:1px
    style State Management fill:#f9f,stroke:#333,stroke-width:2px
    style API Communication fill:#bfb,stroke:#333,stroke-width:1px
```

## Generating Diagram Images

To generate PNG images from these Mermaid diagrams:

1. Use the Mermaid CLI:
   ```bash
   mmdc -i docs/architecture-diagrams.md -o docs/architecture-diagrams.png
   ```

2. Or use the Mermaid Live Editor:
   - Go to https://mermaid.live/
   - Copy each diagram code
   - Export as PNG

3. For individual diagrams, you can extract each diagram to its own file:
   ```bash
   # Example for system overview
   mmdc -i docs/architecture-diagrams.md -o docs/system-overview.png -s 1
