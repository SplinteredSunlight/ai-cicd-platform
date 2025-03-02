#!/usr/bin/env python3
"""
Policy-as-Code CLI Tool

This CLI tool provides a command-line interface for interacting with the Policy-as-Code framework.
It allows users to manage policies, validate them, and generate compliance reports.
"""

import argparse
import json
import os
import sys
import yaml
import requests
from typing import Dict, Any, List, Optional
from tabulate import tabulate
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()

# Default API endpoint
DEFAULT_API_ENDPOINT = "http://localhost:8000/api/v1"

def get_api_endpoint() -> str:
    """Get the API endpoint from environment variable or use default"""
    return os.environ.get("POLICY_API_ENDPOINT", DEFAULT_API_ENDPOINT)

def print_success(message: str) -> None:
    """Print a success message"""
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

def print_error(message: str) -> None:
    """Print an error message"""
    print(f"{Fore.RED}Error: {message}{Style.RESET_ALL}")

def print_warning(message: str) -> None:
    """Print a warning message"""
    print(f"{Fore.YELLOW}Warning: {message}{Style.RESET_ALL}")

def print_info(message: str) -> None:
    """Print an info message"""
    print(f"{Fore.BLUE}{message}{Style.RESET_ALL}")

def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """Load a YAML file"""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print_error(f"Failed to load YAML file: {e}")
        sys.exit(1)

def save_yaml_file(data: Dict[str, Any], file_path: str) -> None:
    """Save data to a YAML file"""
    try:
        with open(file_path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)
        print_success(f"Saved to {file_path}")
    except Exception as e:
        print_error(f"Failed to save YAML file: {e}")
        sys.exit(1)

def make_api_request(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make an API request"""
    api_endpoint = get_api_endpoint()
    url = f"{api_endpoint}/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            print_error(f"Unsupported HTTP method: {method}")
            sys.exit(1)
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print_error(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print_error(f"Error details: {error_data.get('message', 'Unknown error')}")
            except:
                print_error(f"Status code: {e.response.status_code}")
        sys.exit(1)

def list_policies(args: argparse.Namespace) -> None:
    """List policies"""
    params = {}
    if args.type:
        params['policy_type'] = args.type
    if args.status:
        params['status'] = args.status
    if args.environment:
        params['environment'] = args.environment
    if args.tags:
        params['tags'] = args.tags.split(',')
    
    endpoint = "policies"
    if params:
        query_params = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"{endpoint}?{query_params}"
    
    policies = make_api_request("GET", endpoint)
    
    if not policies:
        print_info("No policies found")
        return
    
    # Prepare table data
    table_data = []
    for policy in policies:
        table_data.append([
            policy['id'],
            policy['name'],
            policy['type'],
            policy['enforcement_mode'],
            policy['status'],
            policy['version'],
            len(policy.get('rules', [])),
            ", ".join(policy.get('environments', [])),
            ", ".join(policy.get('tags', []))
        ])
    
    # Print table
    headers = ["ID", "Name", "Type", "Enforcement", "Status", "Version", "Rules", "Environments", "Tags"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def get_policy(args: argparse.Namespace) -> None:
    """Get a policy by ID"""
    policy = make_api_request("GET", f"policies/{args.id}")
    
    if args.output:
        save_yaml_file(policy, args.output)
    else:
        print(yaml.dump(policy, sort_keys=False))

def create_policy(args: argparse.Namespace) -> None:
    """Create a new policy"""
    policy_data = load_yaml_file(args.file)
    
    result = make_api_request("POST", "policies", policy_data)
    
    if result.get('success'):
        print_success(f"Policy created: {result.get('policy_id')}")
    else:
        print_error(f"Failed to create policy: {result.get('message')}")

def update_policy(args: argparse.Namespace) -> None:
    """Update an existing policy"""
    policy_data = load_yaml_file(args.file)
    
    result = make_api_request("PUT", f"policies/{args.id}", policy_data)
    
    if result.get('success'):
        print_success(f"Policy updated: {result.get('policy_id')}")
        print_info(f"Old version: {result.get('old_version')}")
        print_info(f"New version: {result.get('new_version')}")
    else:
        print_error(f"Failed to update policy: {result.get('message')}")

def delete_policy(args: argparse.Namespace) -> None:
    """Delete a policy"""
    if not args.force:
        confirm = input(f"Are you sure you want to delete policy {args.id}? (y/n): ")
        if confirm.lower() != 'y':
            print_info("Deletion cancelled")
            return
    
    result = make_api_request("DELETE", f"policies/{args.id}")
    
    if result.get('success'):
        print_success(f"Policy deleted: {result.get('policy_id')}")
    else:
        print_error(f"Failed to delete policy: {result.get('message')}")

def validate_policy(args: argparse.Namespace) -> None:
    """Validate a policy"""
    policy_data = load_yaml_file(args.file)
    
    result = make_api_request("POST", "validate", policy_data)
    
    if result.get('valid'):
        print_success("Policy is valid")
    else:
        print_error("Policy validation failed")
        for error in result.get('errors', []):
            print_error(f"- {error}")

def evaluate_resource(args: argparse.Namespace) -> None:
    """Evaluate a resource against policies"""
    resource_data = load_yaml_file(args.file)
    
    params = {}
    if args.policy_id:
        params['policy_id'] = args.policy_id
    if args.policy_type:
        params['policy_type'] = args.policy_type
    
    endpoint = "evaluate"
    if params:
        query_params = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"{endpoint}?{query_params}"
    
    result = make_api_request("POST", endpoint, resource_data)
    
    if result.get('compliant'):
        print_success("Resource is compliant with all policies")
    else:
        print_error("Resource is non-compliant")
        
        # Print violations
        violations = result.get('violations', [])
        if violations:
            print_info("\nPolicy Violations:")
            for violation in violations:
                print(f"\n{Fore.RED}Policy: {violation['policy_name']} ({violation['policy_id']}){Style.RESET_ALL}")
                print(f"Rule: {violation['rule_name']} ({violation['rule_id']})")
                print(f"Severity: {violation['severity']}")
                print(f"Description: {violation['description']}")
                
                if violation.get('remediation_steps'):
                    print(f"\n{Fore.YELLOW}Remediation Steps:{Style.RESET_ALL}")
                    for step in violation['remediation_steps']:
                        print(f"- {step}")

def list_policy_versions(args: argparse.Namespace) -> None:
    """List versions of a policy"""
    result = make_api_request("GET", f"policies/{args.id}/versions")
    
    if not result.get('success'):
        print_error(f"Failed to get policy versions: {result.get('message')}")
        return
    
    versions = result.get('versions', [])
    
    if not versions:
        print_info("No versions found")
        return
    
    # Prepare table data
    table_data = []
    for version in versions:
        table_data.append([
            version['version'],
            version['updated_at'],
            version['status'],
            "Yes" if version.get('is_current') else "No"
        ])
    
    # Print table
    headers = ["Version", "Updated At", "Status", "Current"]
    print(f"\nPolicy: {result.get('policy_name')} ({result.get('policy_id')})")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def get_policy_version(args: argparse.Namespace) -> None:
    """Get a specific version of a policy"""
    result = make_api_request("GET", f"policies/{args.id}/versions/{args.version}")
    
    if not result.get('success'):
        print_error(f"Failed to get policy version: {result.get('message')}")
        return
    
    policy = result.get('policy')
    
    if args.output:
        save_yaml_file(policy, args.output)
    else:
        print(yaml.dump(policy, sort_keys=False))

def restore_policy_version(args: argparse.Namespace) -> None:
    """Restore a policy to a previous version"""
    result = make_api_request("POST", f"policies/{args.id}/versions/{args.version}/restore")
    
    if result.get('success'):
        print_success(f"Policy restored from version {args.version} to {result.get('to_version')}")
    else:
        print_error(f"Failed to restore policy version: {result.get('message')}")

def compare_policy_versions(args: argparse.Namespace) -> None:
    """Compare two versions of a policy"""
    result = make_api_request("GET", f"policies/{args.id}/versions/{args.version1}/compare/{args.version2}")
    
    if not result.get('success'):
        print_error(f"Failed to compare policy versions: {result.get('message')}")
        return
    
    print_info(f"Comparing policy {result.get('policy_id')} versions:")
    print_info(f"Version {result.get('version1')} -> Version {result.get('version2')}")
    
    # Print diff
    diff = result.get('diff', [])
    if diff:
        print("\nDiff:")
        for line in diff:
            if line.startswith('+'):
                print(f"{Fore.GREEN}{line}{Style.RESET_ALL}")
            elif line.startswith('-'):
                print(f"{Fore.RED}{line}{Style.RESET_ALL}")
            else:
                print(line)
    
    # Print rule changes
    added_rules = result.get('added_rules', [])
    if added_rules:
        print(f"\n{Fore.GREEN}Added Rules:{Style.RESET_ALL}")
        for rule_id in added_rules:
            print(f"- {rule_id}")
    
    removed_rules = result.get('removed_rules', [])
    if removed_rules:
        print(f"\n{Fore.RED}Removed Rules:{Style.RESET_ALL}")
        for rule_id in removed_rules:
            print(f"- {rule_id}")
    
    modified_rules = result.get('modified_rules', [])
    if modified_rules:
        print(f"\n{Fore.YELLOW}Modified Rules:{Style.RESET_ALL}")
        for rule_id in modified_rules:
            print(f"- {rule_id}")
    
    # Print field changes
    field_changes = result.get('field_changes', [])
    if field_changes:
        print("\nField Changes:")
        for change in field_changes:
            print(f"- {change['field']}: {change['from']} -> {change['to']}")

def generate_compliance_report(args: argparse.Namespace) -> None:
    """Generate a compliance report"""
    resource_data = load_yaml_file(args.file)
    
    params = {}
    if args.standards:
        params['standards'] = args.standards.split(',')
    
    endpoint = "compliance/reports"
    if params:
        query_params = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"{endpoint}?{query_params}"
    
    result = make_api_request("POST", endpoint, resource_data)
    
    if not result.get('id'):
        print_error("Failed to generate compliance report")
        return
    
    print_success(f"Compliance report generated: {result.get('id')}")
    
    # Print summary
    summary = result.get('summary', {})
    if summary:
        print("\nCompliance Summary:")
        print(f"Standards: {', '.join(summary.get('standards', []))}")
        print(f"Requirements: {summary.get('requirements_count', 0)}")
        print(f"Violations: {summary.get('violations_count', 0)}")
        print(f"Compliance Score: {summary.get('compliance_score', 0)}%")
        print(f"Overall Status: {summary.get('overall_status', 'unknown')}")
    
    # Print violations
    violations = result.get('violations', [])
    if violations:
        print_info("\nCompliance Violations:")
        for violation in violations:
            print(f"\n{Fore.RED}Standard: {violation['standard_name']} ({violation['standard_id']}){Style.RESET_ALL}")
            print(f"Requirement: {violation['requirement_name']} ({violation['requirement_id']})")
            print(f"Severity: {violation['severity']}")
            print(f"Description: {violation['description']}")
            
            if violation.get('remediation_steps'):
                print(f"\n{Fore.YELLOW}Remediation Steps:{Style.RESET_ALL}")
                for step in violation['remediation_steps']:
                    print(f"- {step}")
    
    # Save report to file if output specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print_success(f"Report saved to {args.output}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Policy-as-Code CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List policies
    list_parser = subparsers.add_parser("list", help="List policies")
    list_parser.add_argument("--type", help="Filter by policy type")
    list_parser.add_argument("--status", help="Filter by policy status")
    list_parser.add_argument("--environment", help="Filter by environment")
    list_parser.add_argument("--tags", help="Filter by tags (comma-separated)")
    list_parser.set_defaults(func=list_policies)
    
    # Get policy
    get_parser = subparsers.add_parser("get", help="Get a policy by ID")
    get_parser.add_argument("id", help="Policy ID")
    get_parser.add_argument("--output", "-o", help="Output file path")
    get_parser.set_defaults(func=get_policy)
    
    # Create policy
    create_parser = subparsers.add_parser("create", help="Create a new policy")
    create_parser.add_argument("file", help="Policy file path")
    create_parser.set_defaults(func=create_policy)
    
    # Update policy
    update_parser = subparsers.add_parser("update", help="Update an existing policy")
    update_parser.add_argument("id", help="Policy ID")
    update_parser.add_argument("file", help="Policy file path")
    update_parser.set_defaults(func=update_policy)
    
    # Delete policy
    delete_parser = subparsers.add_parser("delete", help="Delete a policy")
    delete_parser.add_argument("id", help="Policy ID")
    delete_parser.add_argument("--force", "-f", action="store_true", help="Force deletion without confirmation")
    delete_parser.set_defaults(func=delete_policy)
    
    # Validate policy
    validate_parser = subparsers.add_parser("validate", help="Validate a policy")
    validate_parser.add_argument("file", help="Policy file path")
    validate_parser.set_defaults(func=validate_policy)
    
    # Evaluate resource
    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate a resource against policies")
    evaluate_parser.add_argument("file", help="Resource file path")
    evaluate_parser.add_argument("--policy-id", help="Filter by policy ID")
    evaluate_parser.add_argument("--policy-type", help="Filter by policy type")
    evaluate_parser.set_defaults(func=evaluate_resource)
    
    # List policy versions
    versions_parser = subparsers.add_parser("versions", help="List versions of a policy")
    versions_parser.add_argument("id", help="Policy ID")
    versions_parser.set_defaults(func=list_policy_versions)
    
    # Get policy version
    version_parser = subparsers.add_parser("version", help="Get a specific version of a policy")
    version_parser.add_argument("id", help="Policy ID")
    version_parser.add_argument("version", help="Policy version")
    version_parser.add_argument("--output", "-o", help="Output file path")
    version_parser.set_defaults(func=get_policy_version)
    
    # Restore policy version
    restore_parser = subparsers.add_parser("restore", help="Restore a policy to a previous version")
    restore_parser.add_argument("id", help="Policy ID")
    restore_parser.add_argument("version", help="Policy version to restore")
    restore_parser.set_defaults(func=restore_policy_version)
    
    # Compare policy versions
    compare_parser = subparsers.add_parser("compare", help="Compare two versions of a policy")
    compare_parser.add_argument("id", help="Policy ID")
    compare_parser.add_argument("version1", help="First version to compare")
    compare_parser.add_argument("version2", help="Second version to compare")
    compare_parser.set_defaults(func=compare_policy_versions)
    
    # Generate compliance report
    report_parser = subparsers.add_parser("report", help="Generate a compliance report")
    report_parser.add_argument("file", help="Resource file path")
    report_parser.add_argument("--standards", help="Compliance standards to report on (comma-separated)")
    report_parser.add_argument("--output", "-o", help="Output file path")
    report_parser.set_defaults(func=generate_compliance_report)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)

if __name__ == "__main__":
    main()
