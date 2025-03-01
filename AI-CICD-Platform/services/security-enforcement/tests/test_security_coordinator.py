import pytest
import sys
import os
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

# Add the parent directory to sys.path to allow imports from the main application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.security_coordinator import SecurityCoordinator
from models.vulnerability import (
    Vulnerability, 
    VulnerabilityReport, 
    SeverityLevel
)
from config import Environment, VULNERABILITY_THRESHOLDS

@pytest.fixture
def mock_trivy_scanner():
    """
    Create a mock for the TrivyScanner.
    """
    with patch('services.trivy_scanner.TrivyScanner', autospec=True) as mock:
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        
        # Mock the scan_container method
        mock_instance.scan_container.return_value = VulnerabilityReport(
            scanner_name="trivy",
            scan_timestamp=datetime.utcnow().isoformat() + "Z",
            target="test-container:latest",
            vulnerabilities=[
                Vulnerability(
                    id="CVE-2023-0001",
                    title="Test Vulnerability 1",
                    description="Test description 1",
                    severity=SeverityLevel.HIGH,
                    cvss_score=8.5,
                    affected_component="test-component@1.0.0",
                    fix_version="1.1.0",
                    references=["https://example.com/cve-2023-0001"]
                )
            ]
        )
        
        yield mock_instance

@pytest.fixture
def mock_snyk_scanner():
    """
    Create a mock for the SnykScanner.
    """
    with patch('services.snyk_scanner.SnykScanner', autospec=True) as mock:
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        
        # Mock the scan_project method
        mock_instance.scan_project.return_value = VulnerabilityReport(
            scanner_name="snyk",
            scan_timestamp=datetime.utcnow().isoformat() + "Z",
            target="test-repo",
            vulnerabilities=[
                Vulnerability(
                    id="SNYK-JS-2023-001",
                    title="Test Vulnerability 2",
                    description="Test description 2",
                    severity=SeverityLevel.MEDIUM,
                    cvss_score=5.5,
                    affected_component="npm-package@2.0.0",
                    fix_version="2.1.0",
                    references=["https://example.com/snyk-js-2023-001"]
                )
            ]
        )
        
        # Mock the scan_container method
        mock_instance.scan_container.return_value = VulnerabilityReport(
            scanner_name="snyk",
            scan_timestamp=datetime.utcnow().isoformat() + "Z",
            target="test-container:latest",
            vulnerabilities=[
                Vulnerability(
                    id="SNYK-CONTAINER-2023-001",
                    title="Test Vulnerability 3",
                    description="Test description 3",
                    severity=SeverityLevel.LOW,
                    cvss_score=3.5,
                    affected_component="container-component@3.0.0",
                    fix_version="3.1.0",
                    references=["https://example.com/snyk-container-2023-001"]
                )
            ]
        )
        
        yield mock_instance

@pytest.fixture
def mock_zap_scanner():
    """
    Create a mock for the ZAPScanner.
    """
    with patch('services.zap_scanner.ZAPScanner', autospec=True) as mock:
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        
        # Mock the connect method
        mock_instance.connect.return_value = None
        
        # Mock the scan_webapp method
        mock_instance.scan_webapp.return_value = VulnerabilityReport(
            scanner_name="zap",
            scan_timestamp=datetime.utcnow().isoformat() + "Z",
            target="https://test-webapp.com",
            vulnerabilities=[
                Vulnerability(
                    id="ZAP-2023-001",
                    title="Test Vulnerability 4",
                    description="Test description 4",
                    severity=SeverityLevel.CRITICAL,
                    cvss_score=9.5,
                    affected_component="webapp-component@4.0.0",
                    fix_version="4.1.0",
                    references=["https://example.com/zap-2023-001"]
                )
            ]
        )
        
        yield mock_instance

@pytest.fixture
def mock_signer():
    """
    Create a mock for the Sigstore Signer.
    """
    with patch('sigstore.sign.Signer', autospec=True) as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        
        # Mock the sign method
        mock_instance.sign = AsyncMock()
        mock_instance.sign.return_value = b"mock-signature"
        
        yield mock_instance

@pytest.fixture
def security_coordinator(mock_trivy_scanner, mock_snyk_scanner, mock_zap_scanner):
    """
    Create a SecurityCoordinator with mocked scanners.
    """
    with patch('services.security_coordinator.TrivyScanner', return_value=mock_trivy_scanner), \
         patch('services.security_coordinator.SnykScanner', return_value=mock_snyk_scanner), \
         patch('services.security_coordinator.ZAPScanner', return_value=mock_zap_scanner):
        
        coordinator = SecurityCoordinator()
        yield coordinator

def test_security_coordinator_initialization():
    """
    Test that the SecurityCoordinator can be initialized correctly.
    """
    coordinator = SecurityCoordinator()
    assert coordinator is not None
    assert hasattr(coordinator, 'trivy')
    assert hasattr(coordinator, 'snyk')
    assert hasattr(coordinator, 'zap')

@pytest.mark.asyncio
async def test_create_consolidated_report(security_coordinator):
    """
    Test creating a consolidated vulnerability report.
    """
    # Create test vulnerabilities
    vulnerabilities = [
        Vulnerability(
            id="CVE-2023-0001",
            title="Test Vulnerability 1",
            description="Test description 1",
            severity=SeverityLevel.HIGH,
            cvss_score=8.5,
            affected_component="test-component@1.0.0",
            fix_version="1.1.0",
            references=["https://example.com/cve-2023-0001"]
        ),
        Vulnerability(
            id="SNYK-JS-2023-001",
            title="Test Vulnerability 2",
            description="Test description 2",
            severity=SeverityLevel.MEDIUM,
            cvss_score=5.5,
            affected_component="npm-package@2.0.0",
            fix_version="2.1.0",
            references=["https://example.com/snyk-js-2023-001"]
        )
    ]
    
    # Create consolidated report
    report = security_coordinator._create_consolidated_report(
        vulnerabilities=vulnerabilities,
        repository_url="https://github.com/test/repo",
        commit_sha="abcdef123456"
    )
    
    # Verify the report
    assert isinstance(report, VulnerabilityReport)
    assert report.scanner_name == "security-coordinator"
    assert "https://github.com/test/repo@abcdef123456" in report.target
    assert len(report.vulnerabilities) == 2
    assert report.summary[SeverityLevel.HIGH] == 1
    assert report.summary[SeverityLevel.MEDIUM] == 1
    assert report.metadata["repository_url"] == "https://github.com/test/repo"
    assert report.metadata["commit_sha"] == "abcdef123456"

@pytest.mark.asyncio
async def test_check_security_threshold(security_coordinator):
    """
    Test checking security thresholds for vulnerabilities.
    """
    # Create a report with vulnerabilities below threshold
    report_below_threshold = VulnerabilityReport(
        scanner_name="test-scanner",
        scan_timestamp=datetime.utcnow().isoformat() + "Z",
        target="test-target",
        vulnerabilities=[
            Vulnerability(
                id="CVE-2023-0001",
                title="Test Vulnerability 1",
                description="Test description 1",
                severity=SeverityLevel.HIGH,
                cvss_score=8.5,
                affected_component="test-component@1.0.0",
                fix_version="1.1.0",
                references=[]
            )
        ]
    )
    report_below_threshold.update_summary()
    
    # Check if it passes the threshold
    result = security_coordinator._check_security_threshold(
        report=report_below_threshold,
        blocking_severity=SeverityLevel.HIGH
    )
    
    # Verify the result (should pass with 1 HIGH in development)
    assert result is True
    
    # Create a report with vulnerabilities above threshold
    report_above_threshold = VulnerabilityReport(
        scanner_name="test-scanner",
        scan_timestamp=datetime.utcnow().isoformat() + "Z",
        target="test-target",
        vulnerabilities=[
            Vulnerability(
                id="CVE-2023-0001",
                title="Test Vulnerability 1",
                description="Test description 1",
                severity=SeverityLevel.HIGH,
                cvss_score=8.5,
                affected_component="test-component@1.0.0",
                fix_version="1.1.0",
                references=[]
            ),
            Vulnerability(
                id="CVE-2023-0002",
                title="Test Vulnerability 2",
                description="Test description 2",
                severity=SeverityLevel.HIGH,
                cvss_score=8.0,
                affected_component="test-component@1.0.0",
                fix_version="1.1.0",
                references=[]
            ),
            Vulnerability(
                id="CVE-2023-0003",
                title="Test Vulnerability 3",
                description="Test description 3",
                severity=SeverityLevel.HIGH,
                cvss_score=7.5,
                affected_component="test-component@1.0.0",
                fix_version="1.1.0",
                references=[]
            )
        ]
    )
    report_above_threshold.update_summary()
    
    # Check if it passes the threshold
    result = security_coordinator._check_security_threshold(
        report=report_above_threshold,
        blocking_severity=SeverityLevel.HIGH
    )
    
    # Verify the result (should fail with 3 HIGH in development)
    assert result is False
    
    # Test with a different blocking severity
    result = security_coordinator._check_security_threshold(
        report=report_above_threshold,
        blocking_severity=SeverityLevel.CRITICAL
    )
    
    # Verify the result (should pass since we're only blocking on CRITICAL)
    assert result is True

@pytest.mark.asyncio
async def test_generate_and_sign_sbom(security_coordinator, mock_signer, tmp_path):
    """
    Test generating and signing an SBOM.
    """
    # Mock the artifact storage path
    security_coordinator.settings.artifact_storage_path = str(tmp_path)
    
    # Create a test vulnerability report
    report = VulnerabilityReport(
        scanner_name="test-scanner",
        scan_timestamp=datetime.utcnow().isoformat() + "Z",
        target="test-target",
        vulnerabilities=[
            Vulnerability(
                id="CVE-2023-0001",
                title="Test Vulnerability 1",
                description="Test description 1",
                severity=SeverityLevel.HIGH,
                cvss_score=8.5,
                affected_component="test-component@1.0.0",
                fix_version="1.1.0",
                references=["https://example.com/cve-2023-0001"]
            )
        ]
    )
    
    # Mock the Signer
    with patch('services.security_coordinator.Signer', return_value=mock_signer):
        # Generate and sign SBOM
        sbom_url, signature_url = await security_coordinator.generate_and_sign_sbom(
            repository_url="https://github.com/test/repo",
            commit_sha="abcdef123456",
            vulnerability_report=report
        )
    
    # Verify the results
    assert sbom_url is not None
    assert signature_url is not None
    assert "sbom-abcdef123456.json" in sbom_url
    assert "sbom-abcdef123456.json.sig" in signature_url
    
    # Verify the SBOM file was created
    assert os.path.exists(sbom_url)
    assert os.path.exists(signature_url)

@pytest.mark.asyncio
async def test_run_security_scan(security_coordinator):
    """
    Test running a full security scan.
    """
    # Mock the generate_and_sign_sbom method
    security_coordinator.generate_and_sign_sbom = AsyncMock()
    security_coordinator.generate_and_sign_sbom.return_value = ("sbom_url", "signature_url")
    
    # Run the security scan
    result = await security_coordinator.run_security_scan(
        repository_url="https://github.com/test/repo",
        commit_sha="abcdef123456",
        artifact_url="test-container:latest",
        scan_types=["trivy", "snyk", "zap"],
        blocking_severity=SeverityLevel.HIGH
    )
    
    # Verify the result
    assert result["status"] == "success"
    assert "passed" in result
    assert "report" in result
    assert "sbom_url" in result
    assert "signature_url" in result
    
    # Verify the scanners were called
    security_coordinator.trivy.scan_container.assert_called_once_with("test-container:latest")
    security_coordinator.snyk.scan_project.assert_called_once_with("https://github.com/test/repo")
    security_coordinator.snyk.scan_container.assert_called_once_with("test-container:latest")
    security_coordinator.zap.connect.assert_called_once()
    security_coordinator.zap.scan_webapp.assert_called_once_with("test-container:latest")

@pytest.mark.asyncio
async def test_run_security_scan_with_failures(security_coordinator):
    """
    Test running a security scan with scanner failures.
    """
    # Make one scanner fail
    security_coordinator.trivy.scan_container.side_effect = Exception("Scanner failure")
    
    # Mock the generate_and_sign_sbom method
    security_coordinator.generate_and_sign_sbom = AsyncMock()
    security_coordinator.generate_and_sign_sbom.return_value = ("sbom_url", "signature_url")
    
    # Run the security scan
    result = await security_coordinator.run_security_scan(
        repository_url="https://github.com/test/repo",
        commit_sha="abcdef123456",
        artifact_url="test-container:latest",
        scan_types=["trivy", "snyk"],  # Exclude ZAP to simplify
        blocking_severity=SeverityLevel.HIGH
    )
    
    # Verify the result - should still succeed overall but with fewer vulnerabilities
    assert result["status"] == "success"
    assert "passed" in result
    assert "report" in result
    
    # Verify the scanners were called
    security_coordinator.trivy.scan_container.assert_called_once_with("test-container:latest")
    security_coordinator.snyk.scan_project.assert_called_once_with("https://github.com/test/repo")
    security_coordinator.snyk.scan_container.assert_called_once_with("test-container:latest")

@pytest.mark.asyncio
async def test_run_security_scan_with_critical_vulnerability(security_coordinator):
    """
    Test running a security scan with a critical vulnerability.
    """
    # Make ZAP scanner return a critical vulnerability
    security_coordinator.zap.scan_webapp.return_value = VulnerabilityReport(
        scanner_name="zap",
        scan_timestamp=datetime.utcnow().isoformat() + "Z",
        target="https://test-webapp.com",
        vulnerabilities=[
            Vulnerability(
                id="ZAP-2023-001",
                title="Critical Vulnerability",
                description="Critical vulnerability description",
                severity=SeverityLevel.CRITICAL,
                cvss_score=9.8,
                affected_component="webapp-component@4.0.0",
                fix_version="4.1.0",
                references=["https://example.com/zap-2023-001"]
            )
        ]
    )
    
    # Run the security scan
    result = await security_coordinator.run_security_scan(
        repository_url="https://github.com/test/repo",
        commit_sha="abcdef123456",
        artifact_url="https://test-webapp.com",
        scan_types=["zap"],  # Only use ZAP scanner
        blocking_severity=SeverityLevel.HIGH  # Block on HIGH or worse
    )
    
    # Verify the result - should fail due to CRITICAL vulnerability
    assert result["status"] == "success"  # The scan itself succeeded
    assert result["passed"] is False  # But it didn't pass the security check
    assert "report" in result
    assert "sbom_url" not in result  # SBOM shouldn't be generated for failed scans
    assert "signature_url" not in result
