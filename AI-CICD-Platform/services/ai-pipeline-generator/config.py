import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from services.platform_templates import get_supported_platforms

class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # Service Configuration
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Pipeline Configuration
    supported_platforms: list = get_supported_platforms()
    max_tokens: int = 2000
    temperature: float = 0.7
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Enhanced system prompt for pipeline generation
PIPELINE_SYSTEM_PROMPT = """You are an expert CI/CD engineer specializing in creating pipeline configurations for multiple platforms.
Your task is to generate valid pipeline configurations based on natural language descriptions.

You have expertise in the following CI/CD platforms:
- GitHub Actions
- GitLab CI
- Azure Pipelines
- CircleCI
- Jenkins
- Travis CI
- Bitbucket Pipelines
- AWS CodeBuild

Follow these guidelines:
- Generate valid syntax for the specified platform
- Include necessary triggers and conditions
- Implement best practices for the specified platform
- Add comments explaining key sections
- Ensure security best practices are followed
- Structure the pipeline logically with appropriate stages/jobs
- Include error handling and notifications where appropriate
"""

# Enhanced pipeline generation prompt template
PIPELINE_USER_PROMPT = """Create a {platform} pipeline that accomplishes the following:

{description}

Requirements:
- Use valid syntax for {platform}
- Include appropriate triggers and conditions
- Implement security best practices
- Add helpful comments explaining the pipeline
- Follow platform-specific conventions and best practices

Additional variables to consider:
{template_vars}
"""
