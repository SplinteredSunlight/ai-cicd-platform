import pytest
import asyncio
from datetime import datetime
import os
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock

from ..models.vulnerability import Vulnerability, SeverityLevel, VulnerabilityReport
from ..models.vulnerability_database import (
    VulnerabilityDatabaseEntry,
    VulnerabilityDatabaseQuery,
    VulnerabilityStatus,
    VulnerabilitySource
)
from ..services.security_coordinator import SecurityCoordinator
from ..services.vulnerability_database import VulnerabilityDatabase

@pytest.fixture
def temp_db_path():
    """Create a temporary database file path"""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
def sample_vulnerability():
    """Create a sample vulnerability for testing"""
    return Vulnerability(
        id="CVE-2023-12345",
        title="Test Vulnerability",
        description="This is a test vulnerability",
        severity=SeverityLevel.HIGH,
        cvss_score=8.5,
        affected_component="test-package@1.0.0",
        fix_version="1.1.0",
        references=["https://example.com/cve-2023-12345"]
    )

@pytest.fixture
def sample_db_entry(sample_vulnerability):
    """Create a sample database entry for testing"""
    return VulnerabilityDatabaseEntry(
        vulnerability=sample_vulnerability,
        sources=[VulnerabilitySource.NVD],
        status=VulnerabilityStatus.ACTIVE,
        affected_versions=["1.0.0"],
        fixed_versions=["1.1.0"],
        published_date=datetime.utcnow(),
        last_updated=datetime.utcnow(),
        cwe_ids=["CWE-79"],
        tags={"xss", "web"},
        notes="Test notes"
    )

@pytest.fixture
def mock_coordinator():
    """Create a mock security coordinator with patched methods"""
    with patch('asyncio.create_task'), \
         patch.object(VulnerabilityDatabase, 'initialize_database'), \
         patch.object(VulnerabilityDatabase, 'update_database'):
        coordinator = SecurityCoordinator()
        # Replace the vulnerability database with a mock
        coordinator.vuln_db = MagicMock()
        coordinator.vuln_db.get_vulnerability = AsyncMock()
        coordinator.vuln_db.add_custom_vulnerability = AsyncMock()
        coordinator.vuln_db.search_vulnerabilities = AsyncMock()
        coordinator.vuln_db.get_database_stats = AsyncMock()
        coordinator.vuln_db.update_vulnerability_status = AsyncMock()
        yield coordinator

@pytest.mark.asyncio
async def test_enrich_vulnerabilities_with_database(mock_coordinator, sample_vulnerability, sample_db_entry):
    """Test enriching vulnerabilities with database information"""
    # Setup mock to return a database entry
    mock_coordinator.vuln_db.get_vulnerability.return_value = sample_db_entry
    
    # Create a vulnerability with minimal information
    minimal_vuln = Vulnerability(
        id="CVE-2023-12345",
        title="",
        description="",
        severity=SeverityLevel.MEDIUM,
        cvss_score=5.0,
        affected_component="test-package@1.0.0",
        fix_version=None,
        references=[]
    )
    
    # Enrich the vulnerability
    enriched_vulns = await mock_coordinator.enrich_vulnerabilities_with_database([minimal_vuln])
    
    # Check if the vulnerability was enriched
    assert len(enriched_vulns) == 1
    enriched = enriched_vulns[0]
    
    # Check if fields were updated
    assert enriched.title == sample_vulnerability.title
    assert enriched.description == sample_vulnerability.description
    assert enriched.fix_version == sample_vulnerability.fix_version
    assert enriched.references == sample_vulnerability.references
    
    # Check if metadata was added
    assert hasattr(enriched, "metadata")
    assert "vuln_db_status" in enriched.metadata
    assert enriched.metadata["vuln_db_status"] == VulnerabilityStatus.ACTIVE
    assert "cwe_ids" in enriched.metadata
    assert enriched.metadata["cwe_ids"] == ["CWE-79"]
    
    # Check if severity was updated (since database has higher CVSS score)
    assert enriched.severity == SeverityLevel.HIGH
    assert enriched.cvss_score == 8.5

@pytest.mark.asyncio
async def test_store_vulnerabilities_in_database(mock_coordinator, sample_vulnerability):
    """Test storing vulnerabilities in the database"""
    # Setup mock to return None (vulnerability not in database)
    mock_coordinator.vuln_db.get_vulnerability.return_value = None
    
    # Store the vulnerability
    await mock_coordinator._store_vulnerabilities_in_database([sample_vulnerability])
    
    # Check if add_custom_vulnerability was called
    mock_coordinator.vuln_db.add_custom_vulnerability.assert_called_once()
    
    # Check the arguments
    args, _ = mock_coordinator.vuln_db.add_custom_vulnerability.call_args
    entry = args[0]
    
    # Check if the entry has the correct vulnerability
    assert entry.vulnerability.id == sample_vulnerability.id
    assert entry.vulnerability.title == sample_vulnerability.title
    
    # Check if the entry has the correct metadata
    assert entry.sources == [VulnerabilitySource.INTERNAL]
    assert entry.status == VulnerabilityStatus.ACTIVE
    assert entry.fixed_versions == [sample_vulnerability.fix_version]

@pytest.mark.asyncio
async def test_update_vulnerability_database(mock_coordinator):
    """Test updating the vulnerability database"""
    # Setup mock to return a success result
    mock_coordinator.vuln_db.update_database.return_value = {
        "status": "success",
        "sources": {
            "NVD": {"status": "success", "count": 10},
            "GITHUB": {"status": "success", "count": 5},
            "SNYK": {"status": "success", "count": 8}
        }
    }
    
    # Update the database
    result = await mock_coordinator.update_vulnerability_database(
        sources=["NVD", "GITHUB", "SNYK"],
        force=True
    )
    
    # Check if update_database was called with the correct arguments
    mock_coordinator.vuln_db.update_database.assert_called_once()
    args, kwargs = mock_coordinator.vuln_db.update_database.call_args
    
    # Check sources
    assert len(kwargs["sources"]) == 3
    assert VulnerabilitySource.NVD in kwargs["sources"]
    assert VulnerabilitySource.GITHUB in kwargs["sources"]
    assert VulnerabilitySource.SNYK in kwargs["sources"]
    
    # Check force
    assert kwargs["force"] == True
    
    # Check result
    assert result["status"] == "success"
    assert "sources" in result
    assert len(result["sources"]) == 3

@pytest.mark.asyncio
async def test_search_vulnerability_database(mock_coordinator):
    """Test searching the vulnerability database"""
    # Setup mock to return search results
    mock_coordinator.vuln_db.search_vulnerabilities.return_value = [
        VulnerabilityDatabaseEntry(
            vulnerability=Vulnerability(
                id="CVE-2023-12345",
                title="Test Vulnerability",
                description="This is a test vulnerability",
                severity=SeverityLevel.HIGH,
                cvss_score=8.5,
                affected_component="test-package@1.0.0",
                fix_version="1.1.0",
                references=[]
            ),
            sources=[VulnerabilitySource.NVD],
            status=VulnerabilityStatus.ACTIVE,
            last_updated=datetime.utcnow()
        )
    ]
    
    # Create a query
    query = VulnerabilityDatabaseQuery(
        cve_id="CVE-2023",
        severity=[SeverityLevel.HIGH],
        limit=10
    )
    
    # Search the database
    results = await mock_coordinator.search_vulnerability_database(query)
    
    # Check if search_vulnerabilities was called with the correct query
    mock_coordinator.vuln_db.search_vulnerabilities.assert_called_once_with(query)
    
    # Check results
    assert len(results) == 1
    assert results[0].vulnerability.id == "CVE-2023-12345"
    assert results[0].vulnerability.severity == SeverityLevel.HIGH

@pytest.mark.asyncio
async def test_get_vulnerability_database_stats(mock_coordinator):
    """Test getting vulnerability database statistics"""
    # Setup mock to return statistics
    from ..models.vulnerability_database import VulnerabilityDatabaseStats
    
    stats = VulnerabilityDatabaseStats(
        total_entries=100,
        by_severity={
            SeverityLevel.CRITICAL: 10,
            SeverityLevel.HIGH: 20,
            SeverityLevel.MEDIUM: 30,
            SeverityLevel.LOW: 40
        },
        by_status={
            VulnerabilityStatus.ACTIVE: 80,
            VulnerabilityStatus.FIXED: 20
        },
        by_source={
            VulnerabilitySource.NVD: 50,
            VulnerabilitySource.GITHUB: 30,
            VulnerabilitySource.SNYK: 20
        },
        last_updated=datetime.utcnow()
    )
    
    mock_coordinator.vuln_db.get_database_stats.return_value = stats
    
    # Get statistics
    result = await mock_coordinator.get_vulnerability_database_stats()
    
    # Check if get_database_stats was called
    mock_coordinator.vuln_db.get_database_stats.assert_called_once()
    
    # Check result
    assert result.total_entries == 100
    assert result.by_severity[SeverityLevel.CRITICAL] == 10
    assert result.by_status[VulnerabilityStatus.ACTIVE] == 80
    assert result.by_source[VulnerabilitySource.NVD] == 50

@pytest.mark.asyncio
async def test_run_security_scan_with_vuln_db_integration(mock_coordinator):
    """Test running a security scan with vulnerability database integration"""
    # Setup mocks for scan methods
    mock_coordinator.trivy = MagicMock()
    mock_coordinator.trivy.scan_container = AsyncMock()
    
    # Create a vulnerability report
    vuln = Vulnerability(
        id="CVE-2023-12345",
        title="Test Vulnerability",
        description="This is a test vulnerability",
        severity=SeverityLevel.HIGH,
        cvss_score=8.5,
        affected_component="test-package@1.0.0",
        fix_version=None,
        references=[]
    )
    
    report = VulnerabilityReport(
        scanner_name="trivy",
        scan_timestamp=datetime.utcnow().isoformat() + "Z",
        target="test-image:latest",
        vulnerabilities=[vuln]
    )
    
    # Setup mock to return the report
    mock_coordinator.trivy.scan_container.return_value = report
    
    # Setup mock for enrich_vulnerabilities_with_database
    enriched_vuln = Vulnerability(
        id="CVE-2023-12345",
        title="Enriched Vulnerability",
        description="This is an enriched vulnerability",
        severity=SeverityLevel.CRITICAL,
        cvss_score=9.5,
        affected_component="test-package@1.0.0",
        fix_version="1.1.0",
        references=["https://example.com/cve-2023-12345"]
    )
    
    # Add metadata to the enriched vulnerability
    enriched_vuln.metadata = {
        "vuln_db_status": VulnerabilityStatus.ACTIVE,
        "vuln_db_sources": [VulnerabilitySource.NVD.value],
        "cwe_ids": ["CWE-79"],
        "affected_versions": ["1.0.0"],
        "fixed_versions": ["1.1.0"]
    }
    
    # Patch the enrich_vulnerabilities_with_database method
    original_enrich = mock_coordinator.enrich_vulnerabilities_with_database
    mock_coordinator.enrich_vulnerabilities_with_database = AsyncMock(return_value=[enriched_vuln])
    
    # Patch the _store_vulnerabilities_in_database method
    original_store = mock_coordinator._store_vulnerabilities_in_database
    mock_coordinator._store_vulnerabilities_in_database = AsyncMock()
    
    # Patch the _create_consolidated_report method
    original_create = mock_coordinator._create_consolidated_report
    mock_coordinator._create_consolidated_report = MagicMock()
    mock_coordinator._create_consolidated_report.return_value = report
    
    # Patch the _check_security_threshold method
    original_check = mock_coordinator._check_security_threshold
    mock_coordinator._check_security_threshold = MagicMock(return_value=True)
    
    # Patch the generate_and_sign_sbom method
    original_generate = mock_coordinator.generate_and_sign_sbom
    mock_coordinator.generate_and_sign_sbom = AsyncMock(return_value=("sbom.json", "sbom.json.sig"))
    
    try:
        # Run the security scan
        result = await mock_coordinator.run_security_scan(
            repository_url="https://github.com/test/repo",
            commit_sha="1234567890abcdef",
            artifact_url="test-image:latest",
            scan_types=["trivy"],
            blocking_severity=SeverityLevel.HIGH
        )
        
        # Check if trivy.scan_container was called
        mock_coordinator.trivy.scan_container.assert_called_once_with("test-image:latest")
        
        # Check if enrich_vulnerabilities_with_database was called
        mock_coordinator.enrich_vulnerabilities_with_database.assert_called_once()
        
        # Check if _store_vulnerabilities_in_database was called
        mock_coordinator._store_vulnerabilities_in_database.assert_called_once()
        
        # Check if _create_consolidated_report was called with enriched vulnerabilities
        args, _ = mock_coordinator._create_consolidated_report.call_args
        assert args[0] == [enriched_vuln]
        
        # Check result
        assert result["status"] == "success"
        assert result["passed"] == True
        assert "report" in result
        assert "sbom_url" in result
        assert "signature_url" in result
    
    finally:
        # Restore original methods
        mock_coordinator.enrich_vulnerabilities_with_database = original_enrich
        mock_coordinator._store_vulnerabilities_in_database = original_store
        mock_coordinator._create_consolidated_report = original_create
        mock_coordinator._check_security_threshold = original_check
        mock_coordinator.generate_and_sign_sbom = original_generate
