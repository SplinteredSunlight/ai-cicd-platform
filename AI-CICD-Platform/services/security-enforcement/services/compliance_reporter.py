import os
import json
import yaml
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
import structlog
from pathlib import Path
import asyncio
import uuid

from ..models.policy import (
    Policy,
    PolicyEvaluationResult,
    PolicyViolation,
    PolicyType,
    PolicySeverity,
    PolicyComplianceReport
)
from ..models.compliance_report import (
    ComplianceReport,
    ComplianceReportSummary,
    ComplianceStandard,
    ComplianceRequirement,
    ComplianceViolation,
    ComplianceStatus
)
from .policy_engine import PolicyEngine

logger = structlog.get_logger()

class ComplianceReporter:
    """
    Service for generating compliance reports based on policy evaluations
    """
    
    def __init__(
        self, 
        policy_engine: Optional[PolicyEngine] = None,
        report_dir: Optional[str] = None
    ):
        """
        Initialize the compliance reporter
        
        Args:
            policy_engine: PolicyEngine instance to use
            report_dir: Directory for storing compliance reports
        """
        self.policy_engine = policy_engine or PolicyEngine()
        self.report_dir = report_dir or os.environ.get('COMPLIANCE_REPORT_DIR', '/var/lib/security-policies/reports')
        
        # Create report directory if it doesn't exist
        os.makedirs(self.report_dir, exist_ok=True)
        
        # Load compliance standards
        self.standards = self._load_compliance_standards()
    
    def _load_compliance_standards(self) -> Dict[str, Dict[str, Any]]:
        """
        Load compliance standards definitions
        
        Returns:
            Dictionary of compliance standards
        """
        # In a real implementation, these would be loaded from a database or files
        # For now, we'll define some common standards inline
        return {
            'pci-dss': {
                'name': 'PCI DSS',
                'description': 'Payment Card Industry Data Security Standard',
                'version': '4.0',
                'requirements': {
                    'pci-dss-1': {
                        'id': 'pci-dss-1',
                        'name': 'Install and maintain network security controls',
                        'description': 'Network security controls (NSCs), such as firewalls and other network security technologies, restrict traffic to and from untrusted networks and prohibit direct public access between untrusted networks and any system in the cardholder data environment.',
                        'policy_types': ['security'],
                        'severity': 'high'
                    },
                    'pci-dss-2': {
                        'id': 'pci-dss-2',
                        'name': 'Apply secure configurations to all system components',
                        'description': 'System components are configured and managed in accordance with security configuration standards.',
                        'policy_types': ['security', 'operational'],
                        'severity': 'high'
                    },
                    'pci-dss-3': {
                        'id': 'pci-dss-3',
                        'name': 'Protect stored account data',
                        'description': 'Account data storage is minimized, and sensitive data is encrypted.',
                        'policy_types': ['security', 'compliance'],
                        'severity': 'critical'
                    }
                }
            },
            'hipaa': {
                'name': 'HIPAA',
                'description': 'Health Insurance Portability and Accountability Act',
                'version': '2.0',
                'requirements': {
                    'hipaa-1': {
                        'id': 'hipaa-1',
                        'name': 'Access Control',
                        'description': 'Implement technical policies and procedures for electronic information systems that maintain electronic protected health information to allow access only to those persons or software programs that have been granted access rights.',
                        'policy_types': ['security', 'compliance'],
                        'severity': 'high'
                    },
                    'hipaa-2': {
                        'id': 'hipaa-2',
                        'name': 'Audit Controls',
                        'description': 'Implement hardware, software, and/or procedural mechanisms that record and examine activity in information systems that contain or use electronic protected health information.',
                        'policy_types': ['security', 'operational'],
                        'severity': 'medium'
                    },
                    'hipaa-3': {
                        'id': 'hipaa-3',
                        'name': 'Integrity',
                        'description': 'Implement policies and procedures to protect electronic protected health information from improper alteration or destruction.',
                        'policy_types': ['security', 'compliance'],
                        'severity': 'high'
                    }
                }
            },
            'nist-800-53': {
                'name': 'NIST 800-53',
                'description': 'National Institute of Standards and Technology Special Publication 800-53',
                'version': 'Rev. 5',
                'requirements': {
                    'nist-ac-1': {
                        'id': 'nist-ac-1',
                        'name': 'Access Control Policy and Procedures',
                        'description': 'The organization develops, documents, and disseminates an access control policy that addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance.',
                        'policy_types': ['security', 'compliance'],
                        'severity': 'high'
                    },
                    'nist-cm-1': {
                        'id': 'nist-cm-1',
                        'name': 'Configuration Management Policy and Procedures',
                        'description': 'The organization develops, documents, and disseminates a configuration management policy that addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance.',
                        'policy_types': ['operational'],
                        'severity': 'medium'
                    },
                    'nist-si-1': {
                        'id': 'nist-si-1',
                        'name': 'System and Information Integrity Policy and Procedures',
                        'description': 'The organization develops, documents, and disseminates a system and information integrity policy that addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance.',
                        'policy_types': ['security', 'operational'],
                        'severity': 'high'
                    }
                }
            }
        }
    
    async def generate_compliance_report(
        self,
        policy_evaluation_results: List[PolicyEvaluationResult],
        standards: List[str],
        target_info: Dict[str, Any]
    ) -> ComplianceReport:
        """
        Generate a compliance report based on policy evaluation results
        
        Args:
            policy_evaluation_results: List of policy evaluation results
            standards: List of compliance standards to report on
            target_info: Information about the target being evaluated
            
        Returns:
            ComplianceReport object
        """
        # Create report ID
        report_id = str(uuid.uuid4())
        
        # Filter standards
        selected_standards = {}
        for std_id in standards:
            if std_id in self.standards:
                selected_standards[std_id] = self.standards[std_id]
        
        if not selected_standards:
            logger.warning("No valid compliance standards selected", standards=standards)
            # Use all standards if none specified
            selected_standards = self.standards
        
        # Map policies to compliance requirements
        requirement_results = {}
        
        for std_id, standard in selected_standards.items():
            for req_id, requirement in standard['requirements'].items():
                requirement_results[req_id] = {
                    'requirement': requirement,
                    'standard_id': std_id,
                    'policies': [],
                    'violations': []
                }
        
        # Process policy evaluation results
        for result in policy_evaluation_results:
            # Find matching requirements for this policy
            matching_requirements = self._find_matching_requirements(result, selected_standards)
            
            for req_id in matching_requirements:
                # Add policy to requirement
                requirement_results[req_id]['policies'].append(result)
                
                # If policy failed, add violations
                if not result.passed:
                    violations = self.policy_engine.get_policy_violations(result)
                    requirement_results[req_id]['violations'].extend(violations)
        
        # Create compliance violations
        compliance_violations = []
        
        for req_id, req_result in requirement_results.items():
            if req_result['violations']:
                # Create compliance violation
                std_id = req_result['standard_id']
                requirement = req_result['requirement']
                
                violation = ComplianceViolation(
                    id=f"violation-{uuid.uuid4()}",
                    standard_id=std_id,
                    standard_name=selected_standards[std_id]['name'],
                    requirement_id=req_id,
                    requirement_name=requirement['name'],
                    severity=requirement['severity'],
                    description=f"Violation of {selected_standards[std_id]['name']} requirement: {requirement['name']}",
                    policy_violations=[v.id for v in req_result['violations']],
                    remediation_steps=self._generate_remediation_steps(req_id, req_result['violations'])
                )
                
                compliance_violations.append(violation)
        
        # Create compliance report
        report = ComplianceReport(
            id=report_id,
            generated_at=datetime.utcnow(),
            target=target_info,
            standards=[
                ComplianceStandard(
                    id=std_id,
                    name=std['name'],
                    description=std['description'],
                    version=std['version'],
                    requirements=[
                        ComplianceRequirement(
                            id=req_id,
                            name=req['name'],
                            description=req['description'],
                            status=self._determine_requirement_status(req_id, requirement_results)
                        )
                        for req_id, req in std['requirements'].items()
                    ]
                )
                for std_id, std in selected_standards.items()
            ],
            violations=compliance_violations,
            policy_evaluations=[result.dict() for result in policy_evaluation_results],
            summary=self._generate_report_summary(selected_standards, requirement_results, compliance_violations)
        )
        
        # Save report
        self._save_report(report)
        
        return report
    
    def _find_matching_requirements(
        self,
        policy_result: PolicyEvaluationResult,
        standards: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """
        Find compliance requirements that match a policy
        
        Args:
            policy_result: Policy evaluation result
            standards: Dictionary of compliance standards
            
        Returns:
            List of requirement IDs that match the policy
        """
        matching_requirements = []
        
        for std_id, standard in standards.items():
            for req_id, requirement in standard['requirements'].items():
                # Check if policy type matches requirement
                if policy_result.policy_type in requirement['policy_types']:
                    matching_requirements.append(req_id)
        
        return matching_requirements
    
    def _determine_requirement_status(
        self,
        requirement_id: str,
        requirement_results: Dict[str, Dict[str, Any]]
    ) -> ComplianceStatus:
        """
        Determine the status of a compliance requirement
        
        Args:
            requirement_id: ID of the requirement
            requirement_results: Dictionary of requirement results
            
        Returns:
            ComplianceStatus enum value
        """
        if requirement_id not in requirement_results:
            return ComplianceStatus.UNKNOWN
        
        result = requirement_results[requirement_id]
        
        if not result['policies']:
            return ComplianceStatus.NOT_APPLICABLE
        
        if result['violations']:
            return ComplianceStatus.NON_COMPLIANT
        
        return ComplianceStatus.COMPLIANT
    
    def _generate_remediation_steps(
        self,
        requirement_id: str,
        violations: List[PolicyViolation]
    ) -> List[str]:
        """
        Generate remediation steps for a compliance violation
        
        Args:
            requirement_id: ID of the requirement
            violations: List of policy violations
            
        Returns:
            List of remediation steps
        """
        # Collect remediation steps from policy violations
        steps = []
        
        for violation in violations:
            if violation.remediation_steps:
                steps.extend(violation.remediation_steps)
        
        # Add standard remediation steps based on requirement
        for std_id, standard in self.standards.items():
            if requirement_id in standard['requirements']:
                requirement = standard['requirements'][requirement_id]
                
                if requirement_id.startswith('pci-dss'):
                    if requirement_id == 'pci-dss-1':
                        steps.append("Implement and configure firewalls between all wireless networks and the cardholder data environment.")
                        steps.append("Maintain a current network diagram that documents all connections between the cardholder data environment and other networks.")
                    elif requirement_id == 'pci-dss-2':
                        steps.append("Implement secure configuration standards for all system components.")
                        steps.append("Maintain an inventory of system components that are in scope for PCI DSS.")
                    elif requirement_id == 'pci-dss-3':
                        steps.append("Keep cardholder data storage to a minimum by implementing data retention and disposal policies.")
                        steps.append("Protect stored cardholder data by using strong cryptography with associated key-management processes and procedures.")
                
                elif requirement_id.startswith('hipaa'):
                    if requirement_id == 'hipaa-1':
                        steps.append("Implement technical policies and procedures for electronic information systems that maintain electronic protected health information.")
                        steps.append("Ensure that access to electronic protected health information is limited to authorized personnel.")
                    elif requirement_id == 'hipaa-2':
                        steps.append("Implement hardware, software, and/or procedural mechanisms that record and examine activity in information systems.")
                        steps.append("Regularly review audit logs for suspicious activity.")
                    elif requirement_id == 'hipaa-3':
                        steps.append("Implement policies and procedures to protect electronic protected health information from improper alteration or destruction.")
                        steps.append("Use secure, authenticated, and encrypted communications when transmitting electronic protected health information.")
                
                elif requirement_id.startswith('nist'):
                    if requirement_id == 'nist-ac-1':
                        steps.append("Develop, document, and disseminate an access control policy.")
                        steps.append("Review and update the access control policy on a regular basis.")
                    elif requirement_id == 'nist-cm-1':
                        steps.append("Develop, document, and disseminate a configuration management policy.")
                        steps.append("Establish and maintain baseline configurations for information systems.")
                    elif requirement_id == 'nist-si-1':
                        steps.append("Develop, document, and disseminate a system and information integrity policy.")
                        steps.append("Monitor information systems for security vulnerabilities and implement security patches in a timely manner.")
        
        # Remove duplicates while preserving order
        unique_steps = []
        for step in steps:
            if step not in unique_steps:
                unique_steps.append(step)
        
        return unique_steps
    
    def _generate_report_summary(
        self,
        standards: Dict[str, Dict[str, Any]],
        requirement_results: Dict[str, Dict[str, Any]],
        violations: List[ComplianceViolation]
    ) -> Dict[str, Any]:
        """
        Generate a summary of the compliance report
        
        Args:
            standards: Dictionary of compliance standards
            requirement_results: Dictionary of requirement results
            violations: List of compliance violations
            
        Returns:
            Dictionary with report summary
        """
        # Count requirements by status
        status_counts = {
            'compliant': 0,
            'non_compliant': 0,
            'not_applicable': 0,
            'unknown': 0
        }
        
        for req_id, result in requirement_results.items():
            status = self._determine_requirement_status(req_id, requirement_results)
            
            if status == ComplianceStatus.COMPLIANT:
                status_counts['compliant'] += 1
            elif status == ComplianceStatus.NON_COMPLIANT:
                status_counts['non_compliant'] += 1
            elif status == ComplianceStatus.NOT_APPLICABLE:
                status_counts['not_applicable'] += 1
            else:
                status_counts['unknown'] += 1
        
        # Count violations by severity
        severity_counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
        
        for violation in violations:
            severity = violation.severity.lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Calculate compliance score
        total_applicable = status_counts['compliant'] + status_counts['non_compliant']
        compliance_score = (status_counts['compliant'] / total_applicable * 100) if total_applicable > 0 else 0
        
        # Generate summary
        return {
            'standards_count': len(standards),
            'requirements_count': sum(len(std['requirements']) for std in standards.values()),
            'violations_count': len(violations),
            'status_counts': status_counts,
            'severity_counts': severity_counts,
            'compliance_score': round(compliance_score, 2),
            'overall_status': 'compliant' if status_counts['non_compliant'] == 0 else 'non_compliant'
        }
    
    def _save_report(self, report: ComplianceReport):
        """
        Save a compliance report to disk
        
        Args:
            report: ComplianceReport object to save
        """
        try:
            # Create report filename
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            filename = f"compliance-report-{report.id}-{timestamp}.json"
            file_path = os.path.join(self.report_dir, filename)
            
            # Write report to file
            with open(file_path, 'w') as f:
                f.write(report.json(indent=2))
            
            logger.info("Saved compliance report", report_id=report.id, file=file_path)
        
        except Exception as e:
            logger.error("Failed to save compliance report", report_id=report.id, error=str(e))
    
    async def get_report(self, report_id: str) -> Optional[ComplianceReport]:
        """
        Get a compliance report by ID
        
        Args:
            report_id: ID of the report
            
        Returns:
            ComplianceReport object or None if not found
        """
        try:
            # Find report file
            report_files = [f for f in os.listdir(self.report_dir) if f.endswith('.json')]
            
            for filename in report_files:
                if report_id in filename:
                    file_path = os.path.join(self.report_dir, filename)
                    
                    with open(file_path, 'r') as f:
                        report_data = json.load(f)
                        return ComplianceReport(**report_data)
            
            return None
        
        except Exception as e:
            logger.error("Failed to get compliance report", report_id=report_id, error=str(e))
            return None
    
    async def list_reports(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List compliance reports
        
        Args:
            limit: Maximum number of reports to return
            offset: Offset for pagination
            
        Returns:
            List of report summaries
        """
        try:
            # Find report files
            report_files = [f for f in os.listdir(self.report_dir) if f.endswith('.json')]
            
            # Sort by timestamp (newest first)
            report_files.sort(reverse=True)
            
            # Apply pagination
            paginated_files = report_files[offset:offset + limit]
            
            # Load report summaries
            summaries = []
            
            for filename in paginated_files:
                file_path = os.path.join(self.report_dir, filename)
                
                try:
                    with open(file_path, 'r') as f:
                        report_data = json.load(f)
                        
                        # Extract summary information
                        summaries.append({
                            'id': report_data.get('id'),
                            'generated_at': report_data.get('generated_at'),
                            'target': report_data.get('target'),
                            'summary': report_data.get('summary'),
                            'standards': [s.get('name') for s in report_data.get('standards', [])]
                        })
                
                except Exception as e:
                    logger.error("Failed to load report summary", file=filename, error=str(e))
            
            return summaries
        
        except Exception as e:
            logger.error("Failed to list compliance reports", error=str(e))
            return []
    
    def get_compliance_report_summary(self, report: ComplianceReport) -> ComplianceReportSummary:
        """
        Get a summary of a compliance report
        
        Args:
            report: ComplianceReport object
            
        Returns:
            ComplianceReportSummary object
        """
        # Count requirements by status
        status_counts = {
            ComplianceStatus.COMPLIANT: 0,
            ComplianceStatus.NON_COMPLIANT: 0,
            ComplianceStatus.NOT_APPLICABLE: 0,
            ComplianceStatus.UNKNOWN: 0
        }
        
        for standard in report.standards:
            for requirement in standard.requirements:
                status_counts[requirement.status] += 1
        
        # Count violations by severity
        severity_counts = {
            PolicySeverity.CRITICAL: 0,
            PolicySeverity.HIGH: 0,
            PolicySeverity.MEDIUM: 0,
            PolicySeverity.LOW: 0,
            PolicySeverity.INFO: 0
        }
        
        for violation in report.violations:
            severity = PolicySeverity(violation.severity)
            severity_counts[severity] += 1
        
        # Calculate compliance score
        total_applicable = status_counts[ComplianceStatus.COMPLIANT] + status_counts[ComplianceStatus.NON_COMPLIANT]
        compliance_score = (status_counts[ComplianceStatus.COMPLIANT] / total_applicable * 100) if total_applicable > 0 else 0
        
        # Create summary
        return ComplianceReportSummary(
            report_id=report.id,
            generated_at=report.generated_at,
            standards=[s.name for s in report.standards],
            requirements_count=sum(len(s.requirements) for s in report.standards),
            violations_count=len(report.violations),
            status_counts={
                'compliant': status_counts[ComplianceStatus.COMPLIANT],
                'non_compliant': status_counts[ComplianceStatus.NON_COMPLIANT],
                'not_applicable': status_counts[ComplianceStatus.NOT_APPLICABLE],
                'unknown': status_counts[ComplianceStatus.UNKNOWN]
            },
            severity_counts={
                'critical': severity_counts[PolicySeverity.CRITICAL],
                'high': severity_counts[PolicySeverity.HIGH],
                'medium': severity_counts[PolicySeverity.MEDIUM],
                'low': severity_counts[PolicySeverity.LOW],
                'info': severity_counts[PolicySeverity.INFO]
            },
            compliance_score=round(compliance_score, 2),
            overall_status=ComplianceStatus.COMPLIANT if status_counts[ComplianceStatus.NON_COMPLIANT] == 0 else ComplianceStatus.NON_COMPLIANT
        )
