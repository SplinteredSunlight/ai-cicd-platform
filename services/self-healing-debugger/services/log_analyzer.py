from typing import List, Dict, Optional, Tuple
import re
import json
from datetime import datetime
import asyncio
from elasticsearch import AsyncElasticsearch
from openai import OpenAI
from fuzzywuzzy import fuzz

from ..config import get_settings, ERROR_PATTERNS, PROMPT_TEMPLATES
from ..models.pipeline_debug import (
    PipelineError,
    AnalysisResult,
    ErrorCategory,
    ErrorSeverity,
    PipelineStage
)

class LogAnalyzer:
    def __init__(self):
        self.settings = get_settings()
        self.es_client = AsyncElasticsearch(
            self.settings.elasticsearch_hosts,
            basic_auth=(
                self.settings.elasticsearch_username,
                self.settings.elasticsearch_password
            ) if self.settings.elasticsearch_username else None
        )
        self.openai_client = OpenAI(api_key=self.settings.openai_api_key)
        self.pattern_cache = {}

    async def analyze_pipeline_logs(
        self,
        pipeline_id: str,
        log_content: str
    ) -> List[PipelineError]:
        """
        Analyze pipeline logs to identify errors and their context
        """
        try:
            # First pass: Rule-based pattern matching
            pattern_matches = await self._match_error_patterns(log_content)
            
            # Second pass: AI-powered analysis for unmatched errors
            ai_matches = await self._analyze_with_ai(log_content, pattern_matches)
            
            # Combine and deduplicate results
            all_errors = pattern_matches + ai_matches
            unique_errors = self._deduplicate_errors(all_errors)
            
            # Store analysis results in Elasticsearch
            await self._store_analysis_results(pipeline_id, unique_errors)
            
            return unique_errors

        except Exception as e:
            raise Exception(f"Log analysis failed: {str(e)}")

    async def get_error_analysis(
        self,
        error: PipelineError,
        pipeline_config: Optional[Dict] = None
    ) -> AnalysisResult:
        """
        Generate detailed analysis for a specific error
        """
        try:
            # Get historical context
            similar_errors = await self._find_similar_errors(error)
            
            # Generate analysis using AI
            analysis = await self._generate_error_analysis(
                error,
                similar_errors,
                pipeline_config
            )
            
            return analysis

        except Exception as e:
            raise Exception(f"Error analysis failed: {str(e)}")

    async def _match_error_patterns(self, log_content: str) -> List[PipelineError]:
        """
        Match known error patterns in log content
        """
        errors = []
        
        for category, pattern_data in ERROR_PATTERNS.items():
            for pattern in pattern_data["patterns"]:
                matches = re.finditer(pattern, log_content, re.MULTILINE)
                
                for match in matches:
                    context_start = max(0, match.start() - 200)
                    context_end = min(len(log_content), match.end() + 200)
                    
                    error = PipelineError(
                        error_id=f"err_{datetime.utcnow().timestamp()}",
                        message=match.group(0),
                        category=ErrorCategory[category.upper()],
                        severity=self._determine_severity(match.group(0)),
                        stage=self._determine_stage(match.group(0)),
                        context={
                            "match": match.group(1) if match.groups() else None,
                            "surrounding_context": log_content[context_start:context_end],
                            "line_number": len(log_content[:match.start()].splitlines())
                        }
                    )
                    errors.append(error)
        
        return errors

    async def _analyze_with_ai(
        self,
        log_content: str,
        existing_matches: List[PipelineError]
    ) -> List[PipelineError]:
        """
        Use AI to identify errors not caught by pattern matching
        """
        try:
            # Extract sections not covered by pattern matches
            unmatched_sections = self._get_unmatched_sections(log_content, existing_matches)
            
            if not unmatched_sections:
                return []

            # Analyze with OpenAI
            response = await self.openai_client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing CI/CD pipeline logs and identifying errors."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze these log sections and identify any errors:\n\n{unmatched_sections}"
                    }
                ],
                temperature=0.3,
                max_tokens=self.settings.max_tokens
            )

            # Parse AI response and convert to PipelineError objects
            ai_errors = self._parse_ai_error_analysis(response.choices[0].message.content)
            return ai_errors

        except Exception as e:
            raise Exception(f"AI analysis failed: {str(e)}")

    async def _generate_error_analysis(
        self,
        error: PipelineError,
        similar_errors: List[PipelineError],
        pipeline_config: Optional[Dict]
    ) -> AnalysisResult:
        """
        Generate detailed analysis of an error using AI
        """
        try:
            # Prepare context for AI
            previous_solutions = await self._get_previous_solutions(error, similar_errors)
            
            # Generate analysis prompt
            prompt = PROMPT_TEMPLATES["error_analysis"].format(
                error_context=json.dumps(error.dict(), indent=2),
                pipeline_config=json.dumps(pipeline_config, indent=2) if pipeline_config else "Not provided",
                previous_solutions=json.dumps(previous_solutions, indent=2)
            )

            # Get AI analysis
            response = await self.openai_client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert CI/CD pipeline debugger."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=self.settings.max_tokens
            )

            # Parse analysis
            analysis_text = response.choices[0].message.content
            return self._parse_ai_analysis(error, analysis_text)

        except Exception as e:
            raise Exception(f"Error analysis generation failed: {str(e)}")

    async def _find_similar_errors(self, error: PipelineError) -> List[PipelineError]:
        """
        Find similar historical errors from Elasticsearch
        """
        try:
            index = f"{self.settings.elasticsearch_index_prefix}*"
            
            query = {
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"message": error.message}},
                            {"term": {"category": error.category}},
                            {"term": {"stage": error.stage}}
                        ],
                        "minimum_should_match": 2
                    }
                },
                "size": 10,
                "sort": [{"timestamp": "desc"}]
            }

            result = await self.es_client.search(index=index, body=query)
            return [PipelineError(**hit["_source"]) for hit in result["hits"]["hits"]]

        except Exception as e:
            # Log error but don't fail the analysis
            print(f"Error finding similar errors: {str(e)}")
            return []

    async def _store_analysis_results(
        self,
        pipeline_id: str,
        errors: List[PipelineError]
    ):
        """
        Store analysis results in Elasticsearch
        """
        try:
            index = f"{self.settings.elasticsearch_index_prefix}{datetime.utcnow().strftime('%Y-%m')}"
            
            for error in errors:
                document = {
                    **error.dict(),
                    "pipeline_id": pipeline_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.es_client.index(
                    index=index,
                    document=document,
                    refresh=True
                )

        except Exception as e:
            # Log error but don't fail the analysis
            print(f"Error storing analysis results: {str(e)}")

    def _determine_severity(self, error_message: str) -> ErrorSeverity:
        """
        Determine error severity based on content and context
        """
        if any(critical in error_message.lower() for critical in 
               ["critical", "fatal", "crash", "exception", "failed"]):
            return ErrorSeverity.CRITICAL
        elif any(high in error_message.lower() for high in 
                ["error", "invalid", "missing"]):
            return ErrorSeverity.HIGH
        elif any(medium in error_message.lower() for medium in 
                ["warning", "deprecated"]):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _determine_stage(self, error_message: str) -> PipelineStage:
        """
        Determine pipeline stage from error context
        """
        stage_indicators = {
            PipelineStage.CHECKOUT: ["git", "checkout", "clone", "fetch"],
            PipelineStage.BUILD: ["build", "compile", "package", "docker"],
            PipelineStage.TEST: ["test", "pytest", "jest", "coverage"],
            PipelineStage.SECURITY_SCAN: ["security", "scan", "vulnerability"],
            PipelineStage.DEPLOY: ["deploy", "release", "publish"],
            PipelineStage.POST_DEPLOY: ["health", "monitor", "verify"]
        }

        for stage, indicators in stage_indicators.items():
            if any(indicator in error_message.lower() for indicator in indicators):
                return stage

        return PipelineStage.BUILD  # Default to BUILD if unclear

    def _deduplicate_errors(self, errors: List[PipelineError]) -> List[PipelineError]:
        """
        Deduplicate errors based on similarity
        """
        unique_errors = []
        
        for error in errors:
            is_duplicate = False
            for unique_error in unique_errors:
                similarity = fuzz.ratio(error.message, unique_error.message)
                if similarity > self.settings.similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_errors.append(error)
        
        return unique_errors

    async def cleanup(self):
        """
        Cleanup resources
        """
        await self.es_client.close()
