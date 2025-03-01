import pytest
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

# Add the parent directory to sys.path to allow imports from the main application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.vulnerability import (
    Vulnerability, 
    VulnerabilityReport, 
    SeverityLevel
)
from config import get_settings, Environment

@pytest.fixture
def mock_settings():
    """
    Create a mock for the settings.
    """
    with patch('config.get_settings') as mock_get_settings:
        settings = get_settings()
        settings.environment = Environment.DEVELOPMENT
        settings.artifact_storage_path = tempfile.mkdtemp()
        mock_get_settings.return_value = settings
        yield settings

@pytest.fixture
def sample_vulnerabilities():
    """
    Create a list of sample vulnerabilities for testing.
    """
    return [
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
            id="CVE-2023-0002",
            title="Test Vulnerability 2",
            description="Test description 2",
            severity=SeverityLevel.MEDIUM,
            cvss_score=5.5,
            affected_component="test-component@2.0.0",
            fix_version="2.1.0",
            references=["https://example.com/cve-2023-0002"]
        ),
        Vulnerability(
            id="CVE-2023-0003",
            title="Test Vulnerability 3",
            description="Test description 3",
            severity=SeverityLevel.LOW,
            cvss_score=3.5,
            affected_component="test-component@3.0.0",
            fix_version="3.1.0",
            references=["https://example.com/cve-2023-0003"]
        ),
        Vulnerability(
            id="CVE-2023-0004",
            title="Test Vulnerability 4",
            description="Test description 4",
            severity=SeverityLevel.CRITICAL,
            cvss_score=9.5,
            affected_component="test-component@4.0.0",
            fix_version="4.1.0",
            references=["https://example.com/cve-2023-0004"]
        )
    ]

@pytest.fixture
def sample_vulnerability_report(sample_vulnerabilities):
    """
    Create a sample vulnerability report for testing.
    """
    report = VulnerabilityReport(
        scanner_name="test-scanner",
        scan_timestamp=datetime.utcnow().isoformat() + "Z",
        target="test-target",
        vulnerabilities=sample_vulnerabilities,
        metadata={
            "repository_url": "https://github.com/test/repo",
            "commit_sha": "abcdef123456",
            "environment": "development"
        }
    )
    report.update_summary()
    return report

@pytest.fixture
def mock_http_client():
    """
    Create a mock for HTTP clients.
    """
    with patch('httpx.AsyncClient') as mock:
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_instance.get.return_value = mock_response
        mock_instance.post.return_value = mock_response
        
        yield mock_instance
