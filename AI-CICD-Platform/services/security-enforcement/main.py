from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn
from typing import Optional

from .models.vulnerability import SecurityScanRequest, SBOMRequest, SecurityScanResponse, SeverityLevel
from .services.security_coordinator import SecurityCoordinator
from .config import get_settings

# Configure structured logging
logger = structlog.get_logger()

app = FastAPI(
    title="Security Enforcement Service",
    description="Automated security scanning and compliance enforcement for CI/CD pipelines",
    version="0.1.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "security-enforcement",
        "version": "0.1.0"
    }

class SecurityService:
    def __init__(self):
        self.settings = get_settings()
        self.coordinator = SecurityCoordinator()

    def get_coordinator(self) -> SecurityCoordinator:
        return self.coordinator

security_service = SecurityService()

@app.post("/api/v1/scan", response_model=SecurityScanResponse)
async def scan_artifacts(
    request: SecurityScanRequest,
    background_tasks: BackgroundTasks,
    coordinator: SecurityCoordinator = Depends(security_service.get_coordinator)
):
    """
    Scan artifacts for security vulnerabilities and generate SBOM
    """
    try:
        logger.info("starting_security_scan", 
                   repository=request.repository_url, 
                   commit=request.commit_sha,
                   scan_types=request.scan_type)
        
        result = await coordinator.run_security_scan(
            repository_url=request.repository_url,
            commit_sha=request.commit_sha,
            artifact_url=request.artifact_url,
            scan_types=request.scan_type,
            blocking_severity=request.blocking_severity
        )
        
        # Schedule cleanup in background
        background_tasks.add_task(coordinator.cleanup)
        
        return JSONResponse(content=result)
    
    except ValueError as e:
        logger.error("security_scan_validation_error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("security_scan_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/sbom", response_model=SecurityScanResponse)
async def generate_sbom(
    request: SBOMRequest,
    coordinator: SecurityCoordinator = Depends(security_service.get_coordinator)
):
    """
    Generate and sign Software Bill of Materials (SBOM)
    """
    try:
        logger.info("generating_sbom", 
                   repository=request.repository_url, 
                   commit=request.commit_sha)
        
        # Run a security scan first to gather component information
        result = await coordinator.run_security_scan(
            repository_url=request.repository_url,
            commit_sha=request.commit_sha,
            scan_types=["trivy", "snyk"]  # Focus on dependency scanning
        )
        
        if not result["passed"]:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "failed",
                    "message": "Security scan failed, SBOM generation aborted",
                    "report": result["report"]
                }
            )
        
        return JSONResponse(content=result)
    
    except ValueError as e:
        logger.error("sbom_generation_validation_error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("sbom_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
