"""
WebSocket Router

This module sets up the WebSocket router for the deployment automation service.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status

from config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create WebSocket router
websocket_router = APIRouter()

# Store active connections
active_connections: Dict[str, List[WebSocket]] = {}

async def get_token(websocket: WebSocket) -> Optional[str]:
    """
    Get the token from the WebSocket query parameters.
    
    Args:
        websocket (WebSocket): The WebSocket connection
        
    Returns:
        Optional[str]: The token if found, None otherwise
    """
    token = websocket.query_params.get("token")
    return token

async def get_client_id(websocket: WebSocket) -> str:
    """
    Get the client ID from the WebSocket query parameters.
    
    Args:
        websocket (WebSocket): The WebSocket connection
        
    Returns:
        str: The client ID
    """
    client_id = websocket.query_params.get("client_id", "anonymous")
    return client_id

async def authenticate(websocket: WebSocket) -> bool:
    """
    Authenticate the WebSocket connection.
    
    Args:
        websocket (WebSocket): The WebSocket connection
        
    Returns:
        bool: True if authenticated, False otherwise
    """
    # In a real implementation, this would validate the token
    # For now, we just check if a token is provided
    token = await get_token(websocket)
    return token is not None

@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.
    """
    # Accept the connection
    await websocket.accept()
    
    # Get client ID
    client_id = await get_client_id(websocket)
    
    # Authenticate
    is_authenticated = await authenticate(websocket)
    if not is_authenticated:
        await websocket.send_json({
            "type": "error",
            "message": "Authentication failed"
        })
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Add to active connections
    if client_id not in active_connections:
        active_connections[client_id] = []
    active_connections[client_id].append(websocket)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to deployment automation service"
        })
        
        # Handle messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await handle_message(websocket, client_id, message)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
    except WebSocketDisconnect:
        # Remove from active connections
        if client_id in active_connections:
            active_connections[client_id].remove(websocket)
            if not active_connections[client_id]:
                del active_connections[client_id]
        logger.info(f"Client disconnected: {client_id}")

async def handle_message(websocket: WebSocket, client_id: str, message: Dict[str, Any]):
    """
    Handle a WebSocket message.
    
    Args:
        websocket (WebSocket): The WebSocket connection
        client_id (str): The client ID
        message (Dict[str, Any]): The message
    """
    message_type = message.get("type")
    
    if message_type == "ping":
        await websocket.send_json({
            "type": "pong",
            "timestamp": message.get("timestamp")
        })
    elif message_type == "subscribe":
        topics = message.get("topics", [])
        await websocket.send_json({
            "type": "subscribed",
            "topics": topics
        })
    elif message_type == "unsubscribe":
        topics = message.get("topics", [])
        await websocket.send_json({
            "type": "unsubscribed",
            "topics": topics
        })
    else:
        await websocket.send_json({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        })

async def broadcast_to_client(client_id: str, message: Dict[str, Any]):
    """
    Broadcast a message to a specific client.
    
    Args:
        client_id (str): The client ID
        message (Dict[str, Any]): The message
    """
    if client_id in active_connections:
        for connection in active_connections[client_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")

async def broadcast_to_all(message: Dict[str, Any]):
    """
    Broadcast a message to all connected clients.
    
    Args:
        message (Dict[str, Any]): The message
    """
    for client_id in active_connections:
        await broadcast_to_client(client_id, message)

async def broadcast_deployment_update(deployment_id: str, status: str, details: Dict[str, Any]):
    """
    Broadcast a deployment update to all connected clients.
    
    Args:
        deployment_id (str): The deployment ID
        status (str): The deployment status
        details (Dict[str, Any]): The deployment details
    """
    message = {
        "type": "deployment_update",
        "deployment_id": deployment_id,
        "status": status,
        "details": details
    }
    await broadcast_to_all(message)

async def broadcast_approval_update(approval_id: str, status: str, details: Dict[str, Any]):
    """
    Broadcast an approval update to all connected clients.
    
    Args:
        approval_id (str): The approval ID
        status (str): The approval status
        details (Dict[str, Any]): The approval details
    """
    message = {
        "type": "approval_update",
        "approval_id": approval_id,
        "status": status,
        "details": details
    }
    await broadcast_to_all(message)

async def broadcast_rollback_update(rollback_id: str, status: str, details: Dict[str, Any]):
    """
    Broadcast a rollback update to all connected clients.
    
    Args:
        rollback_id (str): The rollback ID
        status (str): The rollback status
        details (Dict[str, Any]): The rollback details
    """
    message = {
        "type": "rollback_update",
        "rollback_id": rollback_id,
        "status": status,
        "details": details
    }
    await broadcast_to_all(message)

async def broadcast_monitoring_alert(alert_id: str, severity: str, message: str, details: Dict[str, Any]):
    """
    Broadcast a monitoring alert to all connected clients.
    
    Args:
        alert_id (str): The alert ID
        severity (str): The alert severity
        message (str): The alert message
        details (Dict[str, Any]): The alert details
    """
    alert_message = {
        "type": "monitoring_alert",
        "alert_id": alert_id,
        "severity": severity,
        "message": message,
        "details": details
    }
    await broadcast_to_all(alert_message)
