import pytest
import asyncio
from datetime import datetime, timedelta
import os
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock

from ..models.vulnerability import Vulnerability, SeverityLevel
from ..models.vulnerability_database import (
    VulnerabilityDatabaseEntry,
    VulnerabilitySource,
    VulnerabilityStatus
)
from ..models.compliance_report import (
    ComplianceReport,
    ComplianceStandard,
    ComplianceRequirement,
    ComplianceViolation,
    ComplianceStatus,
    ComplianceReportSummary,
    ComplianceReportRequest
)
from ..services.vulnerability_database import VulnerabilityDatabase
from ..services.compliance_reporting import ComplianceReportingService
from ..services.security_coordinator import SecurityCoordinator

@pytest.fixture
def temp_db_path():
    """Create a temporary database file path"""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
def mock_vuln_db():
    """Create a mock vulnerability database"""
    mock_db = MagicMock(spec=VulnerabilityDatabase)
    mock_db.get_vulnerability = AsyncMock()
    mock_db._save_vulnerabilities = AsyncMock()
    return mock_db

@pytest.fixture
def compliance_service(mock_vuln_db):
    """Create a compliance reporting service with a mock vulnerability database"""
    return ComplianceReportingService(mock_vuln_db)

@pytest.fixture
def sample_vulnerabilities():
    """Create sample vulnerabilities for testing"""
    return [
        Vulnerability(
            id="CVE-2023-12345",
            title="SQL Injection in Login Form",
            description="A SQL injection vulnerability in the login form allows attackers to bypass authentication.",
            severity=SeverityLevel.HIGH,
            cvss_score=8.5,
            affected_component="example-app:login-service",
            fix_version="1.2.3",
            references=["https://example.com/cve-2023-12345"]
        ),
        Vulnerability(
            id="CVE-2023-67890",
            title="Cross-site Scripting in Profile Page",
            description="A cross-site scripting vulnerability in the profile page allows attackers to inject malicious scripts.",
            severity=SeverityLevel.MEDIUM,
            cvss_score=6.5,
            affected_component="example-app:profile-service",
            fix_version="2.3.4",
            references=["https://example.com/cve-2023-67890"]
        ),
        Vulnerability(
            id="CVE-2023-54321",
            title="Insecure Direct Object Reference",
            description="An insecure direct object reference vulnerability allows attackers to access unauthorized resources.",
            severity=SeverityLevel.HIGH,
            cvss_score=7.5,
            affected_component="example-app:resource-service",
            fix_version="3.4.5",
            references=["https://example.com/cve-2023-54321"]
        )
    ]

@pytest.fixture
def sample_db_entries():
    """Create sample database entries for testing"""
    return [
        VulnerabilityDatabaseEntry(
            vulnerability=Vulnerability(
                id="CVE-2023-12345",
                title="SQL Injection in Login Form",
                description="A SQL injection vulnerability in the login form allows attackers to bypass authentication.",
                severity=SeverityLevel.HIGH,
                cvss_score=8.5,
                affected_component="example-app:login-service",
                fix_version="1.2.3",
                references=["https://example.com/cve-2023-12345"]
            ),
            sources=[VulnerabilitySource.NVD, VulnerabilitySource.GITHUB],
            status=VulnerabilityStatus.ACTIVE,
            cwe_ids=["CWE-89"],
            tags={"sql-injection", "authentication"}
        ),
        VulnerabilityDatabaseEntry(
            vulnerability=Vulnerability(
                id="CVE-2023-67890",
                title="Cross-site Scripting in Profile Page",
                description="A cross-site scripting vulnerability in the profile page allows attackers to inject malicious scripts.",
                severity=SeverityLevel.MEDIUM,
                cvss_score=6.5,
                affected_component="example-app:profile-service",
                fix_version="2.3.4",
                references=["https://example.com/cve-2023-67890"]
            ),
            sources=[VulnerabilitySource.NVD, VulnerabilitySource.GITHUB],
            status=VulnerabilityStatus.ACTIVE,
            cwe_ids=["CWE-79"],
            tags={"xss", "injection"}
        )
    ]

@pytest.mark.asyncio
async def test_generate_compliance_report(compliance_service, sample_vulnerabilities, mock_vuln_db):
    """Test generating a compliance report"""
    # Configure mock
    mock_vuln_db.get_vulnerability.side_effect = lambda vuln_id: (
        VulnerabilityDatabaseEntry(
            vulnerability=next((v for v in sample_vulnerabilities if v.id == vuln_id), None),
            sources=[VulnerabilitySource.NVD],
            status=VulnerabilityStatus.ACTIVE,
            cwe_ids=["CWE-89"] if vuln_id == "CVE-2023-12345" else ["CWE-79"] if vuln_id == "CVE-2023-67890" else []
        ) if vuln_id in [v.id for v in sample_vulnerabilities] else None
    )
    
    # Generate a compliance report
    report = await compliance_service.generate_compliance_report(
        repository_url="https://github.com/example/repo",
        commit_sha="1234567890abcdef",
        standards=[ComplianceStandard.PCI_DSS, ComplianceStandard.OWASP_TOP_10],
        vulnerabilities=sample_vulnerabilities,
        include_vulnerability_details=True
    )
    
    # Verify the report
    assert report.id.startswith("CR-")
    assert report.target == "https://github.com/example/repo@1234567890abcdef"
    assert set(report.standards) == {ComplianceStandard.PCI_DSS, ComplianceStandard.OWASP_TOP_10}
    assert len(report.violations) > 0
    
    # Verify that SQL injection vulnerability maps to PCI-DSS-6.5.1
    sql_injection_violations = [v for v in report.violations if v.requirement_id == "PCI-DSS-6.5.1"]
    assert len(sql_injection_violations) > 0
    assert "CVE-2023-12345" in sql_injection_violations[0].vulnerability_ids
    
    # Verify that XSS vulnerability maps to PCI-DSS-6.5.7
    xss_violations = [v for v in report.violations if v.requirement_id == "PCI-DSS-6.5.7"]
    assert len(xss_violations) > 0
    assert "CVE-2023-67890" in xss_violations[0].vulnerability_ids
    
    # Verify that the summary is updated
    assert ComplianceStandard.PCI_DSS in report.summary
    assert ComplianceStandard.OWASP_TOP_10 in report.summary
    assert ComplianceStatus.NON_COMPLIANT in report.summary[ComplianceStandard.PCI_DSS]
    assert report.summary[ComplianceStandard.PCI_DSS][ComplianceStatus.NON_COMPLIANT] > 0

@pytest.mark.asyncio
async def test_get_compliance_report_summary(compliance_service, sample_vulnerabilities):
    """Test getting a compliance report summary"""
    # Generate a compliance report
    report = await compliance_service.generate_compliance_report(
        repository_url="https://github.com/example/repo",
        commit_sha="1234567890abcdef",
        standards=[ComplianceStandard.PCI_DSS, ComplianceStandard.OWASP_TOP_10],
        vulnerabilities=sample_vulnerabilities,
        include_vulnerability_details=True
    )
    
    # Get the summary
    summary = compliance_service.get_compliance_report_summary(report)
    
    # Verify the summary
    assert summary.id == report.id
    assert summary.target == report.target
    assert set(summary.standards) == {ComplianceStandard.PCI_DSS, ComplianceStandard.OWASP_TOP_10}
    assert summary.overall_status in [ComplianceStatus.COMPLIANT, ComplianceStatus.PARTIALLY_COMPLIANT, ComplianceStatus.NON_COMPLIANT]
    assert summary.critical_violations >= 0
    assert summary.high_violations >= 0
    assert summary.summary == report.summary

@pytest.mark.asyncio
async def test_update_from_additional_sources(compliance_service, mock_vuln_db, sample_db_entries):
    """Test updating from additional sources"""
    # Configure mocks
    mock_vuln_db._save_vulnerabilities.return_value = None
    
    # Mock the fetch methods
    with patch.object(compliance_service, 'fetch_from_nist_scap', return_value=sample_db_entries[:1]), \
         patch.object(compliance_service, 'fetch_from_oval', return_value=[]), \
         patch.object(compliance_service, 'fetch_from_capec', return_value=[]), \
         patch.object(compliance_service, 'fetch_from_epss', return_value=[]), \
         patch.object(compliance_service, 'fetch_from_cert_cc', return_value=sample_db_entries[1:]):
        
        # Update from additional sources
        result = await compliance_service.update_from_additional_sources(days_back=30)
        
        # Verify the result
        assert result["status"] == "success"
        assert result["count"] == 2
        assert "nist_scap" in result["sources"]
        assert "cert_cc" in result["sources"]
        assert result["sources"]["nist_scap"]["count"] == 1
        assert result["sources"]["cert_cc"]["count"] == 1
        
        # Verify that the vulnerabilities were saved
        mock_vuln_db._save_vulnerabilities.assert_called()

@pytest.mark.asyncio
async def test_security_coordinator_integration(temp_db_path):
    """Test integration with the security coordinator"""
    # Create a security coordinator with a mock vulnerability database
    with patch('services.security-enforcement.services.security_coordinator.VulnerabilityDatabase') as mock_db_class, \
         patch('services.security-enforcement.services.security_coordinator.ComplianceReportingService') as mock_service_class, \
         patch('services.security-enforcement.services.security_coordinator.TrivyScanner'), \
         patch('services.security-enforcement.services.security_coordinator.SnykScanner'), \
         patch('services.security-enforcement.services.security_coordinator.ZAPScanner'):
        
        # Configure mocks
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        
        mock_service = MagicMock()
        mock_service.generate_compliance_report = AsyncMock(return_value=ComplianceReport(
            id="CR-20250225-12345678",
            timestamp=datetime.utcnow(),
            target="https://github.com/example/repo@1234567890abcdef",
            standards=[ComplianceStandard.PCI_DSS, ComplianceStandard.OWASP_TOP_10],
            violations=[]
        ))
        mock_service.get_compliance_report_summary = MagicMock(return_value=ComplianceReportSummary(
            id="CR-20250225-12345678",
            timestamp=datetime.utcnow(),
            target="https://github.com/example/repo@1234567890abcdef",
            standards=[ComplianceStandard.PCI_DSS, ComplianceStandard.OWASP_TOP_10],
            overall_status=ComplianceStatus.COMPLIANT,
            summary={},
            critical_violations=0,
            high_violations=0
        ))
        mock_service_class.return_value = mock_service
        
        # Create the security coordinator
        coordinator = SecurityCoordinator()
        
        # Mock the run_security_scan method
        coordinator.run_security_scan = AsyncMock(return_value={
            "status": "success",
            "report": {
                "vulnerabilities": []
            }
        })
        
        # Generate a compliance report
        request = ComplianceReportRequest(
            repository_url="https://github.com/example/repo",
            commit_sha="1234567890abcdef",
            standards=[ComplianceStandard.PCI_DSS, ComplianceStandard.OWASP_TOP_10],
            include_vulnerabilities=True
        )
        
        with patch('builtins.open', MagicMock()), \
             patch('os.makedirs', MagicMock()):
            result = await coordinator.generate_compliance_report(request)
        
        # Verify the result
        assert result["status"] == "success"
        assert "report_id" in result
        assert "summary" in result
