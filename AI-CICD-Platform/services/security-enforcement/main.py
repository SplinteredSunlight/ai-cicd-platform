from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn
from typing import Optional, List, Dict, Any
from datetime import datetime

from .models.vulnerability import SecurityScanRequest, SBOMRequest, SecurityScanResponse, SeverityLevel
from .models.vulnerability_database import (
    VulnerabilityDatabaseQuery,
    VulnerabilityDatabaseEntry,
    VulnerabilityDatabaseStats,
    VulnerabilityDatabaseUpdateRequest,
    VulnerabilityStatus,
    VulnerabilitySource
)
from .models.compliance_report import (
    ComplianceReportRequest,
    ComplianceReportSummary,
    ComplianceReport,
    ComplianceStandard
)
from .models.remediation import (
    RemediationAction,
    RemediationPlan,
    RemediationRequest,
    RemediationResult,
    RemediationStrategy,
    RemediationStatus,
    RemediationSource
)
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

# Vulnerability Database API Endpoints
@app.get("/api/v1/vulnerabilities", response_model=List[VulnerabilityDatabaseEntry])
async def search_vulnerabilities(
    cve_id: Optional[str] = Query(None, description="CVE ID to search for"),
    component: Optional[str] = Query(None, description="Component name to search for"),
    severity: Optional[List[SeverityLevel]] = Query(None, description="Severity levels to include"),
    status: Optional[List[VulnerabilityStatus]] = Query(None, description="Status values to include"),
    source: Optional[List[VulnerabilitySource]] = Query(None, description="Sources to include"),
    text_search: Optional[str] = Query(None, description="Free text search in title and description"),
    limit: int = Query(100, description="Maximum number of results to return"),
    offset: int = Query(0, description="Offset for pagination"),
    coordinator: SecurityCoordinator = Depends(security_service.get_coordinator)
):
    """
    Search for vulnerabilities in the database
    """
    try:
        query = VulnerabilityDatabaseQuery(
            cve_id=cve_id,
            component=component,
            severity=severity,
            status=status,
            source=source,
            text_search=text_search,
            limit=limit,
            offset=offset
        )
        
        results = await coordinator.search_vulnerability_database(query)
        return results
    
    except Exception as e:
        logger.error("vulnerability_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/vulnerabilities/{vuln_id}", response_model=VulnerabilityDatabaseEntry)
async def get_vulnerability(
    vuln_id: str,
    coordinator: SecurityCoordinator = Depends(security_service.get_coordinator)
):
    """
    Get a specific vulnerability by ID
    """
    try:
        result = await coordinator.get_vulnerability_from_database(vuln_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Vulnerability {vuln_id} not found")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_vulnerability_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/vulnerabilities", response_model=VulnerabilityDatabaseEntry)
async def add_vulnerability(
    entry: VulnerabilityDatabaseEntry,
    coordinator: SecurityCoordinator = Depends(security_service.get_coordinator)
):
    """
    Add a custom vulnerability to the database
    """
    try:
        success = await coordinator.add_custom_vulnerability(entry)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add vulnerability")
        
        # Return the added vulnerability
        return entry
    
    except Exception as e:
        logger.error("add_vulnerability_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/v1/vulnerabilities/{vuln_id}/status", response_model=dict)
async def update_vulnerability_status(
    vuln_id: str,
    status: VulnerabilityStatus,
    notes: Optional[str] = None,
    coordinator: SecurityCoordinator = Depends(security_service.get_coordinator)
):
    """
    Update the status of a vulnerability
    """
    try:
        success = await coordinator.update_vulnerability_status(vuln_id, status, notes)
        if not success:
            raise HTTPException(status_code=404, detail=f"Vulnerability {vuln_id} not found")
        
        return {
            "id": vuln_id,
            "status": status,
            "updated": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_vulnerability_status_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/vulnerabilities/stats", response_model=VulnerabilityDatabaseStats)
async def get_vulnerability_stats(
    coordinator: SecurityCoordinator = Depends(security_service.get_coordinator)
):
    """
    Get statistics about the vulnerability database
    """
    try:
        stats = await coordinator.get_vulnerability_database_stats()
        return stats
    
    except Exception as e:
        logger.error("get_vulnerability_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/vulnerabilities/update-database", response_model=dict)
async def update_vulnerability_database(
    request: VulnerabilityDatabaseUpdateRequest,
    coordinator: SecurityCoordinator = Depends(security_service.get_coordinator)
):
    """
    Update the vulnerability database from external sources
    """
    try:
        sources = [s.value for s in request.sources]
        result = await coordinator.update_vulnerability_database(sources, request.force_update)
        return result
    
    except Exception as e:
        logger.error("update_vulnerability_database_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Compliance Reporting API Endpoints
@app.post("/api/v1/compliance/report", response_model=Dict[str, Any])
async def generate_compliance_report(
    request: ComplianceReportRequest,
    coordinator: SecurityCoordinator = Depends(security_service.get_coordinator)
):
    """
    Generate a compliance report for a repository
    """
    try:
        logger.info("generating_compliance_report", 
                   repository=request.repository_url, 
                   commit=request.commit_sha,
                   standards=request.standards)
        
        result = await coordinator.generate_compliance_report(request)
        
        if result.get("status") == "error":
            return JSONResponse(
                status_code=400,
                content=result
            )
        
        return JSONResponse(content=result)
    
    except ValueError as e:
        logger.error("compliance_report_validation_error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("compliance_report_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/compliance/report/{report_id}", response_model=ComplianceReport)
async def get_compliance_report(
    report_id: str,
    coordinator: SecurityCoordinator = Depends(security_service.get_coordinator)
):
    """
    Get a compliance report by ID
    """
    try:
        report = await coordinator.get_compliance_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"Compliance report {report_id} not found")
        return report
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_compliance_report_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/compliance/update-sources", response_model=Dict[str, Any])
async def update_additional_sources(
    days_back: int = Query(30, description="Number of days to look back for recent vulnerabilities"),
    coordinator: SecurityCoordinator = Depends(security_service.get_coordinator)
):
    """
    Update vulnerability database from additional sources for compliance reporting
    """
    try:
        result = await coordinator.update_from_additional_sources(days_back)
        return result
    
    except Exception as e:
        logger.error("update_additional_sources_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Remediation API Endpoints
@app.post("/api/v1/remediation/plan", response_model=RemediationPlan)
async def generate_remediation_plan(
    request: RemediationRequest,
    coordinator: SecurityCoordinator = Depends(security_service.get_coordinator)
):
    """
    Generate a remediation plan for vulnerabilities
    """
    try:
        logger.info("generating_remediation_plan", 
                   repository=request.repository_url, 
                   commit=request.commit_sha)
        
        plan = await coordinator.generate_remediation_plan(request)
        return plan
    
    except ValueError as e:
        logger.error("remediation_plan_validation_error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("remediation_plan_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/remediation/plan/{plan_id}", response_model=RemediationPlan)
async def get_remediation_plan(
    plan_id: str,
    coordinator: SecurityCoordinator = Depends(security_service.get_coordinator)
):
    """
    Get a remediation plan by ID
    """
    try:
        plan = await coordinator.get_remediation_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail=f"Remediation plan {plan_id} not found")
        return plan
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_remediation_plan_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/remediation/plans", response_model=List[RemediationPlan])
async def get_all_remediation_plans(
    coordinator: SecurityCoordinator = Depends(security_service.get_coordinator)
):
    """
    Get all remediation plans
    """
    try:
        plans = await coordinator.get_all_remediation_plans()
        return plans
    
    except Exception as e:
        logger.error("get_all_remediation_plans_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/remediation/plan/{plan_id}/apply", response_model=List[RemediationResult])
async def apply_remediation_plan(
    plan_id: str,
    coordinator: SecurityCoordinator = Depends(security_service.get_coordinator)
):
    """
    Apply a remediation plan
    """
    try:
        results = await coordinator.apply_remediation_plan(plan_id)
        return results
    
    except ValueError as e:
        logger.error("apply_remediation_plan_validation_error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("apply_remediation_plan_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/remediation/actions/{vulnerability_id}", response_model=List[RemediationAction])
async def get_remediation_actions(
    vulnerability_id: str,
    coordinator: SecurityCoordinator = Depends(security_service.get_coordinator)
):
    """
    Get remediation actions for a vulnerability
    """
    try:
        actions = await coordinator.get_remediation_actions(vulnerability_id)
        return actions
    
    except Exception as e:
        logger.error("get_remediation_actions_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
