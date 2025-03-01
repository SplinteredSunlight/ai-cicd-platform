import pytest
import asyncio
from datetime import datetime
import os
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock
import uuid
import json

from ..models.vulnerability import Vulnerability, SeverityLevel
from ..models.vulnerability_database import (
    VulnerabilityDatabaseEntry,
    VulnerabilityStatus,
    VulnerabilitySource
)
from ..models.remediation import (
    RemediationAction,
    RemediationPlan,
    RemediationRequest,
    RemediationResult,
    RemediationStrategy,
    RemediationStatus,
    RemediationSource
)
from ..services.remediation_service import RemediationService
from ..services.vulnerability_database import VulnerabilityDatabase
from ..services.ncp_integration import NCPIntegration
from ..services.cert_integration import CERTIntegration
from ..services.oval_integration import OVALIntegration
from ..services.epss_integration import EPSSIntegration
from ..services.scap_integration import SCAPIntegration

@pytest.fixture
def temp_dir():
    """Create a temporary directory for remediation plans"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_vuln_db():
    """Create a mock vulnerability database"""
    mock_db = AsyncMock(spec=VulnerabilityDatabase)
    
    # Mock get_vulnerability
    async def mock_get_vulnerability(vuln_id):
        if vuln_id == "CVE-2023-12345":
            return VulnerabilityDatabaseEntry(
                vulnerability=Vulnerability(
                    id="CVE-2023-12345",
                    title="Test Vulnerability",
                    description="This is a test vulnerability",
                    severity=SeverityLevel.HIGH,
                    cvss_score=8.5,
                    affected_component="test-package@1.0.0",
                    fix_version="1.1.0",
                    references=["https://example.com/cve-2023-12345"]
                ),
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
        return None
    
    # Mock search_vulnerabilities
    async def mock_search_vulnerabilities(query):
        return [
            VulnerabilityDatabaseEntry(
                vulnerability=Vulnerability(
                    id="CVE-2023-12345",
                    title="Test Vulnerability",
                    description="This is a test vulnerability",
                    severity=SeverityLevel.HIGH,
                    cvss_score=8.5,
                    affected_component="test-package@1.0.0",
                    fix_version="1.1.0",
                    references=["https://example.com/cve-2023-12345"]
                ),
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
        ]
    
    # Mock update_vulnerability_status
    async def mock_update_vulnerability_status(vuln_id, status, notes):
        return True
    
    mock_db.get_vulnerability.side_effect = mock_get_vulnerability
    mock_db.search_vulnerabilities.side_effect = mock_search_vulnerabilities
    mock_db.update_vulnerability_status.side_effect = mock_update_vulnerability_status
    
    return mock_db

@pytest.fixture
def mock_ncp_integration():
    """Create a mock NCP integration"""
    mock_ncp = AsyncMock(spec=NCPIntegration)
    
    # Mock fetch_remediation_actions
    async def mock_fetch_remediation_actions(vuln_id):
        if vuln_id == "CVE-2023-12345":
            return [
                RemediationAction(
                    id=f"REM-NCP-{uuid.uuid4().hex[:8]}",
                    vulnerability_id=vuln_id,
                    strategy=RemediationStrategy.MITIGATE,
                    description="Apply NIST checklist: Test Checklist",
                    steps=["Step 1: Update configuration", "Step 2: Restart service"],
                    source=RemediationSource.NCP,
                    status=RemediationStatus.PENDING,
                    metadata={
                        "checklist_id": "CL12345",
                        "publication_date": "2023-01-01",
                        "target_products": ["Product A", "Product B"],
                        "content_url": "https://example.com/checklist"
                    }
                )
            ]
        return []
    
    mock_ncp.fetch_remediation_actions.side_effect = mock_fetch_remediation_actions
    
    return mock_ncp

@pytest.fixture
def mock_cert_integration():
    """Create a mock CERT integration"""
    mock_cert = AsyncMock(spec=CERTIntegration)
    
    # Mock fetch_remediation_actions
    async def mock_fetch_remediation_actions(vuln_id):
        if vuln_id == "CVE-2023-12345":
            return [
                RemediationAction(
                    id=f"REM-CERT-{uuid.uuid4().hex[:8]}",
                    vulnerability_id=vuln_id,
                    strategy=RemediationStrategy.UPGRADE,
                    description="Apply CERT/CC recommendation: Upgrade to version 1.1.0",
                    steps=["Step 1: Update dependency", "Step 2: Rebuild application"],
                    source=RemediationSource.CERT,
                    status=RemediationStatus.PENDING,
                    metadata={
                        "cert_id": "VU#12345",
                        "publication_date": "2023-01-01",
                        "update_date": "2023-01-02",
                        "severity": "HIGH",
                        "url": "https://kb.cert.org/vuls/id/12345"
                    }
                )
            ]
        return []
    
    mock_cert.fetch_remediation_actions.side_effect = mock_fetch_remediation_actions
    
    return mock_cert

@pytest.fixture
def mock_oval_integration():
    """Create a mock OVAL integration"""
    mock_oval = AsyncMock(spec=OVALIntegration)
    
    # Mock fetch_remediation_actions
    async def mock_fetch_remediation_actions(vuln_id):
        if vuln_id == "CVE-2023-12345":
            return [
                RemediationAction(
                    id=f"REM-OVAL-{uuid.uuid4().hex[:8]}",
                    vulnerability_id=vuln_id,
                    strategy=RemediationStrategy.PATCH,
                    description="Apply OVAL definition: Test Definition",
                    steps=["Step 1: Apply patch", "Step 2: Verify patch"],
                    source=RemediationSource.OVAL,
                    status=RemediationStatus.PENDING,
                    metadata={
                        "oval_id": "oval:org.mitre.oval:def:12345",
                        "class": "patch",
                        "platforms": ["Windows", "Linux"],
                        "references": []
                    }
                )
            ]
        return []
    
    mock_oval.fetch_remediation_actions.side_effect = mock_fetch_remediation_actions
    
    return mock_oval

@pytest.fixture
def mock_epss_integration():
    """Create a mock EPSS integration"""
    mock_epss = AsyncMock(spec=EPSSIntegration)
    
    # Mock fetch_remediation_actions
    async def mock_fetch_remediation_actions(vuln_id):
        if vuln_id == "CVE-2023-12345":
            return [
                RemediationAction(
                    id=f"REM-EPSS-{uuid.uuid4().hex[:8]}",
                    vulnerability_id=vuln_id,
                    strategy=RemediationStrategy.MITIGATE,
                    description="Prioritize remediation based on EPSS score: 0.8500 (percentile: 95.0)",
                    steps=[
                        "EPSS Score: 0.8500 (likelihood of exploitation)",
                        "Percentile: 95.0 (relative to other vulnerabilities)",
                        "Priority: CRITICAL",
                        "Date: 2023-01-01",
                        "Recommendation: Prioritize remediation based on EPSS score and other vulnerability characteristics."
                    ],
                    source=RemediationSource.EPSS,
                    status=RemediationStatus.PENDING,
                    metadata={
                        "epss_score": 0.85,
                        "percentile": 95.0,
                        "priority": "CRITICAL",
                        "date": "2023-01-01"
                    }
                )
            ]
        return []
    
    mock_epss.fetch_remediation_actions.side_effect = mock_fetch_remediation_actions
    
    return mock_epss

@pytest.fixture
def mock_scap_integration():
    """Create a mock SCAP integration"""
    mock_scap = AsyncMock(spec=SCAPIntegration)
    
    # Mock fetch_remediation_actions
    async def mock_fetch_remediation_actions(vuln_id):
        if vuln_id == "CVE-2023-12345":
            return [
                RemediationAction(
                    id=f"REM-SCAP-{uuid.uuid4().hex[:8]}",
                    vulnerability_id=vuln_id,
                    strategy=RemediationStrategy.MITIGATE,
                    description="Apply SCAP rule: Test Rule",
                    steps=["Step 1: Configure security settings", "Step 2: Verify configuration"],
                    source=RemediationSource.SCAP,
                    status=RemediationStatus.PENDING,
                    metadata={
                        "scap_content_id": "scap_org.open-scap_datastream_12345",
                        "rule_id": "xccdf_org.ssgproject.content_rule_12345",
                        "severity": "high",
                        "checks": []
                    }
                )
            ]
        return []
    
    mock_scap.fetch_remediation_actions.side_effect = mock_fetch_remediation_actions
    
    return mock_scap

@pytest.fixture
def remediation_service(
    temp_dir,
    mock_vuln_db,
    mock_ncp_integration,
    mock_cert_integration,
    mock_oval_integration,
    mock_epss_integration,
    mock_scap_integration
):
    """Create a remediation service with mocked dependencies"""
    with patch('services.security-enforcement.services.remediation_service.NCPIntegration', return_value=mock_ncp_integration), \
         patch('services.security-enforcement.services.remediation_service.CERTIntegration', return_value=mock_cert_integration), \
         patch('services.security-enforcement.services.remediation_service.OVALIntegration', return_value=mock_oval_integration), \
         patch('services.security-enforcement.services.remediation_service.EPSSIntegration', return_value=mock_epss_integration), \
         patch('services.security-enforcement.services.remediation_service.SCAPIntegration', return_value=mock_scap_integration), \
         patch('services.security-enforcement.services.remediation_service.get_settings') as mock_settings:
        
        mock_settings.return_value.artifact_storage_path = temp_dir
        
        service = RemediationService(vuln_db=mock_vuln_db)
        service.plans_dir = temp_dir
        
        yield service

@pytest.mark.asyncio
async def test_generate_remediation_plan(remediation_service):
    """Test generating a remediation plan"""
    # Create a remediation request
    request = RemediationRequest(
        repository_url="https://github.com/example/repo",
        commit_sha="abcdef123456",
        vulnerability_ids=["CVE-2023-12345"],
        auto_apply=False
    )
    
    # Generate a remediation plan
    plan = await remediation_service.generate_remediation_plan(request)
    
    # Check the plan
    assert plan is not None
    assert plan.id.startswith("PLAN-")
    assert plan.name == "Remediation Plan for https://github.com/example/repo"
    assert plan.target == "https://github.com/example/repo@abcdef123456"
    assert plan.status == RemediationStatus.PENDING
    assert len(plan.actions) > 0
    
    # Check that the plan was saved
    plan_path = os.path.join(remediation_service.plans_dir, f"{plan.id}.json")
    assert os.path.exists(plan_path)
    
    # Check the plan content
    with open(plan_path, "r") as f:
        plan_data = json.load(f)
        assert plan_data["id"] == plan.id
        assert plan_data["name"] == plan.name
        assert plan_data["target"] == plan.target
        assert plan_data["status"] == RemediationStatus.PENDING
        assert len(plan_data["actions"]) > 0

@pytest.mark.asyncio
async def test_get_remediation_plan(remediation_service):
    """Test getting a remediation plan"""
    # Create a remediation plan
    plan_id = f"PLAN-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
    plan = RemediationPlan(
        id=plan_id,
        name="Test Plan",
        description="Test Description",
        target="https://github.com/example/repo@abcdef123456",
        actions=[],
        status=RemediationStatus.PENDING
    )
    
    # Save the plan
    plan_path = os.path.join(remediation_service.plans_dir, f"{plan.id}.json")
    with open(plan_path, "w") as f:
        f.write(plan.json(indent=2))
    
    # Get the plan
    retrieved_plan = await remediation_service.get_remediation_plan(plan_id)
    
    # Check the plan
    assert retrieved_plan is not None
    assert retrieved_plan.id == plan_id
    assert retrieved_plan.name == "Test Plan"
    assert retrieved_plan.target == "https://github.com/example/repo@abcdef123456"
    assert retrieved_plan.status == RemediationStatus.PENDING

@pytest.mark.asyncio
async def test_apply_remediation_plan(remediation_service):
    """Test applying a remediation plan"""
    # Create a remediation plan with actions
    plan_id = f"PLAN-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
    action_id = f"REM-TEST-{uuid.uuid4().hex[:8]}"
    
    plan = RemediationPlan(
        id=plan_id,
        name="Test Plan",
        description="Test Description",
        target="https://github.com/example/repo@abcdef123456",
        actions=[
            RemediationAction(
                id=action_id,
                vulnerability_id="CVE-2023-12345",
                strategy=RemediationStrategy.UPGRADE,
                description="Upgrade to version 1.1.0",
                steps=["Step 1: Update dependency", "Step 2: Rebuild application"],
                source=RemediationSource.CERT,
                status=RemediationStatus.PENDING
            )
        ],
        status=RemediationStatus.PENDING
    )
    
    # Save the plan
    plan_path = os.path.join(remediation_service.plans_dir, f"{plan.id}.json")
    with open(plan_path, "w") as f:
        f.write(plan.json(indent=2))
    
    # Apply the plan
    results = await remediation_service.apply_remediation_plan(plan_id)
    
    # Check the results
    assert len(results) == 1
    assert results[0].action_id == action_id
    assert results[0].vulnerability_id == "CVE-2023-12345"
    assert results[0].success is True
    assert results[0].status == RemediationStatus.COMPLETED
    
    # Check that the vulnerability status was updated
    remediation_service.vuln_db.update_vulnerability_status.assert_called_once_with(
        "CVE-2023-12345",
        VulnerabilityStatus.MITIGATED,
        f"Automatically mitigated by remediation action {action_id}"
    )
    
    # Check that the plan was updated
    updated_plan = await remediation_service.get_remediation_plan(plan_id)
    assert updated_plan.status == RemediationStatus.COMPLETED
    assert updated_plan.actions[0].status == RemediationStatus.COMPLETED

@pytest.mark.asyncio
async def test_get_remediation_actions(remediation_service):
    """Test getting remediation actions for a vulnerability"""
    # Get remediation actions
    actions = await remediation_service.get_remediation_actions("CVE-2023-12345")
    
    # Check the actions
    assert len(actions) > 0
    for action in actions:
        assert action.vulnerability_id == "CVE-2023-12345"
        assert action.status == RemediationStatus.PENDING
        assert len(action.steps) > 0

@pytest.mark.asyncio
async def test_get_all_remediation_plans(remediation_service):
    """Test getting all remediation plans"""
    # Create some remediation plans
    plan_ids = []
    for i in range(3):
        plan_id = f"PLAN-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        plan_ids.append(plan_id)
        
        plan = RemediationPlan(
            id=plan_id,
            name=f"Test Plan {i}",
            description=f"Test Description {i}",
            target=f"https://github.com/example/repo{i}@abcdef123456",
            actions=[],
            status=RemediationStatus.PENDING
        )
        
        # Save the plan
        plan_path = os.path.join(remediation_service.plans_dir, f"{plan.id}.json")
        with open(plan_path, "w") as f:
            f.write(plan.json(indent=2))
    
    # Get all plans
    plans = await remediation_service.get_all_remediation_plans()
    
    # Check the plans
    assert len(plans) == 3
    for plan in plans:
        assert plan.id in plan_ids
        assert plan.name.startswith("Test Plan ")
        assert plan.target.startswith("https://github.com/example/repo")
        assert plan.status == RemediationStatus.PENDING

@pytest.mark.asyncio
async def test_deduplicate_actions(remediation_service):
    """Test deduplicating remediation actions"""
    # Create some actions with duplicates
    actions = [
        RemediationAction(
            id=f"REM-TEST-{uuid.uuid4().hex[:8]}",
            vulnerability_id="CVE-2023-12345",
            strategy=RemediationStrategy.UPGRADE,
            description="Upgrade to version 1.1.0",
            steps=["Step 1", "Step 2"],
            source=RemediationSource.CERT,
            status=RemediationStatus.PENDING
        ),
        RemediationAction(
            id=f"REM-TEST-{uuid.uuid4().hex[:8]}",
            vulnerability_id="CVE-2023-12345",
            strategy=RemediationStrategy.UPGRADE,
            description="Upgrade to version 1.1.0",  # Same description
            steps=["Step 3", "Step 4"],  # Different steps
            source=RemediationSource.CERT,
            status=RemediationStatus.PENDING
        ),
        RemediationAction(
            id=f"REM-TEST-{uuid.uuid4().hex[:8]}",
            vulnerability_id="CVE-2023-12345",
            strategy=RemediationStrategy.PATCH,  # Different strategy
            description="Apply patch",
            steps=["Step 5", "Step 6"],
            source=RemediationSource.OVAL,
            status=RemediationStatus.PENDING
        )
    ]
    
    # Deduplicate actions
    deduplicated = remediation_service._deduplicate_actions(actions)
    
    # Check the deduplicated actions
    assert len(deduplicated) == 2  # First two actions are duplicates
    assert deduplicated[0].strategy == RemediationStrategy.UPGRADE
    assert deduplicated[0].description == "Upgrade to version 1.1.0"
    assert deduplicated[1].strategy == RemediationStrategy.PATCH
    assert deduplicated[1].description == "Apply patch"
