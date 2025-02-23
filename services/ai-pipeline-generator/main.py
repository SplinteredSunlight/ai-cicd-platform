from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import yaml
from typing import Optional, Dict

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
    platform: Optional[str] = "github-actions"
    template_vars: Optional[Dict] = {}

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

@app.post("/api/v1/generate")
async def generate_pipeline(
    request: PipelineRequest,
    pipeline_generator: PipelineGeneratorService = Depends(settings.get_pipeline_generator)
):
    try:
        result = await pipeline_generator.generate_pipeline(
            description=request.description,
            platform=request.platform,
            template_vars=request.template_vars
        )
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
