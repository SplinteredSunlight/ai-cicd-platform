from typing import List, Dict, Optional, Tuple
import re
import json
from datetime import datetime
import asyncio
from elasticsearch import AsyncElasticsearch
from openai import OpenAI
from fuzzywuzzy import fuzz
import logging

from config import get_settings, ERROR_PATTERNS, PROMPT_TEMPLATES
from models.pipeline_debug import (
    PipelineError,
    AnalysisResult,
    ErrorCategory,
    ErrorSeverity,
    PipelineStage
)
from services.ml_classifier_service import MLClassifierService

# Configure logging
logger = logging.getLogger(__name__)

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
        
        # Initialize ML classifier service
        try:
            self.ml_classifier_service = MLClassifierService()
            self.use_ml_classification = self.settings.use_ml_classification if hasattr(self.settings, 'use_ml_classification') else True
            logger.info("ML classifier service initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize ML classifier service: {str(e)}")
            self.ml_classifier_service = None
            self.use_ml_classification = False

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

    def _get_unmatched_sections(self, log_content: str, existing_matches: List[PipelineError]) -> str:
        """
        Extract sections of log content not covered by existing matches
        """
        if not existing_matches:
            return log_content
            
        # Sort matches by position in log
        sorted_matches = sorted(existing_matches, key=lambda e: e.context.get("line_number", 0))
        
        # Extract unmatched sections
        unmatched = []
        last_end = 0
        
        for error in sorted_matches:
            line_num = error.context.get("line_number", 0)
            if line_num > last_end + 5:  # Add some buffer
                # Find the actual line in the log content
                lines = log_content.split("\n")
                if line_num < len(lines):
                    start_line = max(0, last_end)
                    end_line = min(len(lines), line_num - 1)
                    if end_line > start_line:
                        unmatched.append("\n".join(lines[start_line:end_line]))
            
            # Update last_end
            last_end = line_num + 5  # Add some buffer
            
        # Add any remaining content
        lines = log_content.split("\n")
        if last_end < len(lines) - 1:
            unmatched.append("\n".join(lines[last_end:]))
            
        return "\n\n".join(unmatched)
    
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

    def _parse_ai_error_analysis(self, analysis_text: str) -> List[PipelineError]:
        """
        Parse AI-generated error analysis and convert to PipelineError objects
        """
        errors = []
        
        # Simple parsing logic - look for error patterns in the text
        lines = analysis_text.split("\n")
        current_error = None
        error_lines = []
        
        for line in lines:
            if "error:" in line.lower() or "exception:" in line.lower() or "failed:" in line.lower():
                # If we were already collecting an error, save it
                if current_error and error_lines:
                    error_message = "\n".join(error_lines)
                    errors.append(PipelineError(
                        error_id=f"ai_err_{datetime.utcnow().timestamp()}",
                        message=error_message,
                        severity=self._determine_severity(error_message),
                        category=self._determine_category(error_message),
                        stage=self._determine_stage(error_message),
                        context={}
                    ))
                
                # Start a new error
                current_error = line
                error_lines = [line]
            elif current_error and line.strip():
                # Continue collecting lines for the current error
                error_lines.append(line)
        
        # Don't forget the last error if there is one
        if current_error and error_lines:
            error_message = "\n".join(error_lines)
            errors.append(PipelineError(
                error_id=f"ai_err_{datetime.utcnow().timestamp()}",
                message=error_message,
                severity=self._determine_severity(error_message),
                category=self._determine_category(error_message),
                stage=self._determine_stage(error_message),
                context={}
            ))
        
        return errors
    
    async def _determine_category_with_ml(self, error_message: str, context: Optional[Dict] = None) -> Tuple[ErrorCategory, float]:
        """
        Determine error category using ML classification.
        
        Args:
            error_message: The error message text
            context: Additional context for the error
            
        Returns:
            Tuple of (category, confidence)
        """
        try:
            # Use ML classifier service to classify error
            result = await self.ml_classifier_service.classify_error(error_message)
            
            if result["status"] == "success" and "classifications" in result:
                # Get category prediction and confidence
                category_result = result["classifications"].get("category", {})
                prediction = category_result.get("prediction")
                confidence = category_result.get("confidence", 0.0)
                
                if prediction and confidence > self.settings.ml_confidence_threshold:
                    # Convert prediction to ErrorCategory enum
                    try:
                        return ErrorCategory[prediction.upper()], confidence
                    except (KeyError, ValueError):
                        logger.warning(f"Invalid category prediction: {prediction}")
            
            # Fall back to rule-based approach
            return self._determine_category_rule_based(error_message), 0.0
            
        except Exception as e:
            logger.warning(f"ML classification failed: {str(e)}")
            return self._determine_category_rule_based(error_message), 0.0
    
    def _determine_category(self, error_message: str) -> ErrorCategory:
        """
        Determine error category based on content.
        
        This method tries to use ML classification if available, and falls back
        to rule-based classification if ML is not available or fails.
        """
        # Check if ML classification is enabled and available
        if self.use_ml_classification and self.ml_classifier_service:
            try:
                # Create event loop if not already running
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Use run_coroutine_threadsafe if loop is already running
                    future = asyncio.run_coroutine_threadsafe(
                        self._determine_category_with_ml(error_message),
                        loop
                    )
                    category, _ = future.result(timeout=2.0)  # 2 second timeout
                    return category
                else:
                    # Use run_until_complete if loop is not running
                    category, _ = loop.run_until_complete(
                        self._determine_category_with_ml(error_message)
                    )
                    return category
            except Exception as e:
                logger.warning(f"Error using ML classification: {str(e)}")
                # Fall back to rule-based approach
        
        # Use rule-based approach
        return self._determine_category_rule_based(error_message)
    
    def _determine_category_rule_based(self, error_message: str) -> ErrorCategory:
        """
        Determine error category based on content using rule-based approach.
        """
        error_lower = error_message.lower()
        
        # Dependency errors
        if any(dep in error_lower for dep in [
            "module", "import", "package", "dependency", "require", "npm", "pip",
            "gem", "maven", "gradle", "nuget", "cargo", "go get", "yarn",
            "could not find", "not found", "missing", "cannot resolve", "unresolved",
            "no such module", "cannot import", "failed to load", "not installed"
        ]):
            return ErrorCategory.DEPENDENCY
            
        # Permission errors
        elif any(perm in error_lower for perm in [
            "permission", "access", "denied", "eacces", "forbidden", "unauthorized",
            "not allowed", "cannot access", "cannot create", "cannot write",
            "cannot read", "cannot delete", "cannot modify", "cannot execute"
        ]):
            return ErrorCategory.PERMISSION
            
        # Configuration errors
        elif any(conf in error_lower for conf in [
            "config", "configuration", "setting", "environment", "env", "variable",
            "yaml", "json", "toml", "ini", "properties", "invalid syntax",
            "malformed", "missing key", "missing value", "invalid value"
        ]):
            return ErrorCategory.CONFIGURATION
            
        # Network errors
        elif any(net in error_lower for perm in [
            "network", "connection", "timeout", "unreachable", "refused", "reset",
            "dns", "http", "https", "ssl", "tls", "certificate", "proxy",
            "firewall", "port", "socket", "ping", "connect", "disconnect"
        ]):
            return ErrorCategory.NETWORK
            
        # Resource errors
        elif any(res in error_lower for res in [
            "resource", "memory", "cpu", "disk", "space", "storage", "quota",
            "limit", "exceeded", "out of memory", "oom", "full", "capacity",
            "insufficient", "exhausted", "overload", "throttle"
        ]):
            return ErrorCategory.RESOURCE
            
        # Build errors
        elif any(build in error_lower for build in [
            "build", "compile", "compilation", "syntax", "type", "linker",
            "undefined reference", "undefined symbol", "missing declaration",
            "missing definition", "failed to build", "build failed"
        ]):
            return ErrorCategory.BUILD
            
        # Test errors
        elif any(test in error_lower for test in [
            "test", "assert", "expect", "mock", "stub", "spy", "fixture",
            "junit", "pytest", "jest", "mocha", "karma", "jasmine", "cypress",
            "selenium", "webdriver", "coverage", "fail", "failed test"
        ]):
            return ErrorCategory.TEST
            
        # Deployment errors
        elif any(deploy in error_lower for deploy in [
            "deploy", "deployment", "release", "publish", "kubernetes", "k8s",
            "container", "docker", "image", "registry", "cluster", "pod",
            "service", "ingress", "helm", "chart", "terraform", "cloudformation"
        ]):
            return ErrorCategory.DEPLOYMENT
            
        # Security errors
        elif any(sec in error_lower for sec in [
            "security", "vulnerability", "cve", "exploit", "attack", "breach",
            "authentication", "authorization", "credential", "password", "token",
            "secret", "key", "certificate", "encrypt", "decrypt", "hash", "salt"
        ]):
            return ErrorCategory.SECURITY
            
        # Default to UNKNOWN if no match
        else:
            return ErrorCategory.UNKNOWN
    
    def _parse_ai_analysis(self, error: PipelineError, analysis_text: str) -> AnalysisResult:
        """
        Parse AI-generated analysis text into structured AnalysisResult
        """
        # Extract root cause
        root_cause = ""
        root_cause_match = re.search(r"Root cause:(.*?)(?=\n\n|\Z)", analysis_text, re.DOTALL)
        if root_cause_match:
            root_cause = root_cause_match.group(1).strip()
        
        # Extract suggested solutions
        solutions = []
        solutions_match = re.search(r"Suggested solutions:(.*?)(?=\n\n|\Z)", analysis_text, re.DOTALL)
        if solutions_match:
            solutions_text = solutions_match.group(1)
            solutions = [s.strip().lstrip("- ") for s in solutions_text.split("\n") if s.strip()]
        
        # Extract prevention measures
        prevention = []
        prevention_match = re.search(r"Prevention measures:(.*?)(?=\n\n|\Z)", analysis_text, re.DOTALL)
        if prevention_match:
            prevention_text = prevention_match.group(1)
            prevention = [p.strip().lstrip("- ") for p in prevention_text.split("\n") if p.strip()]
        
        return AnalysisResult(
            error=error,
            root_cause=root_cause,
            confidence_score=0.85,  # Default confidence
            suggested_solutions=solutions,
            prevention_measures=prevention
        )
    
    async def _get_previous_solutions(self, error: PipelineError, similar_errors: List[PipelineError]) -> List[Dict]:
        """
        Get previous solutions for similar errors
        """
        # This would typically query a database of previous solutions
        # For now, we'll return a simple placeholder
        return [{"error_id": e.error_id, "solution": "Previous solution placeholder"} for e in similar_errors[:3]]
    
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
        # Check for POST_DEPLOY first since it might contain words from other stages
        if any(indicator in error_message.lower() for indicator in ["health check", "post-deploy", "post deploy", "after deployment"]):
            return PipelineStage.POST_DEPLOY
            
        stage_indicators = {
            PipelineStage.CHECKOUT: ["git", "checkout", "clone", "fetch"],
            PipelineStage.BUILD: ["build", "compile", "package", "docker"],
            PipelineStage.TEST: ["test", "pytest", "jest", "coverage"],
            PipelineStage.SECURITY_SCAN: ["security", "scan", "vulnerability"],
            PipelineStage.DEPLOY: ["deploy", "release", "publish"]
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
