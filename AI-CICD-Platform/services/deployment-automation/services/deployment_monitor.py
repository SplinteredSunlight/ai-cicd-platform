"""
Deployment Monitor Service

This module implements the deployment monitoring service, which is responsible for
monitoring and verifying deployments.
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from models.monitoring import (
    HealthCheck,
    Metric,
    MetricBaseline,
    Alert,
    MonitoringRule,
    MonitoringDashboard,
    MonitoringPanel,
    PerformanceTest,
    MonitoringIntegration,
    UserImpactAnalysis,
    DeploymentVerification
)

# Configure logging
logger = logging.getLogger(__name__)

class DeploymentMonitor:
    """
    Service for monitoring and verifying deployments.
    """
    
    def __init__(self):
        """
        Initialize the deployment monitor service.
        """
        logger.info("Initializing DeploymentMonitor service")
        # In a real implementation, these would be loaded from a database
        self.health_checks = {}
        self.metrics = {}
        self.baselines = {}
        self.alerts = {}
        self.rules = {}
        self.dashboards = {}
        self.panels = {}
        self.performance_tests = {}
        self.integrations = {}
        self.impact_analyses = {}
        self.verifications = {}
        
        # Initialize with some default monitoring rules
        self._initialize_default_rules()
        self._initialize_default_integrations()
        self._initialize_default_dashboards()
    
    def _initialize_default_rules(self):
        """
        Initialize default monitoring rules.
        """
        # CPU usage rule
        cpu_rule = MonitoringRule(
            id=str(uuid.uuid4()),
            name="High CPU Usage",
            description="Alert when CPU usage is too high",
            metric_type="cpu_usage",
            conditions={
                "threshold": 80,
                "duration_seconds": 300,
                "comparison": ">"
            },
            severity="high",
            actions=[
                {
                    "type": "alert",
                    "parameters": {
                        "channels": ["slack", "email"],
                        "message": "High CPU usage detected: {value}%"
                    }
                }
            ],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Memory usage rule
        memory_rule = MonitoringRule(
            id=str(uuid.uuid4()),
            name="High Memory Usage",
            description="Alert when memory usage is too high",
            metric_type="memory_usage",
            conditions={
                "threshold": 85,
                "duration_seconds": 300,
                "comparison": ">"
            },
            severity="high",
            actions=[
                {
                    "type": "alert",
                    "parameters": {
                        "channels": ["slack", "email"],
                        "message": "High memory usage detected: {value}%"
                    }
                }
            ],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Error rate rule
        error_rule = MonitoringRule(
            id=str(uuid.uuid4()),
            name="High Error Rate",
            description="Alert when error rate is too high",
            metric_type="error_rate",
            conditions={
                "threshold": 5,
                "duration_seconds": 300,
                "comparison": ">"
            },
            severity="critical",
            actions=[
                {
                    "type": "alert",
                    "parameters": {
                        "channels": ["slack", "email", "pagerduty"],
                        "message": "High error rate detected: {value}%"
                    }
                },
                {
                    "type": "rollback_trigger",
                    "parameters": {
                        "automatic": False,
                        "approval_required": True
                    }
                }
            ],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Response time rule
        response_rule = MonitoringRule(
            id=str(uuid.uuid4()),
            name="Slow Response Time",
            description="Alert when response time is too slow",
            metric_type="response_time",
            conditions={
                "threshold": 1000,
                "duration_seconds": 300,
                "comparison": ">"
            },
            severity="medium",
            actions=[
                {
                    "type": "alert",
                    "parameters": {
                        "channels": ["slack", "email"],
                        "message": "Slow response time detected: {value}ms"
                    }
                }
            ],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Add rules to the in-memory store
        self.rules[cpu_rule.id] = cpu_rule
        self.rules[memory_rule.id] = memory_rule
        self.rules[error_rule.id] = error_rule
        self.rules[response_rule.id] = response_rule
    
    def _initialize_default_integrations(self):
        """
        Initialize default monitoring integrations.
        """
        # Prometheus integration
        prometheus = MonitoringIntegration(
            id=str(uuid.uuid4()),
            name="Prometheus",
            type="prometheus",
            configuration={
                "url": "http://prometheus:9090",
                "scrape_interval": 15,
                "metrics": ["cpu", "memory", "requests", "errors"]
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Datadog integration
        datadog = MonitoringIntegration(
            id=str(uuid.uuid4()),
            name="Datadog",
            type="datadog",
            configuration={
                "api_key": "your_api_key",
                "app_key": "your_app_key",
                "metrics": ["cpu", "memory", "requests", "errors"]
            },
            status="disabled",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # CloudWatch integration
        cloudwatch = MonitoringIntegration(
            id=str(uuid.uuid4()),
            name="CloudWatch",
            type="cloudwatch",
            configuration={
                "region": "us-west-2",
                "namespace": "AWS/EC2",
                "metrics": ["CPUUtilization", "MemoryUtilization"]
            },
            status="disabled",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Add integrations to the in-memory store
        self.integrations[prometheus.id] = prometheus
        self.integrations[datadog.id] = datadog
        self.integrations[cloudwatch.id] = cloudwatch
    
    def _initialize_default_dashboards(self):
        """
        Initialize default monitoring dashboards.
        """
        # Create a dashboard
        dashboard = MonitoringDashboard(
            id=str(uuid.uuid4()),
            name="Deployment Overview",
            description="Overview of deployment metrics",
            panels=[],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Create panels
        cpu_panel = MonitoringPanel(
            id=str(uuid.uuid4()),
            dashboard_id=dashboard.id,
            name="CPU Usage",
            type="chart",
            metrics=["cpu_usage"],
            options={
                "chart_type": "line",
                "time_range": "1h"
            },
            position={
                "x": 0,
                "y": 0,
                "width": 6,
                "height": 4
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        memory_panel = MonitoringPanel(
            id=str(uuid.uuid4()),
            dashboard_id=dashboard.id,
            name="Memory Usage",
            type="chart",
            metrics=["memory_usage"],
            options={
                "chart_type": "line",
                "time_range": "1h"
            },
            position={
                "x": 6,
                "y": 0,
                "width": 6,
                "height": 4
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        error_panel = MonitoringPanel(
            id=str(uuid.uuid4()),
            dashboard_id=dashboard.id,
            name="Error Rate",
            type="chart",
            metrics=["error_rate"],
            options={
                "chart_type": "line",
                "time_range": "1h"
            },
            position={
                "x": 0,
                "y": 4,
                "width": 6,
                "height": 4
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        response_panel = MonitoringPanel(
            id=str(uuid.uuid4()),
            dashboard_id=dashboard.id,
            name="Response Time",
            type="chart",
            metrics=["response_time"],
            options={
                "chart_type": "line",
                "time_range": "1h"
            },
            position={
                "x": 6,
                "y": 4,
                "width": 6,
                "height": 4
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Add panels to the dashboard
        dashboard.panels = [cpu_panel.id, memory_panel.id, error_panel.id, response_panel.id]
        
        # Add dashboard and panels to the in-memory store
        self.dashboards[dashboard.id] = dashboard
        self.panels[cpu_panel.id] = cpu_panel
        self.panels[memory_panel.id] = memory_panel
        self.panels[error_panel.id] = error_panel
        self.panels[response_panel.id] = response_panel
    
    def create_health_check(self, deployment_id: str, environment_id: str, status: str, checks: List[Dict[str, Any]]) -> HealthCheck:
        """
        Create a health check for a deployment.
        
        Args:
            deployment_id (str): Deployment ID
            environment_id (str): Environment ID
            status (str): Health check status
            checks (List[Dict[str, Any]]): List of checks performed
            
        Returns:
            HealthCheck: Created health check
        """
        # Create a new health check ID
        health_check_id = str(uuid.uuid4())
        
        # Create the health check
        health_check = HealthCheck(
            id=health_check_id,
            deployment_id=deployment_id,
            environment_id=environment_id,
            status=status,
            checks=checks,
            timestamp=datetime.now().isoformat()
        )
        
        self.health_checks[health_check_id] = health_check
        logger.info(f"Created health check: {health_check_id}")
        
        return health_check
    
    def get_health_checks(self, deployment_id: Optional[str] = None, environment_id: Optional[str] = None) -> List[HealthCheck]:
        """
        Get all health checks, optionally filtered by deployment ID or environment ID.
        
        Args:
            deployment_id (Optional[str]): Deployment ID to filter by
            environment_id (Optional[str]): Environment ID to filter by
            
        Returns:
            List[HealthCheck]: List of health checks
        """
        health_checks = list(self.health_checks.values())
        
        if deployment_id:
            health_checks = [hc for hc in health_checks if hc.deployment_id == deployment_id]
        
        if environment_id:
            health_checks = [hc for hc in health_checks if hc.environment_id == environment_id]
        
        return health_checks
    
    def get_health_check(self, health_check_id: str) -> Optional[HealthCheck]:
        """
        Get a health check by ID.
        
        Args:
            health_check_id (str): Health check ID
            
        Returns:
            Optional[HealthCheck]: Health check if found, None otherwise
        """
        return self.health_checks.get(health_check_id)
    
    def create_metric(self, deployment_id: str, environment_id: str, name: str, metric_type: str, unit: str, description: str, values: List[Dict[str, Any]], tags: Dict[str, Any] = None) -> Metric:
        """
        Create a metric for a deployment.
        
        Args:
            deployment_id (str): Deployment ID
            environment_id (str): Environment ID
            name (str): Metric name
            metric_type (str): Metric type
            unit (str): Metric unit
            description (str): Metric description
            values (List[Dict[str, Any]]): Metric values
            tags (Dict[str, Any], optional): Metric tags
            
        Returns:
            Metric: Created metric
        """
        # Create a new metric ID
        metric_id = str(uuid.uuid4())
        
        # Create the metric
        metric = Metric(
            id=metric_id,
            deployment_id=deployment_id,
            environment_id=environment_id,
            name=name,
            type=metric_type,
            unit=unit,
            description=description,
            values=values,
            tags=tags or {}
        )
        
        self.metrics[metric_id] = metric
        logger.info(f"Created metric: {metric_id}")
        
        return metric
    
    def get_metrics(self, deployment_id: Optional[str] = None, environment_id: Optional[str] = None, metric_type: Optional[str] = None) -> List[Metric]:
        """
        Get all metrics, optionally filtered by deployment ID, environment ID, or metric type.
        
        Args:
            deployment_id (Optional[str]): Deployment ID to filter by
            environment_id (Optional[str]): Environment ID to filter by
            metric_type (Optional[str]): Metric type to filter by
            
        Returns:
            List[Metric]: List of metrics
        """
        metrics = list(self.metrics.values())
        
        if deployment_id:
            metrics = [m for m in metrics if m.deployment_id == deployment_id]
        
        if environment_id:
            metrics = [m for m in metrics if m.environment_id == environment_id]
        
        if metric_type:
            metrics = [m for m in metrics if m.type == metric_type]
        
        return metrics
    
    def get_metric(self, metric_id: str) -> Optional[Metric]:
        """
        Get a metric by ID.
        
        Args:
            metric_id (str): Metric ID
            
        Returns:
            Optional[Metric]: Metric if found, None otherwise
        """
        return self.metrics.get(metric_id)
    
    def update_metric(self, metric_id: str, values: List[Dict[str, Any]]) -> Optional[Metric]:
        """
        Update a metric with new values.
        
        Args:
            metric_id (str): Metric ID
            values (List[Dict[str, Any]]): New metric values
            
        Returns:
            Optional[Metric]: Updated metric if found, None otherwise
        """
        metric = self.get_metric(metric_id)
        if not metric:
            return None
        
        metric.values.extend(values)
        
        self.metrics[metric_id] = metric
        logger.info(f"Updated metric: {metric_id}")
        
        return metric
    
    def create_baseline(self, metric_id: str, deployment_id: str, environment_id: str, metric_name: str, min_value: float, max_value: float, avg_value: float, p95_value: float, p99_value: float) -> MetricBaseline:
        """
        Create a baseline for a metric.
        
        Args:
            metric_id (str): Metric ID
            deployment_id (str): Deployment ID
            environment_id (str): Environment ID
            metric_name (str): Metric name
            min_value (float): Minimum value
            max_value (float): Maximum value
            avg_value (float): Average value
            p95_value (float): 95th percentile value
            p99_value (float): 99th percentile value
            
        Returns:
            MetricBaseline: Created baseline
        """
        # Create a new baseline ID
        baseline_id = str(uuid.uuid4())
        
        # Create the baseline
        baseline = MetricBaseline(
            id=baseline_id,
            metric_id=metric_id,
            deployment_id=deployment_id,
            environment_id=environment_id,
            metric_name=metric_name,
            min=min_value,
            max=max_value,
            avg=avg_value,
            p95=p95_value,
            p99=p99_value,
            updated_at=datetime.now().isoformat()
        )
        
        self.baselines[baseline_id] = baseline
        logger.info(f"Created baseline: {baseline_id}")
        
        return baseline
    
    def get_baselines(self, metric_id: Optional[str] = None, deployment_id: Optional[str] = None, environment_id: Optional[str] = None) -> List[MetricBaseline]:
        """
        Get all baselines, optionally filtered by metric ID, deployment ID, or environment ID.
        
        Args:
            metric_id (Optional[str]): Metric ID to filter by
            deployment_id (Optional[str]): Deployment ID to filter by
            environment_id (Optional[str]): Environment ID to filter by
            
        Returns:
            List[MetricBaseline]: List of baselines
        """
        baselines = list(self.baselines.values())
        
        if metric_id:
            baselines = [b for b in baselines if b.metric_id == metric_id]
        
        if deployment_id:
            baselines = [b for b in baselines if b.deployment_id == deployment_id]
        
        if environment_id:
            baselines = [b for b in baselines if b.environment_id == environment_id]
        
        return baselines
    
    def get_baseline(self, baseline_id: str) -> Optional[MetricBaseline]:
        """
        Get a baseline by ID.
        
        Args:
            baseline_id (str): Baseline ID
            
        Returns:
            Optional[MetricBaseline]: Baseline if found, None otherwise
        """
        return self.baselines.get(baseline_id)
    
    def create_alert(self, deployment_id: str, environment_id: str, rule_id: str, metric_id: Optional[str], severity: str, message: str, details: Dict[str, Any]) -> Alert:
        """
        Create an alert for a deployment.
        
        Args:
            deployment_id (str): Deployment ID
            environment_id (str): Environment ID
            rule_id (str): Rule ID
            metric_id (Optional[str]): Metric ID
            severity (str): Alert severity
            message (str): Alert message
            details (Dict[str, Any]): Alert details
            
        Returns:
            Alert: Created alert
        """
        # Create a new alert ID
        alert_id = str(uuid.uuid4())
        
        # Create the alert
        alert = Alert(
            id=alert_id,
            deployment_id=deployment_id,
            environment_id=environment_id,
            rule_id=rule_id,
            metric_id=metric_id,
            severity=severity,
            message=message,
            details=details,
            status="active",
            timestamp=datetime.now().isoformat()
        )
        
        self.alerts[alert_id] = alert
        logger.info(f"Created alert: {alert_id}")
        
        return alert
    
    def get_alerts(self, deployment_id: Optional[str] = None, environment_id: Optional[str] = None, status: Optional[str] = None) -> List[Alert]:
        """
        Get all alerts, optionally filtered by deployment ID, environment ID, or status.
        
        Args:
            deployment_id (Optional[str]): Deployment ID to filter by
            environment_id (Optional[str]): Environment ID to filter by
            status (Optional[str]): Status to filter by
            
        Returns:
            List[Alert]: List of alerts
        """
        alerts = list(self.alerts.values())
        
        if deployment_id:
            alerts = [a for a in alerts if a.deployment_id == deployment_id]
        
        if environment_id:
            alerts = [a for a in alerts if a.environment_id == environment_id]
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        
        return alerts
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """
        Get an alert by ID.
        
        Args:
            alert_id (str): Alert ID
            
        Returns:
            Optional[Alert]: Alert if found, None otherwise
        """
        return self.alerts.get(alert_id)
    
    def resolve_alert(self, alert_id: str) -> Optional[Alert]:
        """
        Resolve an alert.
        
        Args:
            alert_id (str): Alert ID
            
        Returns:
            Optional[Alert]: Resolved alert if found, None otherwise
        """
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        
        alert.status = "resolved"
        alert.resolved_at = datetime.now().isoformat()
        
        self.alerts[alert_id] = alert
        logger.info(f"Resolved alert: {alert_id}")
        
        return alert
    
    def get_rules(self, metric_type: Optional[str] = None) -> List[MonitoringRule]:
        """
        Get all monitoring rules, optionally filtered by metric type.
        
        Args:
            metric_type (Optional[str]): Metric type to filter by
            
        Returns:
            List[MonitoringRule]: List of monitoring rules
        """
        if metric_type:
            return [rule for rule in self.rules.values() if rule.metric_type == metric_type]
        else:
            return list(self.rules.values())
    
    def get_rule(self, rule_id: str) -> Optional[MonitoringRule]:
        """
        Get a monitoring rule by ID.
        
        Args:
            rule_id (str): Rule ID
            
        Returns:
            Optional[MonitoringRule]: Monitoring rule if found, None otherwise
        """
        return self.rules.get(rule_id)
    
    def create_rule(self, rule: MonitoringRule) -> MonitoringRule:
        """
        Create a new monitoring rule.
        
        Args:
            rule (MonitoringRule): Monitoring rule to create
            
        Returns:
            MonitoringRule: Created monitoring rule
        """
        if not rule.id:
            rule.id = str(uuid.uuid4())
        
        rule.created_at = datetime.now().isoformat()
        rule.updated_at = datetime.now().isoformat()
        
        self.rules[rule.id] = rule
        logger.info(f"Created monitoring rule: {rule.id}")
        
        return rule
    
    def update_rule(self, rule_id: str, rule: MonitoringRule) -> Optional[MonitoringRule]:
        """
        Update an existing monitoring rule.
        
        Args:
            rule_id (str): Rule ID
            rule (MonitoringRule): Updated monitoring rule
            
        Returns:
            Optional[MonitoringRule]: Updated monitoring rule if found, None otherwise
        """
        if rule_id not in self.rules:
            return None
        
        rule.id = rule_id
        rule.updated_at = datetime.now().isoformat()
        
        self.rules[rule_id] = rule
        logger.info(f"Updated monitoring rule: {rule_id}")
        
        return rule
    
    def delete_rule(self, rule_id: str) -> bool:
        """
        Delete a monitoring rule.
        
        Args:
            rule_id (str): Rule ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        if rule_id not in self.rules:
            return False
        
        del self.rules[rule_id]
        logger.info(f"Deleted monitoring rule: {rule_id}")
        
        return True
    
    def check_rules(self, deployment_id: str, environment_id: str, metrics: Dict[str, Any]) -> List[Alert]:
        """
        Check if any rules should trigger alerts based on the provided metrics.
        
        Args:
            deployment_id (str): Deployment ID
            environment_id (str): Environment ID
            metrics (Dict[str, Any]): Metrics to check against rules
            
        Returns:
            List[Alert]: List of triggered alerts
        """
        triggered_alerts = []
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            if rule.metric_type not in metrics:
                continue
            
            metric_value = metrics[rule.metric_type]
            threshold = rule.conditions.get("threshold")
            comparison = rule.conditions.get("comparison", ">")
            
            # Check if the rule conditions are met
            if comparison == ">" and metric_value > threshold:
                # Create an alert
                alert = self.create_alert(
                    deployment_id=deployment_id,
                    environment_id=environment_id,
                    rule_id=rule.id,
                    metric_id=None,  # In a real implementation, this would be the actual metric ID
                    severity=rule.severity,
                    message=rule.actions[0]["parameters"]["message"].format(value=metric_value),
                    details={
                        "metric_type": rule.metric_type,
                        "metric_value": metric_value,
                        "threshold": threshold,
                        "comparison": comparison
                    }
                )
                
                triggered_alerts.append(alert)
                logger.info(f"Rule triggered: {rule.id}, created alert: {alert.id}")
            
            elif comparison == "<" and metric_value < threshold:
                # Create an alert
                alert = self.create_alert(
                    deployment_id=deployment_id,
                    environment_id=environment_id,
                    rule_id=rule.id,
                    metric_id=None,  # In a real implementation, this would be the actual metric ID
                    severity=rule.severity,
                    message=rule.actions[0]["parameters"]["message"].format(value=metric_value),
                    details={
                        "metric_type": rule.metric_type,
                        "metric_value": metric_value,
                        "threshold": threshold,
                        "comparison": comparison
                    }
                )
                
                triggered_alerts.append(alert)
                logger.info(f"Rule triggered: {rule.id}, created alert: {alert.id}")
            
            elif comparison == "==" and metric_value == threshold:
                # Create an alert
                alert = self.create_alert(
                    deployment_id=deployment_id,
                    environment_id=environment_id,
                    rule_id=rule.id,
                    metric_id=None,  # In a real implementation, this would be the actual metric ID
                    severity=rule.severity,
                    message=rule.actions[0]["parameters"]["message"].format(value=metric_value),
                    details={
                        "metric_type": rule.metric_type,
                        "metric_value": metric_value,
                        "threshold": threshold,
                        "comparison": comparison
                    }
                )
                
                triggered_alerts.append(alert)
                logger.info(f"Rule triggered: {rule.id}, created alert: {alert.id}")
        
        return triggered_alerts
    
    def get_dashboards(self) -> List[MonitoringDashboard]:
        """
        Get all monitoring dashboards.
        
        Returns:
            List[MonitoringDashboard]: List of monitoring dashboards
        """
        return list(self.dashboards.values())
    
    def get_dashboard(self, dashboard_id: str) -> Optional[MonitoringDashboard]:
        """
        Get a monitoring dashboard by ID.
        
        Args:
            dashboard_id (str): Dashboard ID
            
        Returns:
            Optional[MonitoringDashboard]: Monitoring dashboard if found, None otherwise
        """
        return self.dashboards.get(dashboard_id)
    
    def create_dashboard(self, dashboard: MonitoringDashboard) -> MonitoringDashboard:
        """
        Create a new monitoring dashboard.
        
        Args:
            dashboard (MonitoringDashboard): Monitoring dashboard to create
            
        Returns:
            MonitoringDashboard: Created monitoring dashboard
        """
        if not dashboard.id:
            dashboard.id = str(uuid.uuid4())
        
        dashboard.created_at = datetime.now().isoformat()
        dashboard.updated_at = datetime.now().isoformat()
        
        self.dashboards[dashboard.id] = dashboard
        logger.info(f"Created monitoring dashboard: {dashboard.id}")
        
        return dashboard
    
    def update_dashboard(self, dashboard_id: str, dashboard: MonitoringDashboard) -> Optional[MonitoringDashboard]:
        """
        Update an existing monitoring dashboard.
        
        Args:
            dashboard_id (str): Dashboard ID
            dashboard (MonitoringDashboard): Updated monitoring dashboard
            
        Returns:
            Optional[MonitoringDashboard]: Updated monitoring dashboard if found, None otherwise
        """
        if dashboard_id not in self.dashboards:
            return None
        
        dashboard.id = dashboard_id
        dashboard.updated_at = datetime.now().isoformat()
        
        self.dashboards[dashboard_id] = dashboard
        logger.info(f"Updated monitoring dashboard: {dashboard_id}")
        
        return dashboard
    
    def delete_dashboard(self, dashboard_id: str) -> bool:
        """
        Delete a monitoring dashboard.
        
        Args:
            dashboard_id (str): Dashboard ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        if dashboard_id not in self.dashboards:
            return False
        
        # Delete all panels associated with the dashboard
        panels_to_delete = [panel_id for panel_id, panel in self.panels.items() if panel.dashboard_id == dashboard_id]
        for panel_id in panels_to_delete:
            del self.panels[panel_id]
        
        del self.dashboards[dashboard_id]
        logger.info(f"Deleted monitoring dashboard: {dashboard_id}")
        
        return True
    
    def get_panels(self, dashboard_id: Optional[str] = None) -> List[MonitoringPanel]:
        """
        Get all monitoring panels, optionally filtered by dashboard ID.
        
        Args:
            dashboard_id (Optional[str]): Dashboard ID to filter by
            
        Returns:
            List[MonitoringPanel]: List of monitoring panels
        """
        if dashboard_id:
            return [panel for panel in self.panels.values() if panel.dashboard_id == dashboard_id]
        else:
            return list(self.panels.values())
    
    def get_panel(self, panel_id: str) -> Optional[MonitoringPanel]:
        """
        Get a monitoring panel by ID.
        
        Args:
            panel_id (str): Panel ID
            
        Returns:
            Optional[MonitoringPanel]: Monitoring panel if found, None otherwise
        """
        return self.panels.get(panel_id)
