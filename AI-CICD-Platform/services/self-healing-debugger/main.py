from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import structlog
import uvicorn
import json
import os
from typing import Optional, List, Dict
import asyncio
from datetime import datetime

from config import get_settings
from models.pipeline_debug import (
    DebugSession,
    PipelineError,
    AnalysisResult,
    PatchSolution,
    DebugReport
)
from services.log_analyzer import LogAnalyzer
from services.auto_patcher import AutoPatcher
from services.cli_debugger import CLIDebugger
from services.ml_classifier_service import MLClassifierService

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
        self.ml_classifier_service = MLClassifierService()
        self.active_sessions: Dict[str, DebugSession] = {}
        
        # Create reports directory if it doesn't exist
        os.makedirs("debug_reports", exist_ok=True)
        
        # Create models directory if it doesn't exist
        os.makedirs(self.settings.ml_model_dir, exist_ok=True)

    def get_log_analyzer(self) -> LogAnalyzer:
        return self.log_analyzer

    def get_auto_patcher(self) -> AutoPatcher:
        return self.auto_patcher

    def get_cli_debugger(self) -> CLIDebugger:
        return self.cli_debugger
        
    def get_ml_classifier_service(self) -> MLClassifierService:
        return self.ml_classifier_service

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

@app.post("/api/v1/debug/batch-apply-patches")
async def batch_apply_patches(
    error_ids: List[str],
    pipeline_id: str,
    dry_run: bool = True,
    auto_patcher: AutoPatcher = Depends(debug_service.get_auto_patcher)
):
    """
    Apply patches to multiple errors in batch
    """
    try:
        logger.info("batch_applying_patches", 
                   error_count=len(error_ids),
                   pipeline_id=pipeline_id,
                   dry_run=dry_run)
        
        # Get session
        session = debug_service.active_sessions.get(pipeline_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"No active session found for pipeline {pipeline_id}")
        
        # Get errors
        errors = [e for e in session.errors if e.error_id in error_ids]
        if len(errors) != len(error_ids):
            raise HTTPException(status_code=400, detail="Some error IDs not found in session")
        
        # Apply patches
        results = []
        for error in errors:
            try:
                # Generate patch
                patch = await auto_patcher.generate_patch(error, {})
                
                # Apply patch
                success = await auto_patcher.apply_patch(patch, dry_run)
                
                if success and not dry_run:
                    session.add_patch(patch)
                    
                results.append({
                    "error_id": error.error_id,
                    "patch_id": patch.solution_id,
                    "success": success
                })
                
            except Exception as e:
                results.append({
                    "error_id": error.error_id,
                    "success": False,
                    "error": str(e)
                })
        
        return JSONResponse(content={
            "status": "completed",
            "dry_run": dry_run,
            "results": results,
            "success_count": sum(1 for r in results if r["success"]),
            "failure_count": sum(1 for r in results if not r["success"])
        })
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("batch_patch_application_failed", error=str(e))
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

@app.post("/api/v1/ml/classify-error")
async def classify_error(
    error: PipelineError,
    background_tasks: BackgroundTasks,
    ml_classifier_service: MLClassifierService = Depends(debug_service.get_ml_classifier_service),
    model_types: Optional[Dict[str, str]] = None
):
    """
    Classify an error using ML models
    """
    try:
        logger.info("classifying_error", error_id=error.error_id)
        
        result = await ml_classifier_service.classify_error(error, model_types)
        
        # Schedule cleanup in background
        background_tasks.add_task(ml_classifier_service.cleanup)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error("classification_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ml/train-models")
async def train_models(
    background_tasks: BackgroundTasks,
    ml_classifier_service: MLClassifierService = Depends(debug_service.get_ml_classifier_service),
    pipeline_id: Optional[str] = None,
    limit: int = 1000,
    model_types: List[str] = ["random_forest"]
):
    """
    Train ML models using historical error data
    """
    try:
        logger.info("training_models", 
                   pipeline_id=pipeline_id,
                   model_types=model_types)
        
        result = await ml_classifier_service.train_models(
            pipeline_id=pipeline_id,
            limit=limit,
            model_types=model_types
        )
        
        # Schedule cleanup in background
        background_tasks.add_task(ml_classifier_service.cleanup)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error("model_training_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ml/model-info")
async def get_model_info(
    background_tasks: BackgroundTasks,
    ml_classifier_service: MLClassifierService = Depends(debug_service.get_ml_classifier_service)
):
    """
    Get information about trained ML models
    """
    try:
        logger.info("getting_model_info")
        
        result = await ml_classifier_service.get_model_info()
        
        # Schedule cleanup in background
        background_tasks.add_task(ml_classifier_service.cleanup)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error("get_model_info_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ml/generate-training-data")
async def generate_training_data(
    background_tasks: BackgroundTasks,
    ml_classifier_service: MLClassifierService = Depends(debug_service.get_ml_classifier_service),
    output_file: str = "training_data.json",
    limit: int = 1000
):
    """
    Generate training data from historical errors
    """
    try:
        logger.info("generating_training_data", 
                   output_file=output_file,
                   limit=limit)
        
        result = await ml_classifier_service.generate_training_data(
            output_file=output_file,
            limit=limit
        )
        
        # Schedule cleanup in background
        background_tasks.add_task(ml_classifier_service.cleanup)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error("generate_training_data_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/debug/export-session")
async def export_debug_session(
    pipeline_id: str,
    format: str = Query("json", regex="^(json|markdown|text)$"),
    cli_debugger: CLIDebugger = Depends(debug_service.get_cli_debugger)
):
    """
    Export a debug session to a file
    """
    try:
        # Get session
        session = debug_service.active_sessions.get(pipeline_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"No active session found for pipeline {pipeline_id}")
        
        # Set up CLI debugger with the session
        cli_debugger.current_session = session
        
        # Generate report
        report = cli_debugger._generate_debug_report()
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"debug_report_{pipeline_id}_{timestamp}"
        
        # Generate content based on format
        if format.lower() == "json":
            filename += ".json"
            content = json.dumps(report.dict(), indent=2)
        elif format.lower() == "markdown":
            filename += ".md"
            content = cli_debugger._generate_markdown_report(report)
        else:  # text
            filename += ".txt"
            content = cli_debugger._generate_text_report(report)
            
        # Save to file
        filepath = os.path.join("debug_reports", filename)
        with open(filepath, "w") as f:
            f.write(content)
            
        # Return file
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/octet-stream"
        )
    
    except Exception as e:
        logger.error("export_session_failed", error=str(e))
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
        
        # Store session for API access
        debug_service.active_sessions[pipeline_id] = session
        
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
            
            if command == "analyze_error":
                error_id = data.get("error_id")
                error = next((e for e in session.errors if e.error_id == error_id), None)
                if error:
                    analysis = await cli_debugger.log_analyzer.get_error_analysis(error)
                    session.add_analysis(analysis)
                    await websocket.send_json({
                        "type": "analysis_result",
                        "data": analysis.dict()
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Error with ID {error_id} not found"
                    })
            
            elif command == "generate_patch":
                error_id = data.get("error_id")
                error = next((e for e in session.errors if e.error_id == error_id), None)
                if error:
                    patch = await cli_debugger.auto_patcher.generate_patch(error, {})
                    await websocket.send_json({
                        "type": "patch_solution",
                        "data": patch.dict()
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Error with ID {error_id} not found"
                    })
            
            elif command == "apply_patch":
                patch_data = data.get("patch")
                dry_run = data.get("dry_run", True)
                
                if not patch_data:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No patch data provided"
                    })
                    continue
                
                patch = PatchSolution(**patch_data)
                success = await cli_debugger.auto_patcher.apply_patch(patch, dry_run)
                
                if success:
                    session.add_patch(patch)
                    await websocket.send_json({
                        "type": "patch_applied",
                        "success": True,
                        "dry_run": dry_run
                    })
                else:
                    await websocket.send_json({
                        "type": "patch_applied",
                        "success": False,
                        "dry_run": dry_run,
                        "message": "Patch application failed"
                    })
            
            elif command == "apply_all_patches":
                error_ids = data.get("error_ids", [])
                dry_run = data.get("dry_run", True)
                
                if not error_ids:
                    # If no error IDs provided, use all unpatched errors
                    error_ids = [
                        e.error_id for e in session.errors
                        if not any(p.error_id == e.error_id for p in session.applied_patches)
                    ]
                
                if not error_ids:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No errors to patch"
                    })
                    continue
                
                # Apply patches
                results = []
                for error_id in error_ids:
                    error = next((e for e in session.errors if e.error_id == error_id), None)
                    if not error:
                        results.append({
                            "error_id": error_id,
                            "success": False,
                            "message": "Error not found"
                        })
                        continue
                        
                    try:
                        # Generate patch
                        patch = await cli_debugger.auto_patcher.generate_patch(error, {})
                        
                        # Apply patch
                        success = await cli_debugger.auto_patcher.apply_patch(patch, dry_run)
                        
                        if success and not dry_run:
                            session.add_patch(patch)
                            
                        results.append({
                            "error_id": error_id,
                            "patch_id": patch.solution_id,
                            "success": success
                        })
                        
                    except Exception as e:
                        results.append({
                            "error_id": error_id,
                            "success": False,
                            "message": str(e)
                        })
                
                await websocket.send_json({
                    "type": "batch_patches_applied",
                    "success_count": sum(1 for r in results if r["success"]),
                    "failure_count": sum(1 for r in results if not r["success"]),
                    "dry_run": dry_run,
                    "results": results
                })
            
            elif command == "rollback_patch":
                patch_id = data.get("patch_id")
                if not patch_id:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No patch ID provided"
                    })
                    continue
                
                success = await cli_debugger.auto_patcher.rollback_patch(patch_id)
                await websocket.send_json({
                    "type": "patch_rollback",
                    "success": success,
                    "patch_id": patch_id
                })
            
            elif command == "export_session":
                format = data.get("format", "json").lower()
                if format not in ["json", "markdown", "text"]:
                    format = "json"
                
                # Generate report
                report = cli_debugger._generate_debug_report()
                
                # Generate content based on format
                if format == "json":
                    content = json.dumps(report.dict(), indent=2)
                elif format == "markdown":
                    content = cli_debugger._generate_markdown_report(report)
                else:  # text
                    content = cli_debugger._generate_text_report(report)
                
                await websocket.send_json({
                    "type": "session_exported",
                    "format": format,
                    "content": content
                })
            
            elif command == "get_session_summary":
                # Calculate metrics
                duration = (
                    (session.end_time or datetime.utcnow()) - 
                    session.start_time
                ).total_seconds()
                
                success_rate = 0
                if session.errors:
                    resolved_errors = sum(
                        1 for error in session.errors
                        if any(patch.error_id == error.error_id for patch in session.applied_patches)
                    )
                    success_rate = (resolved_errors / len(session.errors)) * 100
                
                await websocket.send_json({
                    "type": "session_summary",
                    "data": {
                        "error_count": len(session.errors),
                        "analysis_count": len(session.analysis_results),
                        "patch_count": len(session.applied_patches),
                        "session_duration": duration,
                        "success_rate": success_rate,
                        "commands_executed": len(cli_debugger.command_sequence) if hasattr(cli_debugger, 'command_sequence') else 0
                    }
                })
                
            elif command == "classify_error_ml":
                error_id = data.get("error_id")
                model_types = data.get("model_types")
                
                error = next((e for e in session.errors if e.error_id == error_id), None)
                if not error:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Error with ID {error_id} not found"
                    })
                    continue
                
                # Get ML classifier service
                ml_classifier_service = debug_service.get_ml_classifier_service()
                
                # Classify error
                result = await ml_classifier_service.classify_error(error, model_types)
                
                await websocket.send_json({
                    "type": "ml_classification_result",
                    "data": result
                })
            
            elif command == "train_ml_models":
                pipeline_id = data.get("pipeline_id", session.pipeline_id)
                limit = data.get("limit", 1000)
                model_types = data.get("model_types", ["random_forest"])
                
                # Get ML classifier service
                ml_classifier_service = debug_service.get_ml_classifier_service()
                
                # Train models
                result = await ml_classifier_service.train_models(
                    pipeline_id=pipeline_id,
                    limit=limit,
                    model_types=model_types
                )
                
                await websocket.send_json({
                    "type": "ml_training_result",
                    "data": result
                })
            
            elif command == "get_ml_model_info":
                # Get ML classifier service
                ml_classifier_service = debug_service.get_ml_classifier_service()
                
                # Get model info
                result = await ml_classifier_service.get_model_info()
                
                await websocket.send_json({
                    "type": "ml_model_info",
                    "data": result
                })
            
            elif command == "get_command_history":
                if not hasattr(cli_debugger, 'command_sequence') or not cli_debugger.command_sequence:
                    await websocket.send_json({
                        "type": "command_history",
                        "data": {
                            "commands": [],
                            "message": "No commands have been executed in this session yet."
                        }
                    })
                    continue
                
                # Count command frequencies
                command_counts = {}
                for cmd in cli_debugger.command_sequence:
                    command_counts[cmd] = command_counts.get(cmd, 0) + 1
                
                # Sort by frequency
                sorted_commands = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)
                
                # Format for JSON response
                command_stats = []
                for cmd, count in sorted_commands:
                    display_name = cmd.replace("_", " ").title()
                    percentage = (count / len(cli_debugger.command_sequence)) * 100
                    command_stats.append({
                        "command": cmd,
                        "display_name": display_name,
                        "count": count,
                        "percentage": percentage
                    })
                
                # Get command flow if available
                command_flow = None
                if len(cli_debugger.command_sequence) >= 3:
                    recent_flow = cli_debugger.command_sequence[-10:]
                    command_flow = [cmd.replace("_", " ").title() for cmd in recent_flow]
                
                # Get command transitions if available
                transitions = []
                if len(cli_debugger.command_sequence) >= 5:
                    transition_counts = {}
                    for i in range(len(cli_debugger.command_sequence) - 1):
                        current = cli_debugger.command_sequence[i]
                        next_cmd = cli_debugger.command_sequence[i + 1]
                        
                        if current not in transition_counts:
                            transition_counts[current] = {}
                        
                        transition_counts[current][next_cmd] = transition_counts[current].get(next_cmd, 0) + 1
                    
                    # Flatten transitions
                    flat_transitions = []
                    for from_cmd, to_cmds in transition_counts.items():
                        for to_cmd, count in to_cmds.items():
                            flat_transitions.append((from_cmd, to_cmd, count))
                    
                    # Sort by count
                    flat_transitions.sort(key=lambda x: x[2], reverse=True)
                    
                    # Format for JSON
                    for from_cmd, to_cmd, count in flat_transitions[:5]:
                        transitions.append({
                            "from": from_cmd,
                            "from_display": from_cmd.replace("_", " ").title(),
                            "to": to_cmd,
                            "to_display": to_cmd.replace("_", " ").title(),
                            "count": count
                        })
                
                await websocket.send_json({
                    "type": "command_history",
                    "data": {
                        "commands": command_stats,
                        "flow": command_flow,
                        "transitions": transitions
                    }
                })
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown command: {command}"
                })
    except Exception as e:
        logger.error("websocket_session_error", error=str(e))
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    
    finally:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
