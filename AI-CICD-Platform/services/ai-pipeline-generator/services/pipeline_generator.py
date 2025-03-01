from typing import Dict, Optional, List, Any, Tuple
import yaml
import json
import sys
import os
from openai import OpenAI

# Add the parent directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import get_settings, PIPELINE_SYSTEM_PROMPT, PIPELINE_USER_PROMPT
from services.platform_templates import (
    get_platform_guide, 
    get_available_templates, 
    get_template_variables, 
    apply_template
)
from services.pipeline_optimizer import PipelineOptimizerService

class PipelineGeneratorService:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.optimizer = PipelineOptimizerService()

    async def generate_pipeline(
        self,
        description: str,
        platform: str = "github-actions",
        template_vars: Optional[Dict] = None,
        template_name: Optional[str] = None,
        optimize: bool = False,
        optimizations: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate a CI/CD pipeline configuration using OpenAI's GPT model or predefined templates.
        
        Args:
            description (str): Natural language description of the desired pipeline
            platform (str): Target CI/CD platform (github-actions, gitlab-ci, etc.)
            template_vars (Dict, optional): Additional variables for pipeline customization
            template_name (str, optional): Name of the predefined template to use
            optimize (bool, optional): Whether to optimize the generated pipeline
            optimizations (List[str], optional): Specific optimizations to apply
        
        Returns:
            Dict containing the generated pipeline configuration and metadata
        """
        if platform not in self.settings.supported_platforms:
            raise ValueError(f"Unsupported platform: {platform}. Supported platforms: {', '.join(self.settings.supported_platforms)}")

        template_vars = template_vars or {}
        
        # If a template name is provided, use the predefined template
        if template_name:
            return await self._generate_from_template(platform, template_name, template_vars, description, optimize, optimizations)
        
        # Otherwise, generate using OpenAI
        return await self._generate_with_ai(description, platform, template_vars, optimize, optimizations)
    
    async def _generate_from_template(
        self,
        platform: str,
        template_name: str,
        variables: Dict[str, Any],
        description: str,
        optimize: bool = False,
        optimizations: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate a pipeline configuration using a predefined template.
        
        Args:
            platform (str): Target CI/CD platform
            template_name (str): Name of the template to use
            variables (Dict[str, Any]): Variables to customize the template
            description (str): Description of the pipeline (used for metadata)
            optimize (bool, optional): Whether to optimize the generated pipeline
            optimizations (List[str], optional): Specific optimizations to apply
            
        Returns:
            Dict containing the generated pipeline configuration and metadata
        """
        # Apply the template with the provided variables
        pipeline_content = apply_template(platform, template_name, variables)
        
        if not pipeline_content:
            raise ValueError(f"Template '{template_name}' not found for platform '{platform}'")
        
        # For YAML-based platforms, parse the YAML
        if platform != "jenkins":  # Jenkins uses Groovy, not YAML
            try:
                pipeline_config = yaml.safe_load(pipeline_content)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in template: {str(e)}")
        else:
            # For Jenkins, store as string
            pipeline_config = {"jenkinsfile": pipeline_content}
        
        result = {
            "status": "success",
            "platform": platform,
            "pipeline_config": pipeline_config,
            "raw_content": pipeline_content,
            "template_used": template_name,
            "metadata": {
                "source": "template",
                "template_name": template_name,
                "description": description
            }
        }
        
        # Apply optimizations if requested
        if optimize:
            result = await self.optimize_pipeline(result, optimizations)
            
        return result
    
    async def _generate_with_ai(
        self,
        description: str,
        platform: str,
        template_vars: Dict,
        optimize: bool = False,
        optimizations: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate a pipeline configuration using OpenAI's GPT model.
        
        Args:
            description (str): Natural language description of the desired pipeline
            platform (str): Target CI/CD platform
            template_vars (Dict): Additional variables for pipeline customization
            optimize (bool, optional): Whether to optimize the generated pipeline
            optimizations (List[str], optional): Specific optimizations to apply
            
        Returns:
            Dict containing the generated pipeline configuration and metadata
        """
        # Get platform-specific guidance
        platform_guide = get_platform_guide(platform)
        
        # Format best practices and security recommendations as bullet points
        best_practices_text = "\n".join([f"- {practice}" for practice in platform_guide["best_practices"]])
        security_recommendations_text = "\n".join([f"- {rec}" for rec in platform_guide["security_recommendations"]])
        
        # Enhanced prompt with platform-specific guidance
        enhanced_user_prompt = f"""
{PIPELINE_USER_PROMPT.format(
    platform=platform,
    description=description,
    template_vars=json.dumps(template_vars, indent=2)
)}

Platform-specific syntax guide:
{platform_guide["syntax_guide"]}

Platform-specific best practices:
{best_practices_text}

Platform-specific security recommendations:
{security_recommendations_text}
"""
        
        # Prepare the conversation messages
        messages = [
            {"role": "system", "content": PIPELINE_SYSTEM_PROMPT},
            {"role": "user", "content": enhanced_user_prompt}
        ]

        try:
            # Generate pipeline using OpenAI
            response = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=messages,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens
            )

            # Extract the generated content
            generated_content = response.choices[0].message.content

            # For YAML-based platforms, validate the YAML
            if platform != "jenkins":  # Jenkins uses Groovy, not YAML
                try:
                    # Extract YAML content (in case there's additional text)
                    yaml_content = self._extract_yaml_or_code_block(generated_content)
                    pipeline_config = yaml.safe_load(yaml_content)
                except yaml.YAMLError as e:
                    raise ValueError(f"Generated invalid YAML for {platform}: {str(e)}")
            else:
                # For Jenkins, just extract the code block but don't validate as YAML
                yaml_content = self._extract_yaml_or_code_block(generated_content)
                pipeline_config = {"jenkinsfile": yaml_content}  # Store as string

            result = {
                "status": "success",
                "platform": platform,
                "pipeline_config": pipeline_config,
                "raw_content": yaml_content,
                "metadata": {
                    "source": "ai",
                    "model": self.settings.openai_model,
                    "tokens_used": response.usage.total_tokens
                }
            }
            
            # Apply optimizations if requested
            if optimize:
                result = await self.optimize_pipeline(result, optimizations)
                
            return result

        except Exception as e:
            raise Exception(f"Pipeline generation failed: {str(e)}")
            
    def _extract_yaml_or_code_block(self, content: str) -> str:
        """
        Extract YAML or code block from the generated content.
        
        Args:
            content (str): Generated content that may contain markdown code blocks
            
        Returns:
            str: Extracted YAML or code content
        """
        # Check if content contains a code block
        if "```" in content:
            # Extract content between code block markers
            blocks = content.split("```")
            # Find the first non-empty block after a marker
            for i in range(1, len(blocks)):
                # Skip language identifier line if present
                lines = blocks[i].strip().split("\n")
                if len(lines) > 1 and (lines[0] == "yaml" or lines[0] == "groovy" or lines[0] == "yml"):
                    return "\n".join(lines[1:])
                else:
                    # If no language identifier, return the whole block
                    return blocks[i].strip()
        
        # If no code blocks found, return the original content
        return content

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
            
    def get_supported_platforms(self) -> List[str]:
        """
        Get a list of all supported CI/CD platforms.
        
        Returns:
            List of platform names
        """
        return self.settings.supported_platforms
    
    def get_available_templates(self, platform: str) -> Dict[str, Dict[str, str]]:
        """
        Get available templates for a specific platform.
        
        Args:
            platform (str): The CI/CD platform name
            
        Returns:
            Dict of template names and their descriptions
        """
        return get_available_templates(platform)
    
    def get_template_variables(self, platform: str, template_name: str) -> Dict[str, str]:
        """
        Get the customizable variables for a specific template.
        
        Args:
            platform (str): The CI/CD platform name
            template_name (str): The template name
            
        Returns:
            Dict of variable names and their default values
        """
        return get_template_variables(platform, template_name)
        
    async def optimize_pipeline(
        self,
        pipeline_result: Dict,
        optimizations: Optional[List[str]] = None
    ) -> Dict:
        """
        Optimize a generated pipeline configuration.
        
        Args:
            pipeline_result (Dict): The pipeline generation result
            optimizations (List[str], optional): Specific optimizations to apply
            
        Returns:
            Dict containing the optimized pipeline configuration and metadata
        """
        platform = pipeline_result.get("platform")
        pipeline_config = pipeline_result.get("pipeline_config", {})
        
        # Apply optimizations
        optimized_config, applied_optimizations = self.optimizer.optimize_pipeline(
            platform, pipeline_config, optimizations
        )
        
        # Update the pipeline result with optimized configuration
        pipeline_result["pipeline_config"] = optimized_config
        
        # Convert optimized config back to YAML for raw_content
        if platform != "jenkins":  # Jenkins uses Groovy, not YAML
            try:
                optimized_content = yaml.dump(optimized_config, default_flow_style=False)
                pipeline_result["raw_content"] = optimized_content
            except yaml.YAMLError as e:
                # If YAML conversion fails, keep the original raw_content
                pass
        
        # Add optimization metadata
        pipeline_result["optimizations"] = applied_optimizations
        pipeline_result["metadata"]["optimized"] = True
        
        return pipeline_result
    
    def get_optimization_strategies(self, platform: str) -> List[Dict[str, Any]]:
        """
        Get available optimization strategies for a specific platform.
        
        Args:
            platform (str): The CI/CD platform name
            
        Returns:
            List of optimization strategies
        """
        return self.optimizer.get_optimization_strategies(platform)
    
    async def analyze_pipeline(self, platform: str, pipeline_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze a pipeline configuration and identify potential optimizations.
        
        Args:
            platform (str): The CI/CD platform name
            pipeline_config (Dict[str, Any]): The pipeline configuration
            
        Returns:
            List of recommended optimizations
        """
        return self.optimizer.analyze_pipeline(platform, pipeline_config)
