import os
import yaml
import json
import shutil
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
import structlog
from pathlib import Path
import asyncio
import uuid
import re
import difflib

from ..models.policy import (
    Policy,
    PolicyStatus,
    PolicyChangeRequest,
    PolicyType,
    PolicyEnforcementMode,
    PolicyEnvironment
)
from .policy_engine import PolicyEngine

logger = structlog.get_logger()

class PolicyManager:
    """
    Service for managing policy lifecycle, versioning, and change management
    """
    
    def __init__(
        self, 
        policy_engine: Optional[PolicyEngine] = None, 
        policy_dir: Optional[str] = None,
        archive_dir: Optional[str] = None
    ):
        """
        Initialize the policy manager
        
        Args:
            policy_engine: PolicyEngine instance to use
            policy_dir: Directory containing policy files
            archive_dir: Directory for archived policy versions
        """
        self.policy_engine = policy_engine or PolicyEngine()
        self.policy_dir = policy_dir or os.environ.get('POLICY_DIR', '/etc/security-policies')
        self.archive_dir = archive_dir or os.environ.get('POLICY_ARCHIVE_DIR', '/var/lib/security-policies/archive')
        
        # Create directories if they don't exist
        os.makedirs(self.policy_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)
        
        # Change requests (id -> request)
        self.change_requests = {}
    
    async def list_policies(
        self,
        policy_type: Optional[str] = None,
        status: Optional[str] = None,
        environment: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List policies with optional filtering
        
        Args:
            policy_type: Optional policy type to filter by
            status: Optional status to filter by
            environment: Optional environment to filter by
            tags: Optional list of tags to filter by
            
        Returns:
            List of policy dictionaries
        """
        try:
            policies = []
            
            # List policy files
            policy_files = [f for f in os.listdir(self.policy_dir) if f.endswith(('.yaml', '.yml'))]
            
            for filename in policy_files:
                file_path = os.path.join(self.policy_dir, filename)
                try:
                    policy = self.policy_engine.load_policy_from_file(file_path)
                    
                    # Apply filters
                    if policy_type and policy.type != policy_type:
                        continue
                    
                    if status and policy.status != status:
                        continue
                    
                    if environment and environment not in policy.environments and 'all' not in policy.environments:
                        continue
                    
                    if tags:
                        if not all(tag in policy.tags for tag in tags):
                            continue
                    
                    # Add to list
                    policies.append(policy.dict(exclude_none=True))
                
                except Exception as e:
                    logger.error("Failed to load policy", file=filename, error=str(e))
            
            return policies
        
        except Exception as e:
            logger.error("Failed to list policies", error=str(e))
            return []
    
    async def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a policy by ID
        
        Args:
            policy_id: ID of the policy
            
        Returns:
            Policy dictionary or None if not found
        """
        try:
            # List policy files
            policy_files = [f for f in os.listdir(self.policy_dir) if f.endswith(('.yaml', '.yml'))]
            
            for filename in policy_files:
                file_path = os.path.join(self.policy_dir, filename)
                try:
                    policy = self.policy_engine.load_policy_from_file(file_path)
                    
                    if policy.id == policy_id:
                        return policy.dict(exclude_none=True)
                
                except Exception as e:
                    logger.error("Failed to load policy", file=filename, error=str(e))
            
            return None
        
        except Exception as e:
            logger.error("Failed to get policy", policy_id=policy_id, error=str(e))
            return None
    
    async def create_policy(self, policy_yaml: str) -> Dict[str, Any]:
        """
        Create a new policy
        
        Args:
            policy_yaml: YAML string containing policy definition
            
        Returns:
            Dictionary with creation results
        """
        try:
            # Load policy
            policy = self.policy_engine.load_policy_from_yaml(policy_yaml)
            
            # Check if policy ID already exists
            existing_policy = await self.get_policy(policy.id)
            if existing_policy:
                return {
                    'success': False,
                    'message': f'Policy with ID {policy.id} already exists'
                }
            
            # Generate filename
            filename = f"{policy.id}.yaml"
            file_path = os.path.join(self.policy_dir, filename)
            
            # Write policy file
            with open(file_path, 'w') as f:
                f.write(policy_yaml)
            
            logger.info("Created policy", policy_id=policy.id, policy_name=policy.name, file=filename)
            
            return {
                'success': True,
                'policy_id': policy.id,
                'policy_name': policy.name,
                'file_path': file_path
            }
        
        except Exception as e:
            logger.error("Failed to create policy", error=str(e))
            return {
                'success': False,
                'message': f'Failed to create policy: {str(e)}'
            }
    
    async def update_policy(self, policy_id: str, policy_yaml: str) -> Dict[str, Any]:
        """
        Update an existing policy
        
        Args:
            policy_id: ID of the policy to update
            policy_yaml: YAML string containing updated policy definition
            
        Returns:
            Dictionary with update results
        """
        try:
            # Check if policy exists
            existing_policy_dict = await self.get_policy(policy_id)
            if not existing_policy_dict:
                return {
                    'success': False,
                    'message': f'Policy with ID {policy_id} not found'
                }
            
            # Load new policy
            new_policy = self.policy_engine.load_policy_from_yaml(policy_yaml)
            
            # Ensure ID matches
            if new_policy.id != policy_id:
                return {
                    'success': False,
                    'message': f'Policy ID in YAML ({new_policy.id}) does not match requested ID ({policy_id})'
                }
            
            # Archive current version
            await self._archive_policy(policy_id)
            
            # Update version
            existing_version = existing_policy_dict.get('version', '1.0.0')
            new_version = self._increment_version(existing_version)
            
            # Update policy with new version and timestamps
            policy_dict = yaml.safe_load(policy_yaml)
            policy_dict['version'] = new_version
            policy_dict['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            
            # Write updated policy
            updated_yaml = yaml.dump(policy_dict, sort_keys=False)
            
            # Find policy file
            policy_files = [f for f in os.listdir(self.policy_dir) if f.endswith(('.yaml', '.yml'))]
            policy_file = None
            
            for filename in policy_files:
                file_path = os.path.join(self.policy_dir, filename)
                try:
                    policy = self.policy_engine.load_policy_from_file(file_path)
                    if policy.id == policy_id:
                        policy_file = file_path
                        break
                except Exception:
                    pass
            
            if not policy_file:
                return {
                    'success': False,
                    'message': f'Policy file for ID {policy_id} not found'
                }
            
            # Write updated policy
            with open(policy_file, 'w') as f:
                f.write(updated_yaml)
            
            logger.info("Updated policy", 
                       policy_id=policy_id, 
                       old_version=existing_version,
                       new_version=new_version)
            
            return {
                'success': True,
                'policy_id': policy_id,
                'old_version': existing_version,
                'new_version': new_version,
                'file_path': policy_file
            }
        
        except Exception as e:
            logger.error("Failed to update policy", policy_id=policy_id, error=str(e))
            return {
                'success': False,
                'message': f'Failed to update policy: {str(e)}'
            }
    
    async def delete_policy(self, policy_id: str) -> Dict[str, Any]:
        """
        Delete a policy
        
        Args:
            policy_id: ID of the policy to delete
            
        Returns:
            Dictionary with deletion results
        """
        try:
            # Check if policy exists
            existing_policy = await self.get_policy(policy_id)
            if not existing_policy:
                return {
                    'success': False,
                    'message': f'Policy with ID {policy_id} not found'
                }
            
            # Archive before deletion
            await self._archive_policy(policy_id)
            
            # Find policy file
            policy_files = [f for f in os.listdir(self.policy_dir) if f.endswith(('.yaml', '.yml'))]
            policy_file = None
            
            for filename in policy_files:
                file_path = os.path.join(self.policy_dir, filename)
                try:
                    policy = self.policy_engine.load_policy_from_file(file_path)
                    if policy.id == policy_id:
                        policy_file = file_path
                        break
                except Exception:
                    pass
            
            if not policy_file:
                return {
                    'success': False,
                    'message': f'Policy file for ID {policy_id} not found'
                }
            
            # Delete policy file
            os.remove(policy_file)
            
            logger.info("Deleted policy", policy_id=policy_id)
            
            return {
                'success': True,
                'policy_id': policy_id
            }
        
        except Exception as e:
            logger.error("Failed to delete policy", policy_id=policy_id, error=str(e))
            return {
                'success': False,
                'message': f'Failed to delete policy: {str(e)}'
            }
    
    async def get_policy_versions(self, policy_id: str) -> Dict[str, Any]:
        """
        Get all versions of a policy
        
        Args:
            policy_id: ID of the policy
            
        Returns:
            Dictionary with policy versions
        """
        try:
            # Check if policy exists
            current_policy = await self.get_policy(policy_id)
            if not current_policy:
                return {
                    'success': False,
                    'message': f'Policy with ID {policy_id} not found'
                }
            
            # Get archived versions
            versions = []
            
            # Add current version
            versions.append({
                'version': current_policy.get('version', '1.0.0'),
                'updated_at': current_policy.get('updated_at', datetime.utcnow().isoformat() + 'Z'),
                'status': current_policy.get('status', 'active'),
                'is_current': True
            })
            
            # Check archive directory
            archive_dir = os.path.join(self.archive_dir, policy_id)
            if os.path.exists(archive_dir):
                archived_files = [f for f in os.listdir(archive_dir) if f.endswith(('.yaml', '.yml'))]
                
                for filename in archived_files:
                    file_path = os.path.join(archive_dir, filename)
                    try:
                        with open(file_path, 'r') as f:
                            policy_dict = yaml.safe_load(f.read())
                            
                            versions.append({
                                'version': policy_dict.get('version', '1.0.0'),
                                'updated_at': policy_dict.get('updated_at', ''),
                                'status': policy_dict.get('status', 'archived'),
                                'is_current': False,
                                'archive_file': filename
                            })
                    
                    except Exception as e:
                        logger.error("Failed to load archived policy", file=filename, error=str(e))
            
            # Sort by version (descending)
            versions.sort(key=lambda v: self._version_tuple(v['version']), reverse=True)
            
            return {
                'success': True,
                'policy_id': policy_id,
                'policy_name': current_policy.get('name', ''),
                'versions': versions
            }
        
        except Exception as e:
            logger.error("Failed to get policy versions", policy_id=policy_id, error=str(e))
            return {
                'success': False,
                'message': f'Failed to get policy versions: {str(e)}'
            }
    
    async def get_policy_version(self, policy_id: str, version: str) -> Dict[str, Any]:
        """
        Get a specific version of a policy
        
        Args:
            policy_id: ID of the policy
            version: Version to retrieve
            
        Returns:
            Dictionary with policy version
        """
        try:
            # Check if policy exists
            current_policy = await self.get_policy(policy_id)
            if not current_policy:
                return {
                    'success': False,
                    'message': f'Policy with ID {policy_id} not found'
                }
            
            # Check if this is the current version
            if current_policy.get('version') == version:
                return {
                    'success': True,
                    'policy': current_policy,
                    'is_current': True
                }
            
            # Look for archived version
            archive_dir = os.path.join(self.archive_dir, policy_id)
            if not os.path.exists(archive_dir):
                return {
                    'success': False,
                    'message': f'Version {version} of policy {policy_id} not found'
                }
            
            # Find version in archive
            archived_files = [f for f in os.listdir(archive_dir) if f.endswith(('.yaml', '.yml'))]
            
            for filename in archived_files:
                file_path = os.path.join(archive_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        policy_dict = yaml.safe_load(f.read())
                        
                        if policy_dict.get('version') == version:
                            return {
                                'success': True,
                                'policy': policy_dict,
                                'is_current': False,
                                'archive_file': filename
                            }
                
                except Exception as e:
                    logger.error("Failed to load archived policy", file=filename, error=str(e))
            
            return {
                'success': False,
                'message': f'Version {version} of policy {policy_id} not found'
            }
        
        except Exception as e:
            logger.error("Failed to get policy version", policy_id=policy_id, version=version, error=str(e))
            return {
                'success': False,
                'message': f'Failed to get policy version: {str(e)}'
            }
    
    async def restore_policy_version(self, policy_id: str, version: str) -> Dict[str, Any]:
        """
        Restore a policy to a previous version
        
        Args:
            policy_id: ID of the policy
            version: Version to restore
            
        Returns:
            Dictionary with restoration results
        """
        try:
            # Get the version to restore
            version_result = await self.get_policy_version(policy_id, version)
            if not version_result['success']:
                return version_result
            
            # If this is already the current version, nothing to do
            if version_result.get('is_current', False):
                return {
                    'success': True,
                    'policy_id': policy_id,
                    'version': version,
                    'message': 'This is already the current version'
                }
            
            # Archive current version
            await self._archive_policy(policy_id)
            
            # Get policy to restore
            policy_to_restore = version_result['policy']
            
            # Update version and timestamp
            current_policy = await self.get_policy(policy_id)
            current_version = current_policy.get('version', '1.0.0')
            new_version = self._increment_version(current_version)
            
            policy_to_restore['version'] = new_version
            policy_to_restore['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            policy_to_restore['status'] = 'active'  # Ensure status is active
            
            # Convert to YAML
            restored_yaml = yaml.dump(policy_to_restore, sort_keys=False)
            
            # Find policy file
            policy_files = [f for f in os.listdir(self.policy_dir) if f.endswith(('.yaml', '.yml'))]
            policy_file = None
            
            for filename in policy_files:
                file_path = os.path.join(self.policy_dir, filename)
                try:
                    policy = self.policy_engine.load_policy_from_file(file_path)
                    if policy.id == policy_id:
                        policy_file = file_path
                        break
                except Exception:
                    pass
            
            if not policy_file:
                # Create new file
                policy_file = os.path.join(self.policy_dir, f"{policy_id}.yaml")
            
            # Write restored policy
            with open(policy_file, 'w') as f:
                f.write(restored_yaml)
            
            logger.info("Restored policy version", 
                       policy_id=policy_id, 
                       from_version=version,
                       to_version=new_version)
            
            return {
                'success': True,
                'policy_id': policy_id,
                'from_version': version,
                'to_version': new_version,
                'file_path': policy_file
            }
        
        except Exception as e:
            logger.error("Failed to restore policy version", policy_id=policy_id, version=version, error=str(e))
            return {
                'success': False,
                'message': f'Failed to restore policy version: {str(e)}'
            }
    
    async def compare_policy_versions(self, policy_id: str, version1: str, version2: str) -> Dict[str, Any]:
        """
        Compare two versions of a policy
        
        Args:
            policy_id: ID of the policy
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            Dictionary with comparison results
        """
        try:
            # Get the versions to compare
            version1_result = await self.get_policy_version(policy_id, version1)
            if not version1_result['success']:
                return version1_result
            
            version2_result = await self.get_policy_version(policy_id, version2)
            if not version2_result['success']:
                return version2_result
            
            # Get policy dictionaries
            policy1 = version1_result['policy']
            policy2 = version2_result['policy']
            
            # Convert to YAML for comparison
            yaml1 = yaml.dump(policy1, sort_keys=False)
            yaml2 = yaml.dump(policy2, sort_keys=False)
            
            # Generate diff
            diff = list(difflib.unified_diff(
                yaml1.splitlines(),
                yaml2.splitlines(),
                fromfile=f"version {version1}",
                tofile=f"version {version2}",
                lineterm=''
            ))
            
            # Compare rules
            rules1 = {rule['id']: rule for rule in policy1.get('rules', [])}
            rules2 = {rule['id']: rule for rule in policy2.get('rules', [])}
            
            added_rules = [rule_id for rule_id in rules2 if rule_id not in rules1]
            removed_rules = [rule_id for rule_id in rules1 if rule_id not in rules2]
            modified_rules = [
                rule_id for rule_id in rules1 
                if rule_id in rules2 and rules1[rule_id] != rules2[rule_id]
            ]
            
            # Compare other fields
            field_changes = []
            for field in ['name', 'description', 'type', 'enforcement_mode', 'status', 'environments', 'tags']:
                if policy1.get(field) != policy2.get(field):
                    field_changes.append({
                        'field': field,
                        'from': policy1.get(field),
                        'to': policy2.get(field)
                    })
            
            return {
                'success': True,
                'policy_id': policy_id,
                'version1': version1,
                'version2': version2,
                'diff': diff,
                'added_rules': added_rules,
                'removed_rules': removed_rules,
                'modified_rules': modified_rules,
                'field_changes': field_changes
            }
        
        except Exception as e:
            logger.error("Failed to compare policy versions", 
                        policy_id=policy_id, 
                        version1=version1,
                        version2=version2,
                        error=str(e))
            return {
                'success': False,
                'message': f'Failed to compare policy versions: {str(e)}'
            }
    
    async def create_change_request(
        self,
        policy_id: str,
        changes: Dict[str, Any],
        requested_by: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Create a change request for a policy
        
        Args:
            policy_id: ID of the policy to change
            changes: Dictionary of changes to apply
            requested_by: Person who requested the change
            reason: Reason for the change
            
        Returns:
            Dictionary with change request details
        """
        try:
            # Check if policy exists
            existing_policy = await self.get_policy(policy_id)
            if not existing_policy:
                return {
                    'success': False,
                    'message': f'Policy with ID {policy_id} not found'
                }
            
            # Create change request
            change_request = PolicyChangeRequest(
                policy_id=policy_id,
                requested_by=requested_by,
                changes=changes,
                reason=reason
            )
            
            # Store change request
            self.change_requests[change_request.id] = change_request
            
            logger.info("Created policy change request", 
                       policy_id=policy_id, 
                       change_request_id=change_request.id,
                       requested_by=requested_by)
            
            return {
                'success': True,
                'change_request_id': change_request.id,
                'policy_id': policy_id,
                'requested_by': requested_by,
                'status': change_request.status
            }
        
        except Exception as e:
            logger.error("Failed to create change request", policy_id=policy_id, error=str(e))
            return {
                'success': False,
                'message': f'Failed to create change request: {str(e)}'
            }
    
    async def get_change_request(self, change_request_id: str) -> Dict[str, Any]:
        """
        Get a change request by ID
        
        Args:
            change_request_id: ID of the change request
            
        Returns:
            Dictionary with change request details
        """
        try:
            if change_request_id not in self.change_requests:
                return {
                    'success': False,
                    'message': f'Change request with ID {change_request_id} not found'
                }
            
            change_request = self.change_requests[change_request_id]
            
            return {
                'success': True,
                'change_request': change_request.dict()
            }
        
        except Exception as e:
            logger.error("Failed to get change request", change_request_id=change_request_id, error=str(e))
            return {
                'success': False,
                'message': f'Failed to get change request: {str(e)}'
            }
    
    async def list_change_requests(
        self,
        policy_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List change requests with optional filtering
        
        Args:
            policy_id: Optional policy ID to filter by
            status: Optional status to filter by
            
        Returns:
            Dictionary with change request list
        """
        try:
            change_requests = []
            
            for cr_id, cr in self.change_requests.items():
                # Apply filters
                if policy_id and cr.policy_id != policy_id:
                    continue
                
                if status and cr.status != status:
                    continue
                
                change_requests.append(cr.dict())
            
            return {
                'success': True,
                'change_requests': change_requests
            }
        
        except Exception as e:
            logger.error("Failed to list change requests", error=str(e))
            return {
                'success': False,
                'message': f'Failed to list change requests: {str(e)}'
            }
    
    async def approve_change_request(
        self,
        change_request_id: str,
        approved_by: str
    ) -> Dict[str, Any]:
        """
        Approve a change request
        
        Args:
            change_request_id: ID of the change request
            approved_by: Person who approved the change
            
        Returns:
            Dictionary with approval results
        """
        try:
            if change_request_id not in self.change_requests:
                return {
                    'success': False,
                    'message': f'Change request with ID {change_request_id} not found'
                }
            
            change_request = self.change_requests[change_request_id]
            
            # Check if already approved
            if change_request.status != 'pending':
                return {
                    'success': False,
                    'message': f'Change request is not pending (status: {change_request.status})'
                }
            
            # Update change request
            change_request.status = 'approved'
            change_request.approved_by = approved_by
            change_request.approved_at = datetime.utcnow()
            
            logger.info("Approved policy change request", 
                       change_request_id=change_request_id,
                       policy_id=change_request.policy_id,
                       approved_by=approved_by)
            
            return {
                'success': True,
                'change_request_id': change_request_id,
                'policy_id': change_request.policy_id,
                'approved_by': approved_by,
                'status': change_request.status
            }
        
        except Exception as e:
            logger.error("Failed to approve change request", change_request_id=change_request_id, error=str(e))
            return {
                'success': False,
                'message': f'Failed to approve change request: {str(e)}'
            }
    
    async def reject_change_request(
        self,
        change_request_id: str,
        rejected_by: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Reject a change request
        
        Args:
            change_request_id: ID of the change request
            rejected_by: Person who rejected the change
            reason: Reason for rejection
            
        Returns:
            Dictionary with rejection results
        """
        try:
            if change_request_id not in self.change_requests:
                return {
                    'success': False,
                    'message': f'Change request with ID {change_request_id} not found'
                }
            
            change_request = self.change_requests[change_request_id]
            
            # Check if already approved or rejected
            if change_request.status != 'pending':
                return {
                    'success': False,
                    'message': f'Change request is not pending (status: {change_request.status})'
                }
            
            # Update change request
            change_request.status = 'rejected'
            change_request.approved_by = rejected_by  # Reuse field for rejected_by
            change_request.metadata = change_request.metadata or {}
            change_request.metadata['rejection_reason'] = reason
            
            logger.info("Rejected policy change request", 
                       change_request_id=change_request_id,
                       policy_id=change_request.policy_id,
                       rejected_by=rejected_by,
                       reason=reason)
            
            return {
                'success': True,
                'change_request_id': change_request_id,
                'policy_id': change_request.policy_id,
                'rejected_by': rejected_by,
                'status': change_request.status,
                'reason': reason
            }
        
        except Exception as e:
            logger.error("Failed to reject change request", change_request_id=change_request_id, error=str(e))
            return {
                'success': False,
                'message': f'Failed to reject change request: {str(e)}'
            }
    
    async def implement_change_request(self, change_request_id: str) -> Dict[str, Any]:
        """
        Implement an approved change request
        
        Args:
            change_request_id: ID of the change request
            
        Returns:
            Dictionary with implementation results
        """
        try:
            if change_request_id not in self.change_requests:
                return {
                    'success': False,
                    'message': f'Change request with ID {change_request_id} not found'
                }
            
            change_request = self.change_requests[change_request_id]
            
            # Check if approved
            if change_request.status != 'approved':
                return {
                    'success': False,
                    'message': f'Change request is not approved (status: {change_request.status})'
                }
            
            # Get current policy
            policy_id = change_request.policy_id
            current_policy_result = await self.get_policy(policy_id)
            
            if not current_policy_result:
                return {
                    'success': False,
                    'message': f'Policy with ID {policy_id} not found'
                }
            
            current_policy = current_policy_result
            
            # Apply changes
            updated_policy = self._apply_changes(current_policy, change_request.changes)
            
            # Update policy
            yaml_content = yaml.dump(updated_policy, sort_keys=False)
            update_result = await self.update_policy(policy_id, yaml_content)
            
            if not update_result['success']:
                return update_result
            
            # Mark change request as implemented
            change_request.status = 'implemented'
            change_request.implemented_at = datetime.utcnow()
            
            logger.info("Implemented policy change request", 
                       change_request_id=change_request_id,
                       policy_id=policy_id)
            
            return {
                'success': True,
                'change_request_id': change_request_id,
                'policy_id': policy_id,
                'status': change_request.status,
                'new_version': update_result.get('new_version')
            }
        
        except Exception as e:
            logger.error("Failed to implement change request", change_request_id=change_request_id, error=str(e))
            return {
                'success': False,
                'message': f'Failed to implement change request: {str(e)}'
            }
    
    def _apply_changes(self, policy: Dict[str, Any], changes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply changes to a policy
        
        Args:
            policy: Current policy dictionary
            changes: Dictionary of changes to apply
            
        Returns:
            Updated policy dictionary
        """
        # Create a deep copy of the policy
        updated_policy = copy.deepcopy(policy)
        
        # Apply changes
        for field, value in changes.items():
            if field == 'rules':
                # Handle rule changes
                self._apply_rule_changes(updated_policy, value)
            else:
                # Simple field update
                updated_policy[field] = value
        
        return updated_policy
    
    def _apply_rule_changes(self, policy: Dict[str, Any], rule_changes: Dict[str, Any]):
        """
        Apply changes to policy rules
        
        Args:
            policy: Policy dictionary to modify
            rule_changes: Dictionary of rule changes
        """
        # Get current rules
        current_rules = {rule['id']: rule for rule in policy.get('rules', [])}
        
        # Process rule changes
        for action, rules in rule_changes.items():
            if action == 'add':
                # Add new rules
                for rule in rules:
                    if 'id' not in rule:
                        rule['id'] = str(uuid.uuid4())
                    policy['rules'].append(rule)
            
            elif action == 'update':
                # Update existing rules
                for rule in rules:
                    if 'id' in rule and rule['id'] in current_rules:
                        # Find the rule in the policy
                        for i, r in enumerate(policy['rules']):
                            if r['id'] == rule['id']:
                                # Update rule
                                policy['rules'][i] = rule
                                break
            
            elif action == 'remove':
                # Remove rules
                for rule_id in rules:
                    policy['rules'] = [r for r in policy['rules'] if r['id'] != rule_id]
    
    async def _archive_policy(self, policy_id: str) -> bool:
        """
        Archive the current version of a policy
        
        Args:
            policy_id: ID of the policy to archive
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current policy
            current_policy = await self.get_policy(policy_id)
            if not current_policy:
                return False
            
            # Find policy file
            policy_files = [f for f in os.listdir(self.policy_dir) if f.endswith(('.yaml', '.yml'))]
            policy_file = None
            
            for filename in policy_files:
                file_path = os.path.join(self.policy_dir, filename)
                try:
                    policy = self.policy_engine.load_policy_from_file(file_path)
                    if policy.id == policy_id:
                        policy_file = file_path
                        break
                except Exception:
                    pass
            
            if not policy_file:
                return False
            
            # Create archive directory for this policy
            policy_archive_dir = os.path.join(self.archive_dir, policy_id)
            os.makedirs(policy_archive_dir, exist_ok=True)
            
            # Generate archive filename
            version = current_policy.get('version', '1.0.0')
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            archive_filename = f"{policy_id}_v{version}_{timestamp}.yaml"
            archive_path = os.path.join(policy_archive_dir, archive_filename)
            
            # Copy policy file to archive
            shutil.copy2(policy_file, archive_path)
            
            logger.info("Archived policy", 
                       policy_id=policy_id, 
                       version=version,
                       archive_file=archive_path)
            
            return True
        
        except Exception as e:
            logger.error("Failed to archive policy", policy_id=policy_id, error=str(e))
            return False
    
    def _increment_version(self, version: str) -> str:
        """
        Increment a semantic version string
        
        Args:
            version: Version string (e.g., "1.0.0")
            
        Returns:
            Incremented version string
        """
        try:
            # Parse version
            match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version)
            if not match:
                # Invalid version format, return a default
                return '1.0.0'
            
            major, minor, patch = map(int, match.groups())
            
            # Increment patch version
            patch += 1
            
            return f"{major}.{minor}.{patch}"
        
        except Exception:
            # If anything goes wrong, return a default
            return '1.0.0'
    
    def _version_tuple(self, version: str) -> tuple:
        """
        Convert a version string to a tuple for sorting
        
        Args:
            version: Version string (e.g., "1.0.0")
            
        Returns:
            Tuple of version components
        """
        try:
            return tuple(map(int, version.split('.')))
        except Exception:
            return (0, 0, 0)  # Default for invalid versions
