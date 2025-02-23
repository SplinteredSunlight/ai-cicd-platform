from typing import Dict, Optional
import yaml
import json
from openai import OpenAI
from ..config import get_settings, PIPELINE_SYSTEM_PROMPT, PIPELINE_USER_PROMPT

class PipelineGeneratorService:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)

    async def generate_pipeline(
        self,
        description: str,
        platform: str = "github-actions",
        template_vars: Optional[Dict] = None
    ) -> Dict:
        """
        Generate a CI/CD pipeline configuration using OpenAI's GPT model.
        
        Args:
            description (str): Natural language description of the desired pipeline
            platform (str): Target CI/CD platform (github-actions, gitlab-ci, etc.)
            template_vars (Dict, optional): Additional variables for pipeline customization
        
        Returns:
            Dict containing the generated pipeline configuration and metadata
        """
        if platform not in self.settings.supported_platforms:
            raise ValueError(f"Unsupported platform: {platform}")

        template_vars = template_vars or {}
        
        # Prepare the conversation messages
        messages = [
            {"role": "system", "content": PIPELINE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": PIPELINE_USER_PROMPT.format(
                    platform=platform,
                    description=description,
                    template_vars=json.dumps(template_vars, indent=2)
                )
            }
        ]

        try:
            # Generate pipeline using OpenAI
            response = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=messages,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens
            )

            # Extract the generated YAML content
            yaml_content = response.choices[0].message.content

            # Validate the generated YAML
            try:
                pipeline_config = yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                raise ValueError(f"Generated invalid YAML: {str(e)}")

            return {
                "status": "success",
                "platform": platform,
                "pipeline_config": pipeline_config,
                "raw_yaml": yaml_content,
                "metadata": {
                    "model": self.settings.openai_model,
                    "tokens_used": response.usage.total_tokens
                }
            }

        except Exception as e:
            raise Exception(f"Pipeline generation failed: {str(e)}")

    def validate_yaml(self, yaml_content: str) -> bool:
        """
        Validate YAML syntax.
        
        Args:
            yaml_content (str): YAML content to validate
        
        Returns:
            bool: True if valid, raises exception if invalid
        """
        try:
            yaml.safe_load(yaml_content)
            return True
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {str(e)}")
