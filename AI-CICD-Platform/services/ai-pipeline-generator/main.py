from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import yaml
from typing import Optional, Dict, List, Any

from config import get_settings
from services.pipeline_generator import PipelineGeneratorService

app = FastAPI(
    title="AI Pipeline Generator",
    description="Generate CI/CD pipelines using natural language processing",
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

class PipelineRequest(BaseModel):
    description: str
    platform: Optional[str] = Field(
        default="github-actions", 
        description="Target CI/CD platform (e.g., github-actions, gitlab-ci, circle-ci)"
    )
    template_vars: Optional[Dict[str, Any]] = Field(
        default={}, 
        description="Additional variables for pipeline customization"
    )
    template_name: Optional[str] = Field(
        default=None,
        description="Name of the predefined template to use (if not provided, AI generation will be used)"
    )
    optimize: Optional[bool] = Field(
        default=False,
        description="Whether to optimize the generated pipeline"
    )
    optimizations: Optional[List[str]] = Field(
        default=None,
        description="Specific optimizations to apply (if None, all recommended optimizations will be applied)"
    )

class OptimizationRequest(BaseModel):
    platform: str = Field(
        description="Target CI/CD platform (e.g., github-actions, gitlab-ci, circle-ci)"
    )
    pipeline_config: Dict[str, Any] = Field(
        description="Pipeline configuration to optimize"
    )
    optimizations: Optional[List[str]] = Field(
        default=None,
        description="Specific optimizations to apply (if None, all recommended optimizations will be applied)"
    )

class AnalyzeRequest(BaseModel):
    platform: str = Field(
        description="Target CI/CD platform (e.g., github-actions, gitlab-ci, circle-ci)"
    )
    pipeline_config: Dict[str, Any] = Field(
        description="Pipeline configuration to analyze"
    )

class TemplateVariableInfo(BaseModel):
    name: str
    default_value: Any
    description: Optional[str] = None

class TemplateInfo(BaseModel):
    name: str
    description: str
    variables: Dict[str, Any]

class Settings:
    def __init__(self):
        self.settings = get_settings()
        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.pipeline_generator = PipelineGeneratorService()

    def get_pipeline_generator(self) -> PipelineGeneratorService:
        return self.pipeline_generator

settings = Settings()

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "ai-pipeline-generator",
        "version": "0.1.0"
    }

@app.get("/api/v1/platforms", response_model=List[str])
async def get_supported_platforms(
    pipeline_generator: PipelineGeneratorService = Depends(settings.get_pipeline_generator)
):
    """
    Get a list of all supported CI/CD platforms.
    """
    return pipeline_generator.get_supported_platforms()

@app.get("/api/v1/templates/{platform}")
async def get_platform_templates(
    platform: str,
    pipeline_generator: PipelineGeneratorService = Depends(settings.get_pipeline_generator)
):
    """
    Get available templates for a specific platform.
    """
    try:
        templates = pipeline_generator.get_available_templates(platform)
        return JSONResponse(content=templates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/templates/{platform}/{template_name}/variables")
async def get_template_variables(
    platform: str,
    template_name: str,
    pipeline_generator: PipelineGeneratorService = Depends(settings.get_pipeline_generator)
):
    """
    Get customizable variables for a specific template.
    """
    try:
        variables = pipeline_generator.get_template_variables(platform, template_name)
        return JSONResponse(content=variables)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/generate")
async def generate_pipeline(
    request: PipelineRequest,
    pipeline_generator: PipelineGeneratorService = Depends(settings.get_pipeline_generator)
):
    """
    Generate a CI/CD pipeline configuration based on a natural language description
    or using a predefined template.
    """
    try:
        result = await pipeline_generator.generate_pipeline(
            description=request.description,
            platform=request.platform,
            template_vars=request.template_vars,
            template_name=request.template_name,
            optimize=request.optimize,
            optimizations=request.optimizations
        )
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/optimize")
async def optimize_pipeline(
    request: OptimizationRequest,
    pipeline_generator: PipelineGeneratorService = Depends(settings.get_pipeline_generator)
):
    """
    Optimize an existing pipeline configuration.
    """
    try:
        # Create a pipeline result object to pass to the optimizer
        pipeline_result = {
            "status": "success",
            "platform": request.platform,
            "pipeline_config": request.pipeline_config,
            "raw_content": yaml.dump(request.pipeline_config, default_flow_style=False) if request.platform != "jenkins" else "",
            "metadata": {
                "source": "user",
            }
        }
        
        # Optimize the pipeline
        result = await pipeline_generator.optimize_pipeline(
            pipeline_result=pipeline_result,
            optimizations=request.optimizations
        )
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analyze")
async def analyze_pipeline(
    request: AnalyzeRequest,
    pipeline_generator: PipelineGeneratorService = Depends(settings.get_pipeline_generator)
):
    """
    Analyze a pipeline configuration and identify potential optimizations.
    """
    try:
        recommendations = await pipeline_generator.analyze_pipeline(
            platform=request.platform,
            pipeline_config=request.pipeline_config
        )
        return JSONResponse(content={"recommendations": recommendations})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/optimization-strategies/{platform}")
async def get_optimization_strategies(
    platform: str,
    pipeline_generator: PipelineGeneratorService = Depends(settings.get_pipeline_generator)
):
    """
    Get available optimization strategies for a specific platform.
    """
    try:
        strategies = pipeline_generator.get_optimization_strategies(platform)
        return JSONResponse(content={"strategies": strategies})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
