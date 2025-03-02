import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Set, Callable, Union
import uuid
from datetime import datetime
from enum import Enum

import socketio
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..models.gateway_models import UserInfo
from ..services.auth_service import get_current_user

logger = logging.getLogger(__name__)

class EventPriority(str, Enum):
    """Priority levels for WebSocket events"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class EventCategory(str, Enum):
    """Categories for WebSocket events"""
    PIPELINE = "pipeline"
    SECURITY = "security"
    DEBUG = "debug"
    SYSTEM = "system"
    ARCHITECTURE = "architecture"
    USER = "user"

class WebSocketEvent(BaseModel):
    """Model for WebSocket events"""
    event_type: str
    data: Dict[str, Any]
    target_users: Optional[List[str]] = None  # If None, broadcast to all authenticated users
    target_roles: Optional[List[str]] = None  # If set, broadcast to users with these roles
    namespace: str = "/"
    priority: Optional[EventPriority] = None  # Priority for real-time events
    category: Optional[EventCategory] = None  # Category for event filtering
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class WebSocketService:
    """Service for handling WebSocket connections and events"""
    
    def __init__(self):
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins="*",  # TODO: Configure for production
            logger=True,
            engineio_logger=True
        )
        self.app = socketio.ASGIApp(self.sio)
        self.connected_users: Dict[str, Set[str]] = {}  # user_id -> set of sid
        self.user_roles: Dict[str, List[str]] = {}  # user_id -> list of roles
        self.sid_to_user: Dict[str, str] = {}  # sid -> user_id
        
        # Set up event handlers
        self.sio.on("connect", self.handle_connect)
        self.sio.on("disconnect", self.handle_disconnect)
        self.sio.on("authenticate", self.handle_authenticate)
        
    async def handle_connect(self, sid, environ):
        """Handle new connection"""
        logger.info(f"New connection: {sid}")
        # Authentication will be handled by the authenticate event
    
    async def handle_disconnect(self, sid):
        """Handle disconnection"""
        logger.info(f"Disconnected: {sid}")
        
        # Remove user from connected users
        if sid in self.sid_to_user:
            user_id = self.sid_to_user[sid]
            if user_id in self.connected_users:
                self.connected_users[user_id].remove(sid)
                if not self.connected_users[user_id]:
                    del self.connected_users[user_id]
            del self.sid_to_user[sid]
    
    async def handle_authenticate(self, sid, data):
        """Handle authentication"""
        token = data.get("token")
        if not token:
            await self.sio.emit("auth_error", {"message": "No token provided"}, room=sid)
            return
        
        try:
            # Verify token (this would use the auth_service in a real implementation)
            # For now, we'll just mock it
            user_id = str(uuid.uuid4())  # In real implementation, get from token
            roles = ["user"]  # In real implementation, get from token
            
            # Register user
            if user_id not in self.connected_users:
                self.connected_users[user_id] = set()
            self.connected_users[user_id].add(sid)
            self.sid_to_user[sid] = user_id
            self.user_roles[user_id] = roles
            
            # Send success response
            await self.sio.emit("authenticated", {"user_id": user_id}, room=sid)
            logger.info(f"User {user_id} authenticated with sid {sid}")
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            await self.sio.emit("auth_error", {"message": str(e)}, room=sid)
    
    async def emit_event(self, event: WebSocketEvent):
        """Emit an event to connected clients based on targeting criteria"""
        target_sids = set()
        
        # Determine target sids based on targeting criteria
        if event.target_users:
            # Target specific users
            for user_id in event.target_users:
                if user_id in self.connected_users:
                    target_sids.update(self.connected_users[user_id])
        elif event.target_roles:
            # Target users with specific roles
            for user_id, roles in self.user_roles.items():
                if any(role in event.target_roles for role in roles):
                    if user_id in self.connected_users:
                        target_sids.update(self.connected_users[user_id])
        else:
            # Broadcast to all authenticated users
            for sids in self.connected_users.values():
                target_sids.update(sids)
        
        # Prepare event data with priority if specified
        event_data = event.data
        if event.priority:
            event_data = {**event_data, "priority": event.priority}
        
        # Emit event to target sids
        for sid in target_sids:
            await self.sio.emit(
                event.event_type,
                event_data,
                room=sid,
                namespace=event.namespace
            )
        
        logger.info(f"Emitted event {event.event_type} to {len(target_sids)} clients")
    
    def register_event_handler(self, event_type: str, handler: Callable, namespace: str = "/"):
        """Register a handler for a custom event type"""
        self.sio.on(event_type, handler, namespace=namespace)
        
    async def emit_ml_classification(self, error_id: str, classifications: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit ML classification events"""
        await self.emit_event(WebSocketEvent(
            event_type="debug_ml_classification",
            data={
                "errorId": error_id,
                "classifications": classifications
            },
            target_users=target_users,
            priority=EventPriority.MEDIUM,
            category=EventCategory.DEBUG
        ))
        
    async def emit_ml_training_started(self, training_id: str, training_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit ML training started events"""
        await self.emit_event(WebSocketEvent(
            event_type="debug_ml_training_started",
            data={
                "trainingId": training_id,
                "training": training_data
            },
            target_users=target_users,
            priority=EventPriority.LOW,
            category=EventCategory.DEBUG
        ))
        
    async def emit_ml_training_progress(self, training_id: str, progress_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit ML training progress events"""
        await self.emit_event(WebSocketEvent(
            event_type="debug_ml_training_progress",
            data={
                "trainingId": training_id,
                "progress": progress_data
            },
            target_users=target_users,
            priority=EventPriority.LOW,
            category=EventCategory.DEBUG
        ))
        
    async def emit_ml_training_completed(self, training_id: str, result_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit ML training completed events"""
        await self.emit_event(WebSocketEvent(
            event_type="debug_ml_training_completed",
            data={
                "trainingId": training_id,
                "result": result_data
            },
            target_users=target_users,
            priority=EventPriority.MEDIUM,
            category=EventCategory.DEBUG
        ))
        
    async def emit_ml_model_evaluation(self, model_id: str, evaluation_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit ML model evaluation events"""
        await self.emit_event(WebSocketEvent(
            event_type="debug_ml_model_evaluation",
            data={
                "modelId": model_id,
                "evaluation": evaluation_data
            },
            target_users=target_users,
            priority=EventPriority.LOW,
            category=EventCategory.DEBUG
        ))
        
    async def emit_architecture_diagram(self, diagram_id: str, diagram_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit architecture diagram events"""
        await self.emit_event(WebSocketEvent(
            event_type="architecture_diagram_update",
            data={
                "diagramId": diagram_id,
                "diagram": diagram_data
            },
            target_users=target_users,
            priority=EventPriority.LOW,
            category=EventCategory.ARCHITECTURE
        ))
        
    async def emit_security_vulnerability_detected(self, vulnerability_id: str, vulnerability_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit security vulnerability detected events"""
        await self.emit_event(WebSocketEvent(
            event_type="security_vulnerability_detected",
            data={
                "vulnerabilityId": vulnerability_id,
                "vulnerability": vulnerability_data
            },
            target_users=target_users,
            priority=EventPriority.HIGH,
            category=EventCategory.SECURITY
        ))
        
    async def emit_security_vulnerability_updated(self, vulnerability_id: str, vulnerability_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit security vulnerability updated events"""
        await self.emit_event(WebSocketEvent(
            event_type="security_vulnerability_updated",
            data={
                "vulnerabilityId": vulnerability_id,
                "vulnerability": vulnerability_data
            },
            target_users=target_users,
            priority=EventPriority.MEDIUM,
            category=EventCategory.SECURITY
        ))
        
    async def emit_security_scan_started(self, scan_id: str, scan_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit security scan started events"""
        await self.emit_event(WebSocketEvent(
            event_type="security_scan_started",
            data={
                "scanId": scan_id,
                "scan": scan_data
            },
            target_users=target_users,
            priority=EventPriority.MEDIUM,
            category=EventCategory.SECURITY
        ))
        
    async def emit_security_scan_updated(self, scan_id: str, scan_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit security scan updated events"""
        await self.emit_event(WebSocketEvent(
            event_type="security_scan_updated",
            data={
                "scanId": scan_id,
                "scan": scan_data
            },
            target_users=target_users,
            priority=EventPriority.LOW,
            category=EventCategory.SECURITY
        ))
        
    async def emit_security_scan_completed(self, scan_id: str, scan_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit security scan completed events"""
        await self.emit_event(WebSocketEvent(
            event_type="security_scan_completed",
            data={
                "scanId": scan_id,
                "scan": scan_data
            },
            target_users=target_users,
            priority=EventPriority.MEDIUM,
            category=EventCategory.SECURITY
        ))
        
    # Pipeline events
    async def emit_pipeline_created(self, pipeline_id: str, pipeline_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit pipeline created events"""
        await self.emit_event(WebSocketEvent(
            event_type="pipeline_created",
            data={
                "pipelineId": pipeline_id,
                "pipeline": pipeline_data
            },
            target_users=target_users,
            priority=EventPriority.MEDIUM,
            category=EventCategory.PIPELINE
        ))
        
    async def emit_pipeline_updated(self, pipeline_id: str, pipeline_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit pipeline updated events"""
        await self.emit_event(WebSocketEvent(
            event_type="pipeline_updated",
            data={
                "pipelineId": pipeline_id,
                "pipeline": pipeline_data
            },
            target_users=target_users,
            priority=EventPriority.LOW,
            category=EventCategory.PIPELINE
        ))
        
    async def emit_pipeline_deleted(self, pipeline_id: str, target_users: Optional[List[str]] = None):
        """Helper method to emit pipeline deleted events"""
        await self.emit_event(WebSocketEvent(
            event_type="pipeline_deleted",
            data={
                "pipelineId": pipeline_id
            },
            target_users=target_users,
            priority=EventPriority.MEDIUM,
            category=EventCategory.PIPELINE
        ))
        
    async def emit_pipeline_execution_started(self, execution_id: str, pipeline_id: str, execution_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit pipeline execution started events"""
        await self.emit_event(WebSocketEvent(
            event_type="pipeline_execution_started",
            data={
                "executionId": execution_id,
                "pipelineId": pipeline_id,
                "execution": execution_data
            },
            target_users=target_users,
            priority=EventPriority.MEDIUM,
            category=EventCategory.PIPELINE
        ))
        
    async def emit_pipeline_execution_updated(self, execution_id: str, pipeline_id: str, execution_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit pipeline execution updated events"""
        await self.emit_event(WebSocketEvent(
            event_type="pipeline_execution_updated",
            data={
                "executionId": execution_id,
                "pipelineId": pipeline_id,
                "execution": execution_data
            },
            target_users=target_users,
            priority=EventPriority.LOW,
            category=EventCategory.PIPELINE
        ))
        
    async def emit_pipeline_execution_completed(self, execution_id: str, pipeline_id: str, execution_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit pipeline execution completed events"""
        await self.emit_event(WebSocketEvent(
            event_type="pipeline_execution_completed",
            data={
                "executionId": execution_id,
                "pipelineId": pipeline_id,
                "execution": execution_data
            },
            target_users=target_users,
            priority=EventPriority.HIGH,
            category=EventCategory.PIPELINE
        ))
        
    # Debug events
    async def emit_debug_session_created(self, session_id: str, session_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit debug session created events"""
        await self.emit_event(WebSocketEvent(
            event_type="debug_session_created",
            data={
                "sessionId": session_id,
                "session": session_data
            },
            target_users=target_users,
            priority=EventPriority.MEDIUM,
            category=EventCategory.DEBUG
        ))
        
    async def emit_debug_session_updated(self, session_id: str, session_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit debug session updated events"""
        await self.emit_event(WebSocketEvent(
            event_type="debug_session_updated",
            data={
                "sessionId": session_id,
                "session": session_data
            },
            target_users=target_users,
            priority=EventPriority.LOW,
            category=EventCategory.DEBUG
        ))
        
    async def emit_debug_error_detected(self, session_id: str, error_id: str, error_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit debug error detected events"""
        await self.emit_event(WebSocketEvent(
            event_type="debug_error_detected",
            data={
                "sessionId": session_id,
                "errorId": error_id,
                "error": error_data
            },
            target_users=target_users,
            priority=EventPriority.HIGH,
            category=EventCategory.DEBUG
        ))
        
    async def emit_debug_patch_generated(self, session_id: str, patch_id: str, patch_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit debug patch generated events"""
        await self.emit_event(WebSocketEvent(
            event_type="debug_patch_generated",
            data={
                "sessionId": session_id,
                "patchId": patch_id,
                "patch": patch_data
            },
            target_users=target_users,
            priority=EventPriority.MEDIUM,
            category=EventCategory.DEBUG
        ))
        
    async def emit_debug_patch_applied(self, session_id: str, patch_id: str, result_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit debug patch applied events"""
        await self.emit_event(WebSocketEvent(
            event_type="debug_patch_applied",
            data={
                "sessionId": session_id,
                "patchId": patch_id,
                "result": result_data
            },
            target_users=target_users,
            priority=EventPriority.HIGH,
            category=EventCategory.DEBUG
        ))
        
    async def emit_debug_patch_rollback(self, session_id: str, patch_id: str, result_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit debug patch rollback events"""
        await self.emit_event(WebSocketEvent(
            event_type="debug_patch_rollback",
            data={
                "sessionId": session_id,
                "patchId": patch_id,
                "result": result_data
            },
            target_users=target_users,
            priority=EventPriority.MEDIUM,
            category=EventCategory.DEBUG
        ))
        
    # System events
    async def emit_system_status_update(self, status_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit system status update events"""
        await self.emit_event(WebSocketEvent(
            event_type="system_status_update",
            data={
                "status": status_data
            },
            target_users=target_users,
            priority=EventPriority.LOW,
            category=EventCategory.SYSTEM
        ))
        
    async def emit_system_metrics_update(self, metrics_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit system metrics update events"""
        await self.emit_event(WebSocketEvent(
            event_type="system_metrics_update",
            data={
                "metrics": metrics_data
            },
            target_users=target_users,
            priority=EventPriority.LOW,
            category=EventCategory.SYSTEM
        ))
        
    async def emit_system_alert(self, alert_id: str, alert_data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """Helper method to emit system alert events"""
        await self.emit_event(WebSocketEvent(
            event_type="system_alert",
            data={
                "alertId": alert_id,
                "alert": alert_data
            },
            target_users=target_users,
            priority=EventPriority.HIGH,
            category=EventCategory.SYSTEM
        ))
    
    def mount_to_app(self, app: FastAPI, path: str = "/ws"):
        """Mount the Socket.IO ASGI app to the FastAPI app"""
        app.mount(path, self.app)
