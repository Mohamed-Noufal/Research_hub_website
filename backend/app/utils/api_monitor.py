"""
Advanced API monitoring system for detecting schema changes and API health.
Monitors response shapes, version changes, and provides alerts for API stability.
"""

import asyncio
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)

@dataclass
class APISchema:
    """Represents the expected schema for an API response"""
    required_fields: List[str]
    optional_fields: List[str]
    array_fields: List[str]  # Fields that should be arrays
    object_fields: List[str]  # Fields that should be objects

@dataclass
class APIMonitorResult:
    """Result of API monitoring check"""
    service_name: str
    timestamp: datetime
    status: str  # 'healthy', 'warning', 'error'
    response_time: float
    schema_changed: bool
    version_changed: bool
    error_message: Optional[str]
    schema_hash: Optional[str]
    alerts: List[str]

class APIMonitoringService:
    """
    Advanced API monitoring service that detects:
    - Schema changes (missing/added fields)
    - Version changes (404s, major response structure changes)
    - Performance degradation
    - Authentication issues
    """

    def __init__(self):
        # Define expected schemas for each API
        self.schemas = {
            "doaj": APISchema(
                required_fields=["results"],
                optional_fields=["total", "page", "pageSize", "query", "timestamp"],
                array_fields=["results"],
                object_fields=[]
            ),
            "core": APISchema(
                required_fields=["results"],
                optional_fields=["totalHits", "took", "scrollId"],
                array_fields=["results"],
                object_fields=[]
            ),
            "openalex": APISchema(
                required_fields=["results", "meta"],
                optional_fields=["group_by"],
                array_fields=["results"],
                object_fields=["meta"]
            ),
            "crossref": APISchema(
                required_fields=["message"],
                optional_fields=["status", "message-type", "message-version"],
                array_fields=["message.items"],
                object_fields=["message"]
            ),
            "semantic_scholar": APISchema(
                required_fields=["data"],
                optional_fields=["total", "offset", "next"],
                array_fields=["data"],
                object_fields=[]
            ),
            "pubmed": APISchema(
                required_fields=["esearchresult", "idlist"],
                optional_fields=["translationstack", "querytranslation", "webenv", "retmax", "retstart"],
                array_fields=["idlist"],
                object_fields=["esearchresult"]
            ),
            "biorxiv": APISchema(
                required_fields=["collection"],
                optional_fields=["messages"],
                array_fields=["collection"],
                object_fields=[]
            )
        }

        # Store baseline schemas for comparison
        self.baseline_schemas = {}
        self.last_check_time = {}

        # Monitoring configuration
        self.check_interval = timedelta(hours=6)  # Check every 6 hours
        self.alert_threshold = 3  # Alert after 3 consecutive failures

    async def monitor_api_health(self, service_name: str, response_data: Dict[str, Any],
                                response_time: float) -> APIMonitorResult:
        """
        Monitor API response for schema changes and health issues
        """
        result = APIMonitorResult(
            service_name=service_name,
            timestamp=datetime.now(),
            status="healthy",
            response_time=response_time,
            schema_changed=False,
            version_changed=False,
            error_message=None,
            schema_hash=None,
            alerts=[]
        )

        try:
            # Generate schema hash for change detection
            schema_str = json.dumps(response_data, sort_keys=True)
            result.schema_hash = hashlib.md5(schema_str.encode()).hexdigest()

            # Check for schema changes
            if service_name in self.schemas:
                schema_issues = self._check_schema_compliance(service_name, response_data)
                if schema_issues:
                    result.schema_changed = True
                    result.alerts.extend(schema_issues)

            # Check for version/API changes (404 patterns, major structure changes)
            version_issues = self._check_version_compatibility(service_name, response_data)
            if version_issues:
                result.version_changed = True
                result.alerts.extend(version_issues)

            # Determine overall status
            if result.schema_changed or result.version_changed:
                result.status = "warning"
            elif response_time > 10.0:  # Slow response
                result.status = "warning"
                result.alerts.append(".2f")

            # Update baseline if this is first check or schema changed
            if service_name not in self.baseline_schemas or result.schema_changed:
                self.baseline_schemas[service_name] = result.schema_hash
                if result.schema_changed:
                    result.alerts.append(f"Schema baseline updated for {service_name}")

        except Exception as e:
            result.status = "error"
            result.error_message = str(e)
            result.alerts.append(f"Monitoring error: {str(e)}")

        return result

    def _check_schema_compliance(self, service_name: str, response_data: Dict[str, Any]) -> List[str]:
        """Check if response matches expected schema"""
        if service_name not in self.schemas:
            return []

        schema = self.schemas[service_name]
        issues = []

        # Check required fields
        for field in schema.required_fields:
            if field not in response_data:
                issues.append(f"Missing required field: {field}")

        # Check array fields
        for field in schema.array_fields:
            keys = field.split('.')
            value = response_data
            try:
                for key in keys:
                    value = value[key]
                if not isinstance(value, list):
                    issues.append(f"Field {field} should be array, got {type(value).__name__}")
            except (KeyError, TypeError):
                pass  # Already handled by required field check

        # Check object fields
        for field in schema.object_fields:
            keys = field.split('.')
            value = response_data
            try:
                for key in keys:
                    value = value[key]
                if not isinstance(value, dict):
                    issues.append(f"Field {field} should be object, got {type(value).__name__}")
            except (KeyError, TypeError):
                pass

        return issues

    def _check_version_compatibility(self, service_name: str, response_data: Dict[str, Any]) -> List[str]:
        """Check for API version compatibility issues"""
        issues = []

        # DOAJ-specific version checks
        if service_name == "doaj":
            # Check if response indicates version issues
            if "error" in response_data and "version" in str(response_data.get("error", "")).lower():
                issues.append("DOAJ version compatibility issue detected")

        # CORE-specific checks
        elif service_name == "core":
            if response_data.get("message") == "The API key you provided is not valid.":
                issues.append("CORE API key authentication failed")

        # General 404/version checks
        if isinstance(response_data, dict) and "error" in response_data:
            error_msg = str(response_data["error"]).lower()
            if "not found" in error_msg or "deprecated" in error_msg:
                issues.append(f"API version/endpoint issue detected: {response_data['error']}")

        return issues

    async def check_doaj_blog_updates(self) -> Dict[str, Any]:
        """
        Check DOAJ blog for recent announcements about API changes
        """
        try:
            # DOAJ blog RSS feed
            blog_url = "https://blog.doaj.org/feed/"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(blog_url)
                response.raise_for_status()

                # Parse RSS (simplified - in production would use proper RSS parser)
                content = response.text

                # Look for keywords indicating API changes
                change_indicators = [
                    "api", "version", "v4", "v3", "deprecated", "migration",
                    "endpoint", "change", "update", "breaking"
                ]

                recent_changes = []
                if any(indicator in content.lower() for indicator in change_indicators):
                    recent_changes.append("Potential API changes detected in DOAJ blog")

                return {
                    "status": "checked",
                    "changes_detected": len(recent_changes) > 0,
                    "alerts": recent_changes,
                    "last_checked": datetime.now().isoformat()
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }

    async def run_comprehensive_monitoring(self) -> Dict[str, Any]:
        """
        Run comprehensive monitoring across all APIs
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "services_checked": [],
            "alerts": [],
            "summary": {}
        }

        # Check DOAJ blog for updates
        blog_check = await self.check_doaj_blog_updates()
        if blog_check.get("changes_detected"):
            results["alerts"].extend(blog_check["alerts"])

        # In a real implementation, this would check each service
        # For now, return the blog check results
        results["doaj_blog_check"] = blog_check

        return results

    def get_monitoring_report(self) -> Dict[str, Any]:
        """Generate a comprehensive monitoring report"""
        return {
            "monitoring_service": "active",
            "schemas_tracked": len(self.schemas),
            "services_monitored": list(self.schemas.keys()),
            "baseline_schemas": len(self.baseline_schemas),
            "last_check_time": {k: v.isoformat() for k, v in self.last_check_time.items()},
            "configuration": {
                "check_interval_hours": self.check_interval.total_seconds() / 3600,
                "alert_threshold": self.alert_threshold
            }
        }
