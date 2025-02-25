from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class ErrorSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class ErrorCategory(str, Enum):
    DEPENDENCY = "DEPENDENCY"
    PERMISSION = "PERMISSION"
    CONFIGURATION = "CONFIGURATION"
    BUILD = "BUILD"
    TEST = "TEST"
    DEPLOYMENT = "DEPLOYMENT"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    SECURITY = "SECURITY"
    UNKNOWN = "UNKNOWN"

class PipelineStage(str, Enum):
    CHECKOUT = "CHECKOUT"
    BUILD = "BUILD"
    TEST = "TEST"
    SECURITY_SCAN = "SECURITY_SCAN"
    DEPLOY = "DEPLOY"
    POST_DEPLOY = "POST_DEPLOY"

class PipelineError(BaseModel):
    """Model representing a pipeline error"""
    error_id: str = Field(..., description="Unique identifier for the error")
    message: str = Field(..., description="Error message")
    stack_trace: Optional[str] = Field(None, description="Stack trace if available")
    severity: ErrorSeverity = Field(..., description="Error severity level")
    category: ErrorCategory = Field(..., description="Type of error")
    stage: PipelineStage = Field(..., description="Pipeline stage where error occurred")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: Dict = Field(default_factory=dict, description="Additional error context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_id": "err_123",
                "message": "ModuleNotFoundError: No module named 'requests'",
                "severity": "HIGH",
                "category": "DEPENDENCY",
                "stage": "BUILD",
                "context": {
                    "file": "app/main.py",
                    "line": 10,
                    "command": "pip install -r requirements.txt"
                }
            }
        }

class AnalysisResult(BaseModel):
    """Model representing error analysis results"""
    error: PipelineError
    root_cause: str = Field(..., description="Identified root cause")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    similar_patterns: List[str] = Field(default_factory=list)
    suggested_solutions: List[str] = Field(default_factory=list)
    prevention_measures: List[str] = Field(default_factory=list)
    metadata: Dict = Field(default_factory=dict)

class PatchSolution(BaseModel):
    """Model representing an auto-patch solution"""
    solution_id: str = Field(..., description="Unique identifier for the solution")
    error_id: str = Field(..., description="Reference to the error being fixed")
    patch_type: str = Field(..., description="Type of patch (e.g., dependency, permission)")
    patch_script: str = Field(..., description="The actual patch code or commands")
    is_reversible: bool = Field(default=True)
    requires_approval: bool = Field(default=True)
    estimated_success_rate: float = Field(..., ge=0.0, le=1.0)
    dependencies: List[str] = Field(default_factory=list)
    validation_steps: List[str] = Field(default_factory=list)
    rollback_script: Optional[str] = None

class DebugSession(BaseModel):
    """Model representing an interactive debug session"""
    session_id: str = Field(..., description="Unique session identifier")
    pipeline_id: str = Field(..., description="Pipeline run identifier")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: str = Field(default="active")
    errors: List[PipelineError] = Field(default_factory=list)
    analysis_results: List[AnalysisResult] = Field(default_factory=list)
    applied_patches: List[PatchSolution] = Field(default_factory=list)
    chat_history: List[Dict] = Field(default_factory=list)
    metadata: Dict = Field(default_factory=dict)

    def add_error(self, error: PipelineError):
        """Add an error to the debug session"""
        self.errors.append(error)

    def add_analysis(self, analysis: AnalysisResult):
        """Add analysis results to the debug session"""
        self.analysis_results.append(analysis)

    def add_patch(self, patch: PatchSolution):
        """Add an applied patch to the debug session"""
        self.applied_patches.append(patch)

    def add_chat_message(self, role: str, content: str):
        """Add a chat message to the session history"""
        self.chat_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })

    def close_session(self, status: str = "completed"):
        """Close the debug session"""
        self.status = status
        self.end_time = datetime.utcnow()

class DebugReport(BaseModel):
    """Model for generating debug session reports"""
    session: DebugSession
    summary: str = Field(..., description="Executive summary")
    error_analysis: List[Dict] = Field(..., description="Detailed error analysis")
    solutions_applied: List[Dict] = Field(..., description="Solutions that were applied")
    recommendations: List[str] = Field(..., description="Future recommendations")
    metrics: Dict = Field(..., description="Session metrics")
    
    @validator("metrics")
    def validate_metrics(cls, v):
        """Ensure required metrics are present"""
        required_metrics = {"duration", "success_rate", "errors_resolved"}
        if not all(metric in v for metric in required_metrics):
            raise ValueError(f"Missing required metrics: {required_metrics - v.keys()}")
        return v
