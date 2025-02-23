from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn
import json
from typing import Optional, List
import asyncio

from .config import get_settings
from .models.pipeline_debug import (
    DebugSession,
    PipelineError,
    AnalysisResult,
    PatchSolution,
    DebugReport
)
from .services.log_analyzer import LogAnalyzer
from .services.auto_patcher import AutoPatcher
from .services.cli_debugger import CLIDebugger

# Configure structured logging
logger = structlog.get_logger()

app = FastAPI(
    title="Self-Healing Debugger Service",
    description="AI-powered pipeline debugging and auto-patching service",
    version="0.1.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DebugService:
    def __init__(self):
        self.settings = get_settings()
        self.log_analyzer = LogAnalyzer()
        self.auto_patcher = AutoPatcher()
        self.cli_debugger = CLIDebugger()
        self.active_sessions: Dict[str, DebugSession] = {}

    def get_log_analyzer(self) -> LogAnalyzer:
        return self.log_analyzer

    def get_auto_patcher(self) -> AutoPatcher:
        return self.auto_patcher

    def get_cli_debugger(self) -> CLIDebugger:
        return self.cli_debugger

debug_service = DebugService()

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "self-healing-debugger",
        "version": "0.1.0"
    }

@app.post("/api/v1/debug/analyze")
async def analyze_pipeline(
    pipeline_id: str,
    log_content: str,
    background_tasks: BackgroundTasks,
    log_analyzer: LogAnalyzer = Depends(debug_service.get_log_analyzer)
):
    """
    Analyze pipeline logs and identify errors
    """
    try:
        logger.info("analyzing_pipeline", pipeline_id=pipeline_id)
        
        errors = await log_analyzer.analyze_pipeline_logs(
            pipeline_id,
            log_content
        )
        
        # Schedule cleanup in background
        background_tasks.add_task(log_analyzer.cleanup)
        
        return JSONResponse(content={
            "status": "success",
            "pipeline_id": pipeline_id,
            "errors": [error.dict() for error in errors]
        })
    
    except Exception as e:
        logger.error("analysis_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/debug/patch")
async def generate_patch(
    error: PipelineError,
    context: Optional[dict] = None,
    auto_patcher: AutoPatcher = Depends(debug_service.get_auto_patcher)
):
    """
    Generate a patch solution for an error
    """
    try:
        logger.info("generating_patch", error_id=error.error_id)
        
        patch = await auto_patcher.generate_patch(
            error,
            context or {}
        )
        
        return JSONResponse(content=patch.dict())
    
    except Exception as e:
        logger.error("patch_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/debug/apply-patch")
async def apply_patch(
    patch: PatchSolution,
    dry_run: bool = True,
    auto_patcher: AutoPatcher = Depends(debug_service.get_auto_patcher)
):
    """
    Apply a patch solution
    """
    try:
        logger.info("applying_patch", 
                   solution_id=patch.solution_id,
                   dry_run=dry_run)
        
        success = await auto_patcher.apply_patch(patch, dry_run)
        
        return JSONResponse(content={
            "status": "success" if success else "failed",
            "dry_run": dry_run,
            "patch_id": patch.solution_id
        })
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("patch_application_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/debug/rollback")
async def rollback_patch(
    patch_id: str,
    auto_patcher: AutoPatcher = Depends(debug_service.get_auto_patcher)
):
    """
    Rollback an applied patch
    """
    try:
        logger.info("rolling_back_patch", patch_id=patch_id)
        
        success = await auto_patcher.rollback_patch(patch_id)
        
        return JSONResponse(content={
            "status": "success" if success else "failed",
            "patch_id": patch_id
        })
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("patch_rollback_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/debug-session")
async def websocket_debug_session(
    websocket: WebSocket,
    cli_debugger: CLIDebugger = Depends(debug_service.get_cli_debugger)
):
    """
    Interactive WebSocket debug session
    """
    await websocket.accept()
    
    try:
        # Get session parameters
        params = await websocket.receive_json()
        pipeline_id = params["pipeline_id"]
        log_content = params["log_content"]
        
        # Start debug session
        session = await cli_debugger.start_debug_session(
            pipeline_id,
            log_content
        )
        
        # Send session updates
        while True:
            if session.status == "completed":
                break
                
            # Send session state
            await websocket.send_json({
                "type": "session_update",
                "data": session.dict()
            })
            
            # Wait for commands
            data = await websocket.receive_json()
            command = data.get("command")
            
            if command == "exit":
                break
            
            # Process other commands...
            
    except Exception as e:
        logger.error("websocket_session_error", error=str(e))
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    
    finally:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
