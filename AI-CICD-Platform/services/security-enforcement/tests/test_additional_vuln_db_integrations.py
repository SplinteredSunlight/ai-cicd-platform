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
from ..services.vulnerability_database import VulnerabilityDatabase
from ..services.cve_mitre_integration import CVEMitreIntegration
from ..services.osv_integration import OSVIntegration
from ..services.vulndb_integration import VulnDBIntegration

@pytest.fixture
def temp_db_path():
    """Create a temporary database file path"""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.mark.asyncio
@patch('aiohttp.ClientSession.post')
async def test_mitre_cve_integration(mock_post, temp_db_path):
    """Test the MITRE CVE integration"""
    # Create a mock response for the MITRE CVE API
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__aenter__.return_value = mock_response
    
    # Sample MITRE CVE data
    mitre_data = {
        "cveRecords": [
            {
                "cve": {
                    "id": "CVE-2023-MITRE-1",
                    "metadata": {
                        "datePublished": "2023-01-01T00:00:00Z",
                        "dateUpdated": "2023-01-02T00:00:00Z"
                    },
                    "descriptions": [
                        {
                            "lang": "en",
                            "value": "This is a test MITRE CVE vulnerability"
                        }
                    ],
                    "references": [
                        {
                            "url": "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-MITRE-1"
                        }
                    ],
                    "metrics": {
                        "cvssMetricV31": [
                            {
                                "cvssData": {
                                    "baseScore": 8.5,
                                    "attackVector": "NETWORK"
                                }
                            }
                        ]
                    },
                    "configurations": [
                        {
                            "nodes": [
                                {
                                    "cpeMatch": [
                                        {
                                            "criteria": "cpe:2.3:a:vendor:product:1.0:*:*:*:*:*:*:*"
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                    "weaknesses": [
                        {
                            "description": [
                                {
                                    "lang": "en",
                                    "value": "CWE-79"
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }
    
    mock_response.json.return_value = mitre_data
    mock_post.return_value = mock_response
    
    # Initialize the MITRE CVE integration
    mitre_integration = CVEMitreIntegration()
    
    # Fetch recent CVEs
    vulnerabilities = await mitre_integration.fetch_recent_cves(days_back=30)
    
    # Check if vulnerabilities were fetched
    assert len(vulnerabilities) == 1
    vuln = vulnerabilities[0]
    
    # Check vulnerability details
    assert vuln.vulnerability.id == "CVE-2023-MITRE-1"
    assert "This is a test MITRE CVE vulnerability" in vuln.vulnerability.description
    assert vuln.vulnerability.severity == SeverityLevel.HIGH
    assert vuln.vulnerability.cvss_score == 8.5
    assert "vendor:product" in vuln.vulnerability.affected_component
    assert VulnerabilitySource.OSINT in vuln.sources
    assert "mitre" in vuln.tags
    assert "cve" in vuln.tags
    assert "CWE-79" in vuln.cwe_ids

@pytest.mark.asyncio
@patch('aiohttp.ClientSession.post')
@patch('aiohttp.ClientSession.get')
async def test_osv_integration(mock_get, mock_post, temp_db_path):
    """Test the OSV integration"""
    # Create a mock response for the OSV API
    mock_post_response = MagicMock()
    mock_post_response.status = 200
    mock_post_response.__aenter__.return_value = mock_post_response
    
    # Sample OSV data for package query
    osv_data = {
        "vulns": [
            {
                "id": "GHSA-abcd-1234-5678",
                "aliases": ["CVE-2023-OSV-1"],
                "summary": "Test OSV Vulnerability",
                "details": "This is a test OSV vulnerability",
                "modified": "2023-01-02T00:00:00Z",
                "published": "2023-01-01T00:00:00Z",
                "references": [
                    {
                        "url": "https://osv.dev/vulnerability/GHSA-abcd-1234-5678"
                    }
                ],
                "affected": [
                    {
                        "package": {
                            "ecosystem": "npm",
                            "name": "test-package"
                        },
                        "ranges": [
                            {
                                "type": "SEMVER",
                                "events": [
                                    {
                                        "introduced": "1.0.0"
                                    },
                                    {
                                        "fixed": "1.1.0"
                                    }
                                ]
                            }
                        ],
                        "versions": ["1.0.0", "1.0.1"]
                    }
                ],
                "database_specific": {
                    "severity": "high"
                }
            }
        ]
    }
    
    mock_post_response.json.return_value = osv_data
    mock_post.return_value = mock_post_response
    
    # Create a mock response for the OSV API (GET)
    mock_get_response = MagicMock()
    mock_get_response.status = 200
    mock_get_response.__aenter__.return_value = mock_get_response
    
    # Sample OSV data for recent vulnerabilities
    osv_list_data = {
        "vulns": [
            {
                "id": "GHSA-abcd-1234-5678",
                "aliases": ["CVE-2023-OSV-1"],
                "modified": "2023-01-02T00:00:00Z"
            }
        ],
        "next_page_token": ""
    }
    
    mock_get_response.json.return_value = osv_list_data
    mock_get.return_value = mock_get_response
    
    # Initialize the OSV integration
    osv_integration = OSVIntegration()
    
    # Fetch vulnerabilities for a package
    vulnerabilities = await osv_integration.fetch_vulnerabilities_by_package("npm", "test-package")
    
    # Check if vulnerabilities were fetched
    assert len(vulnerabilities) == 1
    vuln = vulnerabilities[0]
    
    # Check vulnerability details
    assert vuln.vulnerability.id == "CVE-2023-OSV-1"
    assert vuln.vulnerability.title == "Test OSV Vulnerability"
    assert "This is a test OSV vulnerability" in vuln.vulnerability.description
    assert vuln.vulnerability.severity == SeverityLevel.HIGH
    assert vuln.vulnerability.cvss_score == 8.0  # Estimated from severity
    assert vuln.vulnerability.affected_component == "npm:test-package"
    assert vuln.vulnerability.fix_version == "1.1.0"
    assert VulnerabilitySource.OSINT in vuln.sources
    assert "osv" in vuln.tags
    assert "npm" in vuln.tags
    assert ">=1.0.0,<1.1.0" in vuln.affected_versions
    assert "1.1.0" in vuln.fixed_versions

@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_vulndb_integration(mock_get, temp_db_path):
    """Test the VulnDB integration"""
    # Create a mock response for the VulnDB API
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__aenter__.return_value = mock_response
    
    # Sample VulnDB data
    vulndb_data = {
        "results": [
            {
                "vulndb_id": 12345,
                "title": "Test VulnDB Vulnerability",
                "description": "This is a test VulnDB vulnerability",
                "disclosure_date": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-02T00:00:00Z",
                "ext_references": [
                    {
                        "type": "CVE",
                        "value": "CVE-2023-VULNDB-1",
                        "url": "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-VULNDB-1"
                    }
                ],
                "cvss_metrics": {
                    "cvss_v3": {
                        "score": 9.1,
                        "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
                    }
                },
                "products": [
                    {
                        "vendor": {
                            "name": "vendor"
                        },
                        "name": "product",
                        "versions": [
                            {
                                "name": "1.0.0"
                            }
                        ]
                    }
                ],
                "classifications": [
                    {
                        "type": "CWE",
                        "id": 79,
                        "name": "Cross-site Scripting"
                    }
                ],
                "solution": "Upgrade to version 1.1.0 or later",
                "keywords": ["xss", "web"]
            }
        ],
        "total_pages": 1
    }
    
    mock_response.json.return_value = vulndb_data
    mock_get.return_value = mock_response
    
    # Initialize the VulnDB integration with a mock settings object
    with patch('services.security-enforcement.services.vulndb_integration.get_settings') as mock_settings:
        mock_settings.return_value.vulndb_api_key = "test-api-key"
        
        vulndb_integration = VulnDBIntegration()
        
        # Fetch recent vulnerabilities
        vulnerabilities = await vulndb_integration.fetch_recent_vulnerabilities(days_back=30)
        
        # Check if vulnerabilities were fetched
        assert len(vulnerabilities) == 1
        vuln = vulnerabilities[0]
        
        # Check vulnerability details
        assert vuln.vulnerability.id == "CVE-2023-VULNDB-1"
        assert vuln.vulnerability.title == "Test VulnDB Vulnerability"
        assert "This is a test VulnDB vulnerability" in vuln.vulnerability.description
        assert vuln.vulnerability.severity == SeverityLevel.CRITICAL
        assert vuln.vulnerability.cvss_score == 9.1
        assert vuln.vulnerability.affected_component == "vendor:product"
        assert vuln.vulnerability.fix_version == "1.1.0"
        assert VulnerabilitySource.OSINT in vuln.sources
        assert "vulndb" in vuln.tags
        assert "xss" in vuln.tags
        assert "web" in vuln.tags
        assert "CWE-79" in vuln.cwe_ids
        assert "1.0.0" in vuln.affected_versions
        assert "1.1.0" in vuln.fixed_versions

@pytest.mark.asyncio
async def test_vulnerability_database_integration(temp_db_path):
    """Test the integration of new vulnerability database sources with the main VulnerabilityDatabase class"""
    # Create a database instance
    db = VulnerabilityDatabase(db_path=temp_db_path)
    
    # Patch the update methods
    with patch.object(db, '_update_from_mitre_cve', return_value={"status": "success", "count": 10}), \
         patch.object(db, '_update_from_osv', return_value={"status": "success", "count": 15}), \
         patch.object(db, '_update_from_vulndb', return_value={"status": "success", "count": 5}), \
         patch.object(db, '_update_from_vuldb', return_value={"status": "success", "count": 3}), \
         patch.object(db, '_update_from_exploit_db', return_value={"status": "success", "count": 2}), \
         patch.object(db, '_update_from_security_focus', return_value={"status": "skipped", "count": 0}), \
         patch.object(db, '_update_from_full_disclosure', return_value={"status": "skipped", "count": 0}):
        
        # Update from OSINT sources
        result = await db._update_from_osint()
        
        # Check the result
        assert result["status"] == "success"
        assert result["count"] == 35  # Sum of all sources
        assert "mitre-cve" in result["sources"]
        assert "osv" in result["sources"]
        assert "vulndb" in result["sources"]
        assert result["sources"]["mitre-cve"]["count"] == 10
        assert result["sources"]["osv"]["count"] == 15
        assert result["sources"]["vulndb"]["count"] == 5
