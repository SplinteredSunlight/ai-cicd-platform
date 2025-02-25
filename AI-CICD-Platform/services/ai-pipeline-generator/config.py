import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # Service Configuration
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Pipeline Configuration
    supported_platforms: list = ["github-actions", "gitlab-ci", "azure-pipelines"]
    max_tokens: int = 2000
    temperature: float = 0.7
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Example system prompt for pipeline generation
PIPELINE_SYSTEM_PROMPT = """You are an expert CI/CD engineer specializing in creating pipeline configurations. 
Your task is to generate valid YAML pipeline configurations based on natural language descriptions.
Follow these guidelines:
- Generate valid YAML syntax
- Include necessary triggers and conditions
- Implement best practices for the specified platform
- Add comments explaining key sections
- Ensure security best practices are followed
"""

# Pipeline generation prompt template
PIPELINE_USER_PROMPT = """Create a {platform} pipeline that accomplishes the following:

{description}

Requirements:
- Use valid YAML syntax for {platform}
- Include appropriate triggers and conditions
- Implement security best practices
- Add helpful comments explaining the pipeline

Additional variables to consider:
{template_vars}
"""
