import pytest
import os
import json
from datetime import datetime
import asyncio

from ..services.rollback_service import (
    RollbackService,
    RollbackOperation,
    RollbackType,
    RollbackStatus,
    Snapshot
)

@pytest.fixture
def rollback_service():
    """
    Create a rollback service for testing
    """
    return RollbackService()

def test_rollback_type_enum():
    """
    Test the RollbackType enum
    """
    assert RollbackType.FULL == "FULL"
    assert RollbackType.PARTIAL == "PARTIAL"
    assert RollbackType.CUSTOM == "CUSTOM"

def test_rollback_status_enum():
    """
    Test the RollbackStatus enum
    """
    assert RollbackStatus.PENDING == "PENDING"
    assert RollbackStatus.IN_PROGRESS == "IN_PROGRESS"
    assert RollbackStatus.COMPLETED == "COMPLETED"
    assert RollbackStatus.FAILED == "FAILED"
    assert RollbackStatus.VERIFIED == "VERIFIED"
    assert RollbackStatus.VERIFICATION_FAILED == "VERIFICATION_FAILED"

def test_snapshot_creation():
    """
    Test creating a snapshot
    """
    snapshot = Snapshot(
        id="SNAPSHOT-20250301-12345678",
        workflow_id="WORKFLOW-20250301-12345678",
        action_id="ACTION-20250301-12345678",
        path="/path/to/file",
        content="Original content",
        created_at=datetime.utcnow(),
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "file_type": "json"
        }
    )
    
    assert snapshot.id == "SNAPSHOT-20250301-12345678"
    assert snapshot.workflow_id == "WORKFLOW-20250301-12345678"
    assert snapshot.action_id == "ACTION-20250301-12345678"
    assert snapshot.path == "/path/to/file"
    assert snapshot.content == "Original content"
    assert snapshot.created_at is not None
    assert snapshot.metadata["vulnerability_id"] == "CVE-2023-1234"
    assert snapshot.metadata["file_type"] == "json"

def test_snapshot_to_dict():
    """
    Test converting a snapshot to a dictionary
    """
    created_at = datetime.utcnow()
    
    snapshot = Snapshot(
        id="SNAPSHOT-20250301-12345678",
        workflow_id="WORKFLOW-20250301-12345678",
        action_id="ACTION-20250301-12345678",
        path="/path/to/file",
        content="Original content",
        created_at=created_at,
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "file_type": "json"
        }
    )
    
    snapshot_dict = snapshot.to_dict()
    
    assert snapshot_dict["id"] == "SNAPSHOT-20250301-12345678"
    assert snapshot_dict["workflow_id"] == "WORKFLOW-20250301-12345678"
    assert snapshot_dict["action_id"] == "ACTION-20250301-12345678"
    assert snapshot_dict["path"] == "/path/to/file"
    assert snapshot_dict["content"] == "Original content"
    assert snapshot_dict["created_at"] == created_at.isoformat()
    assert snapshot_dict["metadata"]["vulnerability_id"] == "CVE-2023-1234"
    assert snapshot_dict["metadata"]["file_type"] == "json"

def test_snapshot_from_dict():
    """
    Test creating a snapshot from a dictionary
    """
    created_at = datetime.utcnow()
    
    snapshot_dict = {
        "id": "SNAPSHOT-20250301-12345678",
        "workflow_id": "WORKFLOW-20250301-12345678",
        "action_id": "ACTION-20250301-12345678",
        "path": "/path/to/file",
        "content": "Original content",
        "created_at": created_at.isoformat(),
        "metadata": {
            "vulnerability_id": "CVE-2023-1234",
            "file_type": "json"
        }
    }
    
    snapshot = Snapshot.from_dict(snapshot_dict)
    
    assert snapshot.id == "SNAPSHOT-20250301-12345678"
    assert snapshot.workflow_id == "WORKFLOW-20250301-12345678"
    assert snapshot.action_id == "ACTION-20250301-12345678"
    assert snapshot.path == "/path/to/file"
    assert snapshot.content == "Original content"
    assert snapshot.created_at.isoformat() == created_at.isoformat()
    assert snapshot.metadata["vulnerability_id"] == "CVE-2023-1234"
    assert snapshot.metadata["file_type"] == "json"

def test_rollback_operation_creation():
    """
    Test creating a rollback operation
    """
    operation = RollbackOperation(
        id="ROLLBACK-20250301-12345678",
        workflow_id="WORKFLOW-20250301-12345678",
        action_id="ACTION-20250301-12345678",
        snapshot_id="SNAPSHOT-20250301-12345678",
        rollback_type=RollbackType.FULL,
        status=RollbackStatus.PENDING,
        created_at=datetime.utcnow(),
        completed_at=None,
        result=None,
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "reason": "Failed verification"
        }
    )
    
    assert operation.id == "ROLLBACK-20250301-12345678"
    assert operation.workflow_id == "WORKFLOW-20250301-12345678"
    assert operation.action_id == "ACTION-20250301-12345678"
    assert operation.snapshot_id == "SNAPSHOT-20250301-12345678"
    assert operation.rollback_type == RollbackType.FULL
    assert operation.status == RollbackStatus.PENDING
    assert operation.created_at is not None
    assert operation.completed_at is None
    assert operation.result is None
    assert operation.metadata["vulnerability_id"] == "CVE-2023-1234"
    assert operation.metadata["reason"] == "Failed verification"

def test_rollback_operation_to_dict():
    """
    Test converting a rollback operation to a dictionary
    """
    created_at = datetime.utcnow()
    
    operation = RollbackOperation(
        id="ROLLBACK-20250301-12345678",
        workflow_id="WORKFLOW-20250301-12345678",
        action_id="ACTION-20250301-12345678",
        snapshot_id="SNAPSHOT-20250301-12345678",
        rollback_type=RollbackType.FULL,
        status=RollbackStatus.PENDING,
        created_at=created_at,
        completed_at=None,
        result=None,
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "reason": "Failed verification"
        }
    )
    
    operation_dict = operation.to_dict()
    
    assert operation_dict["id"] == "ROLLBACK-20250301-12345678"
    assert operation_dict["workflow_id"] == "WORKFLOW-20250301-12345678"
    assert operation_dict["action_id"] == "ACTION-20250301-12345678"
    assert operation_dict["snapshot_id"] == "SNAPSHOT-20250301-12345678"
    assert operation_dict["rollback_type"] == RollbackType.FULL
    assert operation_dict["status"] == RollbackStatus.PENDING
    assert operation_dict["created_at"] == created_at.isoformat()
    assert operation_dict["completed_at"] is None
    assert operation_dict["result"] is None
    assert operation_dict["metadata"]["vulnerability_id"] == "CVE-2023-1234"
    assert operation_dict["metadata"]["reason"] == "Failed verification"

def test_rollback_operation_from_dict():
    """
    Test creating a rollback operation from a dictionary
    """
    created_at = datetime.utcnow()
    
    operation_dict = {
        "id": "ROLLBACK-20250301-12345678",
        "workflow_id": "WORKFLOW-20250301-12345678",
        "action_id": "ACTION-20250301-12345678",
        "snapshot_id": "SNAPSHOT-20250301-12345678",
        "rollback_type": RollbackType.FULL,
        "status": RollbackStatus.PENDING,
        "created_at": created_at.isoformat(),
        "completed_at": None,
        "result": None,
        "metadata": {
            "vulnerability_id": "CVE-2023-1234",
            "reason": "Failed verification"
        }
    }
    
    operation = RollbackOperation.from_dict(operation_dict)
    
    assert operation.id == "ROLLBACK-20250301-12345678"
    assert operation.workflow_id == "WORKFLOW-20250301-12345678"
    assert operation.action_id == "ACTION-20250301-12345678"
    assert operation.snapshot_id == "SNAPSHOT-20250301-12345678"
    assert operation.rollback_type == RollbackType.FULL
    assert operation.status == RollbackStatus.PENDING
    assert operation.created_at.isoformat() == created_at.isoformat()
    assert operation.completed_at is None
    assert operation.result is None
    assert operation.metadata["vulnerability_id"] == "CVE-2023-1234"
    assert operation.metadata["reason"] == "Failed verification"

def test_rollback_service_initialization(rollback_service):
    """
    Test initializing the rollback service
    """
    assert rollback_service is not None
    assert rollback_service.snapshots_dir is not None
    assert rollback_service.operations_dir is not None
    assert os.path.exists(rollback_service.snapshots_dir)
    assert os.path.exists(rollback_service.operations_dir)

@pytest.mark.asyncio
async def test_rollback_service_create_snapshot(rollback_service):
    """
    Test creating a snapshot
    """
    snapshot = await rollback_service.create_snapshot(
        workflow_id="WORKFLOW-20250301-12345678",
        action_id="ACTION-20250301-12345678",
        path="/path/to/file",
        content="Original content",
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "file_type": "json"
        }
    )
    
    assert snapshot is not None
    assert snapshot.workflow_id == "WORKFLOW-20250301-12345678"
    assert snapshot.action_id == "ACTION-20250301-12345678"
    assert snapshot.path == "/path/to/file"
    assert snapshot.content == "Original content"
    assert snapshot.created_at is not None
    assert snapshot.metadata["vulnerability_id"] == "CVE-2023-1234"
    assert snapshot.metadata["file_type"] == "json"
    
    # Check that the snapshot was saved
    saved_snapshot = await rollback_service.get_snapshot(snapshot.id)
    assert saved_snapshot is not None
    assert saved_snapshot.id == snapshot.id

@pytest.mark.asyncio
async def test_rollback_service_get_all_snapshots(rollback_service):
    """
    Test getting all snapshots
    """
    # Create a few snapshots
    snapshot1 = await rollback_service.create_snapshot(
        workflow_id="WORKFLOW-20250301-12345678",
        action_id="ACTION-20250301-12345678",
        path="/path/to/file1",
        content="Original content 1",
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "file_type": "json"
        }
    )
    
    snapshot2 = await rollback_service.create_snapshot(
        workflow_id="WORKFLOW-20250301-87654321",
        action_id="ACTION-20250301-87654321",
        path="/path/to/file2",
        content="Original content 2",
        metadata={
            "vulnerability_id": "CVE-2023-5678",
            "file_type": "yaml"
        }
    )
    
    # Get all snapshots
    snapshots = await rollback_service.get_all_snapshots()
    
    assert snapshots is not None
    assert len(snapshots) >= 2
    
    # Check that our snapshots are in the list
    snapshot_ids = [s.id for s in snapshots]
    assert snapshot1.id in snapshot_ids
    assert snapshot2.id in snapshot_ids

@pytest.mark.asyncio
async def test_rollback_service_create_rollback_operation(rollback_service):
    """
    Test creating a rollback operation
    """
    # Create a snapshot first
    snapshot = await rollback_service.create_snapshot(
        workflow_id="WORKFLOW-20250301-12345678",
        action_id="ACTION-20250301-12345678",
        path="/path/to/file",
        content="Original content",
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "file_type": "json"
        }
    )
    
    # Create a rollback operation
    operation = await rollback_service.create_rollback_operation(
        workflow_id="WORKFLOW-20250301-12345678",
        action_id="ACTION-20250301-12345678",
        snapshot_id=snapshot.id,
        rollback_type=RollbackType.FULL,
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "reason": "Failed verification"
        }
    )
    
    assert operation is not None
    assert operation.workflow_id == "WORKFLOW-20250301-12345678"
    assert operation.action_id == "ACTION-20250301-12345678"
    assert operation.snapshot_id == snapshot.id
    assert operation.rollback_type == RollbackType.FULL
    assert operation.status == RollbackStatus.PENDING
    assert operation.created_at is not None
    assert operation.completed_at is None
    assert operation.result is None
    assert operation.metadata["vulnerability_id"] == "CVE-2023-1234"
    assert operation.metadata["reason"] == "Failed verification"
    
    # Check that the operation was saved
    saved_operation = await rollback_service.get_rollback_operation(operation.id)
    assert saved_operation is not None
    assert saved_operation.id == operation.id

@pytest.mark.asyncio
async def test_rollback_service_get_all_rollback_operations(rollback_service):
    """
    Test getting all rollback operations
    """
    # Create a snapshot first
    snapshot = await rollback_service.create_snapshot(
        workflow_id="WORKFLOW-20250301-12345678",
        action_id="ACTION-20250301-12345678",
        path="/path/to/file",
        content="Original content",
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "file_type": "json"
        }
    )
    
    # Create a few rollback operations
    operation1 = await rollback_service.create_rollback_operation(
        workflow_id="WORKFLOW-20250301-12345678",
        action_id="ACTION-20250301-12345678",
        snapshot_id=snapshot.id,
        rollback_type=RollbackType.FULL,
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "reason": "Failed verification"
        }
    )
    
    operation2 = await rollback_service.create_rollback_operation(
        workflow_id="WORKFLOW-20250301-87654321",
        action_id="ACTION-20250301-87654321",
        snapshot_id=snapshot.id,
        rollback_type=RollbackType.PARTIAL,
        metadata={
            "vulnerability_id": "CVE-2023-5678",
            "reason": "Failed verification"
        }
    )
    
    # Get all operations
    operations = await rollback_service.get_all_rollback_operations()
    
    assert operations is not None
    assert len(operations) >= 2
    
    # Check that our operations are in the list
    operation_ids = [o.id for o in operations]
    assert operation1.id in operation_ids
    assert operation2.id in operation_ids

@pytest.mark.asyncio
async def test_rollback_service_update_rollback_operation_status(rollback_service):
    """
    Test updating a rollback operation status
    """
    # Create a snapshot first
    snapshot = await rollback_service.create_snapshot(
        workflow_id="WORKFLOW-20250301-12345678",
        action_id="ACTION-20250301-12345678",
        path="/path/to/file",
        content="Original content",
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "file_type": "json"
        }
    )
    
    # Create a rollback operation
    operation = await rollback_service.create_rollback_operation(
        workflow_id="WORKFLOW-20250301-12345678",
        action_id="ACTION-20250301-12345678",
        snapshot_id=snapshot.id,
        rollback_type=RollbackType.FULL,
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "reason": "Failed verification"
        }
    )
    
    # Update the operation status
    updated_operation = await rollback_service.update_rollback_operation_status(
        operation.id,
        RollbackStatus.IN_PROGRESS,
        {
            "progress": "25%"
        }
    )
    
    assert updated_operation is not None
    assert updated_operation.id == operation.id
    assert updated_operation.status == RollbackStatus.IN_PROGRESS
    assert updated_operation.result is not None
    assert updated_operation.result["progress"] == "25%"
    
    # Check that the operation was updated
    saved_operation = await rollback_service.get_rollback_operation(operation.id)
    assert saved_operation is not None
    assert saved_operation.id == operation.id
    assert saved_operation.status == RollbackStatus.IN_PROGRESS
    assert saved_operation.result is not None
    assert saved_operation.result["progress"] == "25%"
