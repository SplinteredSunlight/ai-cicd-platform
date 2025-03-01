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

@pytest.fixture
def temp_db_path():
    """Create a temporary database file path"""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
@patch('aiohttp.ClientSession.post')
async def test_update_from_osint(mock_post, mock_get, temp_db_path):
    """Test updating from OSINT sources"""
    # Create database
    db = VulnerabilityDatabase(db_path=temp_db_path)
    
    # Mock VulDB response
    vuldb_response = MagicMock()
    vuldb_response.status = 200
    vuldb_response.__aenter__.return_value = vuldb_response
    
    vuldb_data = {
        "result": [
            {
                "entry": {
                    "date": int(datetime.now().timestamp()),
                    "products": [
                        {
                            "type": "software",
                            "name": "test-product",
                            "version": "1.0.0"
                        }
                    ]
                },
                "source": {
                    "cve": {
                        "id": "CVE-2023-OSINT-1"
                    }
                },
                "title": {
                    "text": "Test VulDB Vulnerability"
                },
                "description": {
                    "text": "This is a test vulnerability from VulDB"
                },
                "cvss3": {
                    "score": "8.5"
                },
                "references": {
                    "url": [
                        {"url": "https://vuldb.com/?id.12345"}
                    ]
                }
            }
        ]
    }
    
    vuldb_response.json.return_value = vuldb_data
    mock_post.return_value = vuldb_response
    
    # Mock Exploit-DB response
    exploitdb_response = MagicMock()
    exploitdb_response.status = 200
    exploitdb_response.__aenter__.return_value = exploitdb_response
    
    # Create CSV data for Exploit-DB
    csv_data = """id,description,date,author,type,platform,port,cve,app
12345,"Test Exploit-DB Vulnerability",2023-01-01,test,remote,linux,0,CVE-2023-OSINT-2,test-app
"""
    
    exploitdb_response.text.return_value = csv_data
    mock_get.return_value = exploitdb_response
    
    # Patch the _update_from_security_focus and _update_from_full_disclosure methods
    with patch.object(db, '_update_from_security_focus', return_value={"status": "skipped", "count": 0}), \
         patch.object(db, '_update_from_full_disclosure', return_value={"status": "skipped", "count": 0}):
        
        # Update from OSINT
        result = await db._update_from_osint()
        
        # Check result
        assert result["status"] == "success"
        assert result["count"] == 2  # 1 from VulDB + 1 from Exploit-DB
        assert result["source"] == VulnerabilitySource.OSINT
        
        # Check if vulnerabilities were added
        vuldb_vuln = await db.get_vulnerability("CVE-2023-OSINT-1")
        assert vuldb_vuln is not None
        assert vuldb_vuln.vulnerability.title == "Test VulDB Vulnerability"
        assert vuldb_vuln.vulnerability.severity == SeverityLevel.HIGH
        assert vuldb_vuln.vulnerability.affected_component == "test-product"
        assert VulnerabilitySource.OSINT in vuldb_vuln.sources
        assert "vuldb" in vuldb_vuln.tags
        
        exploitdb_vuln = await db.get_vulnerability("CVE-2023-OSINT-2")
        assert exploitdb_vuln is not None
        assert exploitdb_vuln.vulnerability.title == "Test Exploit-DB Vulnerability"
        assert exploitdb_vuln.vulnerability.severity == SeverityLevel.HIGH
        assert exploitdb_vuln.vulnerability.affected_component == "test-app"
        assert VulnerabilitySource.OSINT in exploitdb_vuln.sources
        assert "exploit-db" in exploitdb_vuln.tags
        assert "exploit" in exploitdb_vuln.tags

@pytest.mark.asyncio
@patch('aiohttp.ClientSession.post')
async def test_update_from_vuldb(mock_post, temp_db_path):
    """Test updating from VulDB"""
    # Create database
    db = VulnerabilityDatabase(db_path=temp_db_path)
    
    # Mock VulDB response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__aenter__.return_value = mock_response
    
    # Sample VulDB data
    vuldb_data = {
        "result": [
            {
                "entry": {
                    "date": int(datetime.now().timestamp()),
                    "products": [
                        {
                            "type": "software",
                            "name": "test-product",
                            "version": "1.0.0"
                        }
                    ]
                },
                "source": {
                    "cve": {
                        "id": "CVE-2023-VULDB-1"
                    }
                },
                "title": {
                    "text": "Test VulDB Vulnerability"
                },
                "description": {
                    "text": "This is a test vulnerability from VulDB"
                },
                "cvss3": {
                    "score": "9.1"
                },
                "references": {
                    "url": [
                        {"url": "https://vuldb.com/?id.12345"}
                    ]
                }
            }
        ]
    }
    
    mock_response.json.return_value = vuldb_data
    mock_post.return_value = mock_response
    
    # Update from VulDB
    result = await db._update_from_vuldb(datetime.now() - timedelta(days=1))
    
    # Check result
    assert result["status"] == "success"
    assert result["count"] == 1
    
    # Check if vulnerability was added
    vuln = await db.get_vulnerability("CVE-2023-VULDB-1")
    assert vuln is not None
    assert vuln.vulnerability.title == "Test VulDB Vulnerability"
    assert vuln.vulnerability.severity == SeverityLevel.CRITICAL
    assert vuln.vulnerability.affected_component == "test-product"
    assert VulnerabilitySource.OSINT in vuln.sources
    assert "vuldb" in vuln.tags

@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_update_from_exploit_db(mock_get, temp_db_path):
    """Test updating from Exploit-DB"""
    # Create database
    db = VulnerabilityDatabase(db_path=temp_db_path)
    
    # Mock Exploit-DB response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__aenter__.return_value = mock_response
    
    # Create CSV data
    csv_data = """id,description,date,author,type,platform,port,cve,app
12345,"Test Exploit-DB Vulnerability",2023-01-01,test,remote,linux,0,CVE-2023-EXPLOITDB-1,test-app
"""
    
    mock_response.text.return_value = csv_data
    mock_get.return_value = mock_response
    
    # Update from Exploit-DB
    result = await db._update_from_exploit_db(datetime.now() - timedelta(days=1))
    
    # Check result
    assert result["status"] == "success"
    assert result["count"] == 1
    
    # Check if vulnerability was added
    vuln = await db.get_vulnerability("CVE-2023-EXPLOITDB-1")
    assert vuln is not None
    assert vuln.vulnerability.title == "Test Exploit-DB Vulnerability"
    assert vuln.vulnerability.severity == SeverityLevel.HIGH
    assert vuln.vulnerability.affected_component == "test-app"
    assert VulnerabilitySource.OSINT in vuln.sources
    assert "exploit-db" in vuln.tags
    assert "exploit" in vuln.tags

@pytest.mark.asyncio
async def test_update_from_security_focus(temp_db_path):
    """Test updating from SecurityFocus"""
    # Create database
    db = VulnerabilityDatabase(db_path=temp_db_path)
    
    # Update from SecurityFocus
    result = await db._update_from_security_focus(datetime.now() - timedelta(days=1))
    
    # Check result
    assert result["status"] == "skipped"
    assert "reason" in result
    assert result["count"] == 0

@pytest.mark.asyncio
async def test_update_from_full_disclosure(temp_db_path):
    """Test updating from Full Disclosure"""
    # Create database
    db = VulnerabilityDatabase(db_path=temp_db_path)
    
    # Update from Full Disclosure
    result = await db._update_from_full_disclosure(datetime.now() - timedelta(days=1))
    
    # Check result
    assert result["status"] == "skipped"
    assert "reason" in result
    assert result["count"] == 0
