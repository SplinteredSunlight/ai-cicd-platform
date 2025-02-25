from typing import List, Dict, Optional
import time
from datetime import datetime
from zapv2 import ZAPv2
from ..config import get_settings, ZAP_CONFIG, SeverityLevel
from ..models.vulnerability import Vulnerability, VulnerabilityReport

class ZAPScanner:
    def __init__(self):
        self.settings = get_settings()
        self.config = ZAP_CONFIG
        self.zap = None
        self.api_key = self.settings.zap_api_key

    async def connect(self, proxy_url: str = "http://localhost:8080"):
        """
        Connect to ZAP instance
        """
        try:
            self.zap = ZAPv2(apikey=self.api_key, proxies={'http': proxy_url, 'https': proxy_url})
            return await self._wait_for_zap_start()
        except Exception as e:
            raise Exception(f"Failed to connect to ZAP: {str(e)}")

    async def scan_webapp(self, target_url: str, scan_type: str = "baseline") -> VulnerabilityReport:
        """
        Scan a web application using OWASP ZAP
        """
        if not self.zap:
            raise Exception("ZAP not connected. Call connect() first.")

        try:
            # Start new session
            self.zap.core.new_session()

            # Configure scan policy based on scan type
            if scan_type == "full":
                policy = self._configure_full_scan_policy()
            else:
                policy = self._configure_baseline_scan_policy()

            # Access the target URL
            self.zap.urlopen(target_url)
            time.sleep(2)  # Wait for the page to load

            # Spider the target
            scan_id = self.zap.spider.scan(target_url)
            await self._wait_for_spider(scan_id)

            if self.config["config_params"]["ajax_spider"]:
                await self._run_ajax_spider(target_url)

            # Run active scan
            scan_id = self.zap.ascan.scan(target_url, policy=policy)
            await self._wait_for_scan(scan_id)

            # Generate report
            alerts = self.zap.core.alerts()
            return self._parse_scan_results(alerts, target_url)

        except Exception as e:
            raise Exception(f"ZAP scan error: {str(e)}")

    async def _wait_for_zap_start(self, timeout: int = 60) -> bool:
        """
        Wait for ZAP to be ready
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                self.zap.core.apis
                return True
            except:
                time.sleep(2)
        raise Exception("ZAP failed to start within timeout")

    async def _wait_for_spider(self, scan_id: str, timeout: int = 600):
        """
        Wait for spider scan to complete
        """
        while int(self.zap.spider.status(scan_id)) < 100:
            time.sleep(5)
            if time.time() - start_time > timeout:
                raise Exception("Spider scan timed out")

    async def _run_ajax_spider(self, target_url: str, timeout: int = 600):
        """
        Run AJAX Spider for modern web applications
        """
        self.zap.ajaxSpider.scan(target_url)
        start_time = time.time()
        
        while self.zap.ajaxSpider.status == 'running':
            time.sleep(5)
            if time.time() - start_time > timeout:
                raise Exception("AJAX Spider scan timed out")

    async def _wait_for_scan(self, scan_id: str, timeout: int = 1800):
        """
        Wait for active scan to complete
        """
        start_time = time.time()
        while int(self.zap.ascan.status(scan_id)) < 100:
            time.sleep(10)
            if time.time() - start_time > timeout:
                raise Exception("Active scan timed out")

    def _configure_baseline_scan_policy(self) -> str:
        """
        Configure and return baseline scan policy
        """
        policy_name = "baseline_policy"
        self.zap.ascan.remove_scan_policy(policy_name)
        self.zap.ascan.add_scan_policy(policy_name)
        
        # Configure for quick baseline scan
        self.zap.ascan.set_policy_attack_strength(
            policy_name, "LOW", "ALL"
        )
        self.zap.ascan.set_policy_alert_threshold(
            policy_name, "MEDIUM", "ALL"
        )
        return policy_name

    def _configure_full_scan_policy(self) -> str:
        """
        Configure and return full scan policy
        """
        policy_name = "full_policy"
        self.zap.ascan.remove_scan_policy(policy_name)
        self.zap.ascan.add_scan_policy(policy_name)
        
        # Configure for thorough scan
        self.zap.ascan.set_policy_attack_strength(
            policy_name, "HIGH", "ALL"
        )
        self.zap.ascan.set_policy_alert_threshold(
            policy_name, "LOW", "ALL"
        )
        return policy_name

    def _parse_scan_results(self, alerts: List[Dict], target: str) -> VulnerabilityReport:
        """
        Parse ZAP alerts into standardized VulnerabilityReport
        """
        vulnerabilities = []

        for alert in alerts:
            severity = self._map_risk_to_severity(alert.get("risk"))
            
            vulnerability = Vulnerability(
                id=f"ZAP-{alert.get('pluginId', 'UNKNOWN')}",
                title=alert.get("name", "Unknown"),
                description=alert.get("description", "No description available"),
                severity=severity,
                cvss_score=self._calculate_cvss_score(severity),
                affected_component=f"{alert.get('url', target)}:{alert.get('parameter', 'N/A')}",
                fix_version=None,
                references=alert.get("reference", "").split("\n")
            )
            vulnerabilities.append(vulnerability)

        report = VulnerabilityReport(
            scanner_name="owasp_zap",
            scan_timestamp=datetime.utcnow().isoformat() + "Z",
            target=target,
            vulnerabilities=vulnerabilities,
            metadata={
                "scan_type": self.config["scan_types"],
                "ajax_spider": self.config["config_params"]["ajax_spider"],
                "recursive_scan": self.config["config_params"]["recursive_scan"]
            }
        )
        report.update_summary()
        return report

    def _map_risk_to_severity(self, risk: str) -> SeverityLevel:
        """
        Map ZAP risk levels to standardized severity levels
        """
        risk_mapping = {
            "High": SeverityLevel.HIGH,
            "Medium": SeverityLevel.MEDIUM,
            "Low": SeverityLevel.LOW,
            "Informational": SeverityLevel.INFO
        }
        return risk_mapping.get(risk, SeverityLevel.UNKNOWN)

    def _calculate_cvss_score(self, severity: SeverityLevel) -> float:
        """
        Estimate CVSS score based on severity level
        """
        cvss_mapping = {
            SeverityLevel.CRITICAL: 9.0,
            SeverityLevel.HIGH: 7.0,
            SeverityLevel.MEDIUM: 5.0,
            SeverityLevel.LOW: 3.0,
            SeverityLevel.INFO: 1.0,
            SeverityLevel.UNKNOWN: 0.0
        }
        return cvss_mapping.get(severity, 0.0)
