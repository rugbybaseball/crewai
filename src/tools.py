"""Stateful mock tools for the BCM CrewAI simulation.

This module replaces static proof-of-concept tool stubs with richer mock
integrations that emulate realistic operational friction. The tools are
designed to stay compatible with ``crewai.tools.BaseTool`` while exposing a
stable set of importable tool instances from ``src.tools``.

Key behaviors modeled:
- Network latency and degraded responses
- Per-tool rate limiting windows
- Timeout and partial failure scenarios
- Ambiguous telemetry requiring clarification or human escalation
- Stateful incident-management workflows across PagerDuty, Jira, and
  stakeholder notifications
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Literal, Optional

from crewai.tools import BaseTool


class ToolOperationalError(RuntimeError):
    """Base exception for mock tool operational failures."""


class ToolRateLimitError(ToolOperationalError):
    """Raised when a tool exceeds its configured request budget."""


class ToolTimeoutError(ToolOperationalError):
    """Raised when a mock external dependency times out."""


class ToolPartialFailureError(ToolOperationalError):
    """Raised when a dependency returns incomplete or degraded results."""


@dataclass
class ServiceRecord:
    """Represents a service and its recovery constraints."""

    name: str
    tier: str
    rto_minutes: int
    rpo_minutes: int
    customers: int
    revenue_loss_per_hour: int
    dependencies: List[str]
    regulators: List[str]
    current_status: str
    telemetry_health: Literal["healthy", "degraded", "ambiguous"] = "healthy"


@dataclass
class IncidentRecord:
    """Represents an incident tracked in the mock incident-management stack."""

    incident_id: str
    title: str
    severity: str
    status: str
    commander: str
    created_at: str
    service: Optional[str] = None
    pagerduty_id: Optional[str] = None
    jira_ticket: Optional[str] = None
    escalation_level: int = 1
    notes: List[str] = field(default_factory=list)


@dataclass
class NotificationReceipt:
    """Tracks stakeholder notification delivery outcomes."""

    receipt_id: str
    audience: str
    channel: str
    status: str
    delivered: int
    pending: int
    failed: int
    message_preview: str
    incident_id: Optional[str]
    created_at: str


class MockBCMEnvironment:
    """Shared state backing all mock tools.

    The environment maintains service inventory, incident records, delivery
    receipts, and request counters so tool calls feel stateful across the same
    Python process.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._rng = random.Random(42)
        self._request_counters: Dict[str, List[float]] = {}
        self._services: Dict[str, ServiceRecord] = {
            "mobile banking app": ServiceRecord(
                name="Mobile Banking App",
                tier="Tier-1 Critical",
                rto_minutes=240,
                rpo_minutes=15,
                customers=2_400_000,
                revenue_loss_per_hour=125_000,
                dependencies=["Core Banking API", "Auth Service", "Fraud Detection Engine"],
                regulators=["PCI-DSS", "SOX", "FFIEC"],
                current_status="degraded",
                telemetry_health="ambiguous",
            ),
            "online transfer service": ServiceRecord(
                name="Online Transfer Service",
                tier="Tier-1 Critical",
                rto_minutes=240,
                rpo_minutes=15,
                customers=1_800_000,
                revenue_loss_per_hour=95_000,
                dependencies=["Core Banking API", "Payment Gateway", "Fraud Detection Engine"],
                regulators=["PCI-DSS", "BSA/AML", "Reg E"],
                current_status="major_outage",
                telemetry_health="degraded",
            ),
            "fraud detection engine": ServiceRecord(
                name="Fraud Detection Engine",
                tier="Tier-1 Critical",
                rto_minutes=120,
                rpo_minutes=5,
                customers=4_200_000,
                revenue_loss_per_hour=75_000,
                dependencies=["ML Model Server", "Transaction DB", "Kafka"],
                regulators=["BSA/AML", "Reg E", "OCC"],
                current_status="degraded",
                telemetry_health="degraded",
            ),
            "core banking api": ServiceRecord(
                name="Core Banking API",
                tier="Tier-1 Critical",
                rto_minutes=120,
                rpo_minutes=10,
                customers=4_200_000,
                revenue_loss_per_hour=200_000,
                dependencies=["Primary DB", "Message Queue", "Secrets Manager"],
                regulators=["SOX", "OCC", "FFIEC"],
                current_status="major_outage",
                telemetry_health="ambiguous",
            ),
            "customer portal (web)": ServiceRecord(
                name="Customer Portal (Web)",
                tier="Tier-2 Important",
                rto_minutes=480,
                rpo_minutes=30,
                customers=900_000,
                revenue_loss_per_hour=35_000,
                dependencies=["Core Banking API", "CDN", "Auth Service"],
                regulators=["SOX"],
                current_status="degraded",
                telemetry_health="healthy",
            ),
            "internal reporting": ServiceRecord(
                name="Internal Reporting",
                tier="Tier-3 Normal",
                rto_minutes=1440,
                rpo_minutes=60,
                customers=500,
                revenue_loss_per_hour=5_000,
                dependencies=["Data Warehouse", "BI Gateway"],
                regulators=["SOX"],
                current_status="healthy",
                telemetry_health="healthy",
            ),
        }
        self._incidents: Dict[str, IncidentRecord] = {}
        self._notifications: Dict[str, NotificationReceipt] = {}
        self._knowledge_entries: List[Dict[str, str]] = []
        self._jira_counter = 100
        self._pd_counter = 3000
        self._incident_counter = 700
        self._receipt_counter = 1

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _normalize_service(self, service: str) -> Optional[str]:
        if not service:
            return None
        key = service.strip().lower()
        if key in self._services:
            return key
        for candidate, record in self._services.items():
            if key == record.name.lower():
                return candidate
        return None

    def rate_limit(self, tool_name: str, limit: int, window_seconds: int) -> None:
        """Enforce a simple sliding-window rate limit per tool."""
        with self._lock:
            now = time.time()
            recent = [stamp for stamp in self._request_counters.get(tool_name, []) if now - stamp < window_seconds]
            if len(recent) >= limit:
                raise ToolRateLimitError(
                    f"{tool_name} rate limit exceeded: {limit} requests per {window_seconds} seconds. "
                    "Wait briefly or escalate to the platform operations team."
                )
            recent.append(now)
            self._request_counters[tool_name] = recent

    def simulate_latency(self, minimum: float = 0.02, maximum: float = 0.12) -> None:
        """Sleep briefly to emulate remote API latency without slowing tests too much."""
        time.sleep(self._rng.uniform(minimum, maximum))

    def maybe_timeout(self, probability: float, message: str) -> None:
        """Randomly raise a timeout to model flaky integrations."""
        if self._rng.random() < probability:
            raise ToolTimeoutError(message)

    def get_service_catalog(self) -> Dict[str, Any]:
        """Return the current mock service catalog as structured data."""
        services = [asdict(record) for record in self._services.values()]
        return {
            "generated_at": self._now(),
            "service_count": len(services),
            "services": services,
            "advisory": (
                "Telemetry quality varies by service. Ambiguous signals should trigger "
                "clarification requests, cross-checks, or human escalation."
            ),
        }

    def calculate_impact(self, service: Optional[str]) -> Dict[str, Any]:
        """Estimate impact for a single service or all affected services."""
        if service:
            normalized = self._normalize_service(service)
            if not normalized:
                raise ToolOperationalError(f"Unknown service '{service}'.")
            targets = [self._services[normalized]]
        else:
            targets = [record for record in self._services.values() if record.current_status != "healthy"]

        impacted = []
        total_hourly_risk = 0
        for record in sorted(targets, key=lambda item: item.revenue_loss_per_hour, reverse=True):
            total_hourly_risk += record.revenue_loss_per_hour
            impact_level = "critical" if "Tier-1" in record.tier else "high" if "Tier-2" in record.tier else "moderate"
            impacted.append(
                {
                    "service": record.name,
                    "status": record.current_status,
                    "telemetry_health": record.telemetry_health,
                    "customers": record.customers,
                    "revenue_loss_per_hour": record.revenue_loss_per_hour,
                    "rto_minutes": record.rto_minutes,
                    "rpo_minutes": record.rpo_minutes,
                    "regulatory_exposure": record.regulators,
                    "dependency_count": len(record.dependencies),
                    "impact_level": impact_level,
                }
            )

        return {
            "generated_at": self._now(),
            "services_analyzed": len(impacted),
            "total_hourly_revenue_at_risk": total_hourly_risk,
            "estimated_four_hour_exposure": total_hourly_risk * 4,
            "recommended_recovery_order": [item["service"] for item in impacted],
            "services": impacted,
        }

    def query_replication_lag(self, database: str) -> Dict[str, Any]:
        """Return mock database replication lag, including ambiguous outcomes."""
        normalized = database.strip().lower() if database else "primary-db"
        scenarios = {
            "primary-db": {
                "database": "Primary DB",
                "replication_lag_seconds": 780,
                "rpo_target_minutes": 10,
                "status": "breaching_rpo",
                "confidence": "medium",
                "notes": [
                    "Replica in us-west-2 is catching up after WAL archive backlog.",
                    "Latest confirmed durable checkpoint is 13 minutes old.",
                ],
            },
            "transaction-db": {
                "database": "Transaction DB",
                "replication_lag_seconds": 140,
                "rpo_target_minutes": 5,
                "status": "near_threshold",
                "confidence": "high",
                "notes": [
                    "Streaming replication healthy but queue depth elevated.",
                ],
            },
        }
        if normalized not in scenarios:
            return {
                "database": database or "unspecified",
                "status": "unknown",
                "confidence": "low",
                "notes": ["Database identifier not found in CMDB.", "Human DBA validation required."],
            }

        result = scenarios[normalized]
        if self._rng.random() < 0.28:
            result = {
                **result,
                "status": "ambiguous",
                "confidence": "low",
                "replication_lag_seconds": None,
                "notes": result["notes"] + ["Replica telemetry agent skipped two scrapes; metric may be stale."],
            }
        return result

    def parse_logs(self, query: str, lookback_minutes: int) -> Dict[str, Any]:
        """Return Datadog-style log query results with potential partial failures."""
        normalized = query.lower()
        if "ransomware" in normalized or "encrypt" in normalized:
            summary = {
                "query": query,
                "lookback_minutes": lookback_minutes,
                "status": "partial" if self._rng.random() < 0.35 else "ok",
                "matched_events": 1432,
                "error_rate": 0.74,
                "top_signals": [
                    "Unusual file rename burst on payment-processing nodes",
                    "Endpoint agent detected ransomware family: BlackCipher variant",
                    "Privilege escalation from svc-batch-transfer account",
                ],
                "host_samples": ["app-pay-03", "db-core-01", "worker-fraud-02"],
                "recommended_next_steps": [
                    "Isolate suspected hosts from east-west traffic",
                    "Validate backup immutability before restore",
                    "Engage security incident response lead",
                ],
            }
        elif "ddos" in normalized or "503" in normalized or "latency" in normalized:
            summary = {
                "query": query,
                "lookback_minutes": lookback_minutes,
                "status": "ok",
                "matched_events": 5820,
                "error_rate": 0.38,
                "top_signals": [
                    "ALB target saturation in us-east-1",
                    "Repeated WAF blocks from 4 autonomous system clusters",
                    "Core Banking API upstream 503 spike",
                ],
                "host_samples": ["alb-edge-1", "api-core-07", "api-core-12"],
                "recommended_next_steps": [
                    "Shift traffic to secondary region if data consistency permits",
                    "Coordinate with network provider on mitigation",
                    "Confirm fraud checks remain available during rate limiting",
                ],
            }
        else:
            summary = {
                "query": query,
                "lookback_minutes": lookback_minutes,
                "status": "ambiguous",
                "matched_events": 97,
                "error_rate": 0.09,
                "top_signals": [
                    "Mixed warning and error events with no single dominant failure domain",
                ],
                "host_samples": ["obs-proxy-01"],
                "recommended_next_steps": [
                    "Refine query by service, region, or error code",
                    "Cross-check metrics and traces before declaring root cause",
                ],
            }

        if summary["status"] == "partial":
            summary["warnings"] = [
                "One Datadog index shard timed out; counts may be underreported.",
                "Correlate with SIEM export before taking irreversible actions.",
            ]
        return summary

    def create_incident(self, title: str, severity: str, commander: str, service: Optional[str]) -> IncidentRecord:
        """Create a new mock incident record."""
        with self._lock:
            self._incident_counter += 1
            self._pd_counter += 1
            incident_id = f"INC-{self._incident_counter}"
            pagerduty_id = f"PD-{self._pd_counter}"
            incident = IncidentRecord(
                incident_id=incident_id,
                title=title,
                severity=severity.upper() if severity else "SEV-2",
                status="investigating",
                commander=commander or "Unassigned",
                created_at=self._now(),
                service=service,
                pagerduty_id=pagerduty_id,
                notes=["Incident opened via mock PagerDuty integration."],
            )
            self._incidents[incident_id] = incident
            return incident

    def escalate_incident(self, incident_id: str, target_team: str, reason: str) -> IncidentRecord:
        """Escalate an existing incident to the next mock support level."""
        with self._lock:
            incident = self._incidents.get(incident_id)
            if not incident:
                raise ToolOperationalError(f"Incident '{incident_id}' not found.")
            incident.escalation_level += 1
            incident.status = "escalated"
            incident.notes.append(f"Escalated to {target_team}: {reason}")
            return incident

    def create_or_update_jira(
        self,
        summary: str,
        description: str,
        incident_id: Optional[str],
        action: Literal["create", "update"],
        ticket: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create or update a mock Jira issue and link it to an incident if provided."""
        with self._lock:
            if action == "create":
                self._jira_counter += 1
                ticket_key = f"BCM-{self._jira_counter}"
            else:
                if not ticket:
                    raise ToolOperationalError("A ticket key is required for Jira updates.")
                ticket_key = ticket

            payload = {
                "ticket": ticket_key,
                "summary": summary,
                "description": description,
                "status": "OPEN" if action == "create" else "UPDATED",
                "updated_at": self._now(),
                "linked_incident": incident_id,
            }

            if incident_id:
                incident = self._incidents.get(incident_id)
                if incident:
                    incident.jira_ticket = ticket_key
                    incident.notes.append(f"Jira {action}: {ticket_key}")
            return payload

    def notify(
        self,
        audience: str,
        message: str,
        incident_id: Optional[str],
    ) -> NotificationReceipt:
        """Create a stakeholder notification receipt with realistic delivery spread."""
        audience_normalized = audience.lower().strip()
        delivery_profiles = {
            "customers": ("SMS + In-App Banner", 840_000, 120_000, 40_000),
            "executives": ("Email + Slack", 12, 1, 0),
            "regulators": ("Secure Portal + Email", 3, 1, 0),
            "employees": ("Slack + Email", 5_400, 300, 16),
        }
        channel, delivered, pending, failed = delivery_profiles.get(
            audience_normalized,
            ("Email", 50, 5, 1),
        )
        if self._rng.random() < 0.2:
            pending += max(1, pending // 2)
            failed += 1

        with self._lock:
            receipt_id = f"NTF-{self._receipt_counter:04d}"
            self._receipt_counter += 1
            receipt = NotificationReceipt(
                receipt_id=receipt_id,
                audience=audience,
                channel=channel,
                status="partial" if pending or failed else "delivered",
                delivered=delivered,
                pending=pending,
                failed=failed,
                message_preview=message[:180],
                incident_id=incident_id,
                created_at=self._now(),
            )
            self._notifications[receipt_id] = receipt
            return receipt

    def failover_service(self, service: str, target_region: str) -> Dict[str, Any]:
        """Simulate a failover attempt with dependency and telemetry caveats."""
        normalized = self._normalize_service(service)
        if not normalized:
            raise ToolOperationalError(f"Unknown service '{service}'.")
        record = self._services[normalized]
        dependency_gate = any(dep in {"Primary DB", "Transaction DB"} for dep in record.dependencies)
        restored = not dependency_gate or self._rng.random() > 0.3
        record.current_status = "recovering" if restored else "degraded"
        return {
            "service": record.name,
            "target_region": target_region,
            "status": "online" if restored else "degraded",
            "rto_target_minutes": record.rto_minutes,
            "rpo_target_minutes": record.rpo_minutes,
            "verification": {
                "synthetic_check": "pass" if restored else "inconclusive",
                "customer_journey_check": "pass" if restored else "partial",
                "telemetry_health": record.telemetry_health,
            },
            "warnings": (
                []
                if restored
                else [
                    "Dependent database consistency not yet confirmed.",
                    "Bounded failover completed, but human review is required before customer all-clear.",
                ]
            ),
        }

    def log_lesson(self, lesson: str) -> Dict[str, Any]:
        """Persist a mock lesson-learned entry."""
        entry = {
            "logged_at": self._now(),
            "lesson": lesson,
            "tags": ["postmortem", "feedback-loop", "resilience", "human-in-the-loop"],
            "status": "saved",
        }
        with self._lock:
            self._knowledge_entries.append(entry)
        return entry


_ENVIRONMENT = MockBCMEnvironment()


class StatefulMockTool(BaseTool):
    """Common base class for all stateful mock tools."""

    rate_limit_requests: int = 6
    rate_limit_window_seconds: int = 10
    timeout_probability: float = 0.0
    latency_min_seconds: float = 0.02
    latency_max_seconds: float = 0.12

    def _prepare_call(self) -> None:
        """Apply standard rate limiting, latency, and timeout simulation."""
        _ENVIRONMENT.rate_limit(self.name, self.rate_limit_requests, self.rate_limit_window_seconds)
        _ENVIRONMENT.simulate_latency(self.latency_min_seconds, self.latency_max_seconds)
        if self.timeout_probability > 0:
            _ENVIRONMENT.maybe_timeout(
                self.timeout_probability,
                f"{self.name} upstream request timed out. Retry with narrower scope or escalate to a human operator.",
            )

    @staticmethod
    def _serialize(payload: Dict[str, Any]) -> str:
        """Serialize structured tool results as indented JSON strings."""
        return json.dumps(payload, indent=2, sort_keys=True)

    @staticmethod
    def _error_payload(
        error_type: str,
        message: str,
        remediation: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create consistent structured error responses for LLM consumption."""
        payload: Dict[str, Any] = {
            "status": "error",
            "error_type": error_type,
            "message": message,
            "remediation": remediation,
        }
        if details:
            payload["details"] = details
        return StatefulMockTool._serialize(payload)


class ServiceCatalogTool(StatefulMockTool):
    """Return the FinServe service catalog with current telemetry caveats."""

    name: str = "get_service_catalog"
    description: str = (
        "Fetch the current FinServe Digital Bank service catalog including tiers, "
        "RTO/RPO, dependencies, customer counts, regulators, current status, and "
        "telemetry quality."
    )
    rate_limit_requests: int = 8
    rate_limit_window_seconds: int = 10

    def _run(self, **_: Any) -> str:
        try:
            self._prepare_call()
            return self._serialize({"status": "ok", **_ENVIRONMENT.get_service_catalog()})
        except ToolOperationalError as exc:
            return self._error_payload(
                "catalog_unavailable",
                str(exc),
                "Retry shortly. If the outage persists, fall back to the documented BIA workbook.",
            )


class ImpactTool(StatefulMockTool):
    """Calculate business and regulatory impact for one or more services."""

    name: str = "calculate_impact"
    description: str = (
        "Estimate customer, revenue, dependency, and regulatory impact for a named "
        "service or for all non-healthy services if no service is provided."
    )
    timeout_probability: float = 0.08

    def _run(self, service: str = "", **_: Any) -> str:
        try:
            self._prepare_call()
            if service and random.random() < 0.12:
                raise ToolPartialFailureError(
                    "Finance exposure feed returned cached values older than 20 minutes."
                )
            payload = {"status": "ok", **_ENVIRONMENT.calculate_impact(service or None)}
            return self._serialize(payload)
        except ToolPartialFailureError as exc:
            return self._error_payload(
                "partial_finance_data",
                str(exc),
                "Use the returned order of magnitude carefully and request finance validation before executive sign-off.",
                {"service": service or "all_impacted_services"},
            )
        except ToolOperationalError as exc:
            return self._error_payload(
                "impact_lookup_failed",
                str(exc),
                "Verify the service name against the catalog or broaden the assessment to all affected services.",
            )


class DatabaseReplicationLagTool(StatefulMockTool):
    """Inspect mock database replication lag and RPO exposure."""

    name: str = "query_database_replication_lag"
    description: str = (
        "Query replication lag for a named database such as Primary-DB or "
        "Transaction-DB, returning lag, confidence, RPO comparison, and telemetry warnings."
    )
    timeout_probability: float = 0.1

    def _run(self, database: str = "Primary-DB", **_: Any) -> str:
        try:
            self._prepare_call()
            payload = {"status": "ok", **_ENVIRONMENT.query_replication_lag(database)}
            return self._serialize(payload)
        except ToolOperationalError as exc:
            return self._error_payload(
                "replication_query_failed",
                str(exc),
                "Retry once with the exact CMDB database name, then escalate to the DBA on-call.",
            )


class LogSearchTool(StatefulMockTool):
    """Perform Datadog-style log analysis with degraded index behavior."""

    name: str = "parse_observability_logs"
    description: str = (
        "Run a Datadog-style log search over a recent time window. Useful for "
        "detecting ransomware indicators, DDoS patterns, error spikes, and ambiguous telemetry."
    )
    rate_limit_requests: int = 5
    timeout_probability: float = 0.12

    def _run(self, query: str = "", lookback_minutes: int = 15, **_: Any) -> str:
        try:
            self._prepare_call()
            payload = {"status": "ok", **_ENVIRONMENT.parse_logs(query, lookback_minutes)}
            return self._serialize(payload)
        except ToolOperationalError as exc:
            return self._error_payload(
                "log_query_failed",
                str(exc),
                "Retry with a narrower query or consult backup SIEM telemetry.",
            )


class PagerDutyIncidentTool(StatefulMockTool):
    """Create a mock PagerDuty incident record."""

    name: str = "create_pagerduty_incident"
    description: str = (
        "Create a PagerDuty-style incident with severity, incident commander, "
        "affected service, and a generated incident identifier."
    )
    rate_limit_requests: int = 4
    timeout_probability: float = 0.05

    def _run(
        self,
        title: str = "",
        severity: str = "SEV-2",
        commander: str = "Lead Incident Commander",
        service: str = "",
        **_: Any,
    ) -> str:
        try:
            self._prepare_call()
            if not title.strip():
                raise ToolOperationalError("Incident title is required.")
            incident = _ENVIRONMENT.create_incident(title, severity, commander, service or None)
            return self._serialize({"status": "ok", "incident": asdict(incident)})
        except ToolOperationalError as exc:
            return self._error_payload(
                "incident_creation_failed",
                str(exc),
                "Provide a concise incident title and validated severity, then retry.",
            )


class PagerDutyEscalationTool(StatefulMockTool):
    """Escalate an existing mock PagerDuty incident."""

    name: str = "escalate_pagerduty_incident"
    description: str = (
        "Escalate an existing PagerDuty incident to another team, supplier, or "
        "human decision-maker, recording rationale and updated escalation level."
    )
    rate_limit_requests: int = 5
    timeout_probability: float = 0.04

    def _run(self, incident_id: str = "", target_team: str = "", reason: str = "", **_: Any) -> str:
        try:
            self._prepare_call()
            if not incident_id.strip():
                raise ToolOperationalError("incident_id is required for escalation.")
            incident = _ENVIRONMENT.escalate_incident(
                incident_id=incident_id,
                target_team=target_team or "Human Operations Bridge",
                reason=reason or "Additional expertise required due to ambiguous telemetry.",
            )
            return self._serialize({"status": "ok", "incident": asdict(incident)})
        except ToolOperationalError as exc:
            return self._error_payload(
                "incident_escalation_failed",
                str(exc),
                "Verify the incident ID and include a clear reason for escalation.",
            )


class JiraTicketTool(StatefulMockTool):
    """Create or update a mock Jira ticket linked to incident response work."""

    name: str = "manage_jira_ticket"
    description: str = (
        "Create or update a Jira issue for BCM or recovery workstreams, optionally "
        "linking it to a PagerDuty incident."
    )
    rate_limit_requests: int = 6
    timeout_probability: float = 0.06

    def _run(
        self,
        summary: str = "",
        description: str = "",
        incident_id: str = "",
        action: str = "create",
        ticket: str = "",
        **_: Any,
    ) -> str:
        try:
            self._prepare_call()
            normalized_action = action.lower().strip() or "create"
            if normalized_action not in {"create", "update"}:
                raise ToolOperationalError("action must be either 'create' or 'update'.")
            if not summary.strip():
                raise ToolOperationalError("summary is required.")
            payload = _ENVIRONMENT.create_or_update_jira(
                summary=summary,
                description=description,
                incident_id=incident_id or None,
                action=normalized_action,  # type: ignore[arg-type]
                ticket=ticket or None,
            )
            return self._serialize({"status": "ok", **payload})
        except ToolOperationalError as exc:
            return self._error_payload(
                "jira_operation_failed",
                str(exc),
                "Supply a valid action and summary. For updates, include the existing ticket key.",
            )


class NotificationTool(StatefulMockTool):
    """Send stakeholder notifications and return delivery tracking status."""

    name: str = "send_notification"
    description: str = (
        "Send a stakeholder communication to customers, executives, regulators, "
        "employees, or another audience and return delivery tracking statistics."
    )
    rate_limit_requests: int = 7
    timeout_probability: float = 0.07

    def _run(self, message: str = "", audience: str = "", incident_id: str = "", **_: Any) -> str:
        try:
            self._prepare_call()
            if not message.strip():
                raise ToolOperationalError("message is required.")
            if not audience.strip():
                raise ToolOperationalError("audience is required.")
            receipt = _ENVIRONMENT.notify(audience, message, incident_id or None)
            return self._serialize({"status": "ok", "receipt": asdict(receipt)})
        except ToolOperationalError as exc:
            return self._error_payload(
                "notification_failed",
                str(exc),
                "Validate the audience and message. If delivery remains partial, escalate through alternate channels.",
            )


class FailoverTool(StatefulMockTool):
    """Trigger mock service failover with dependency-aware caveats."""

    name: str = "failover_service"
    description: str = (
        "Attempt failover of a named service to a target region and return recovery "
        "verification details, warnings, and whether human validation is still required."
    )
    rate_limit_requests: int = 4
    timeout_probability: float = 0.09
    latency_min_seconds: float = 0.04
    latency_max_seconds: float = 0.16

    def _run(self, service: str = "", target_region: str = "us-west-2", **_: Any) -> str:
        try:
            self._prepare_call()
            if not service.strip():
                raise ToolOperationalError("service is required.")
            payload = {"status": "ok", **_ENVIRONMENT.failover_service(service, target_region)}
            return self._serialize(payload)
        except ToolOperationalError as exc:
            return self._error_payload(
                "failover_failed",
                str(exc),
                "Confirm the service name, validate data consistency, and involve human approval before retriggering.",
            )


class LogLessonTool(StatefulMockTool):
    """Persist lessons learned for later post-incident review."""

    name: str = "log_lesson"
    description: str = (
        "Record a lesson learned, improvement action, or control gap in the mock "
        "knowledge base for future retrospectives."
    )

    def _run(self, lesson: str = "", **_: Any) -> str:
        try:
            self._prepare_call()
            if not lesson.strip():
                raise ToolOperationalError("lesson is required.")
            return self._serialize({"status": "ok", **_ENVIRONMENT.log_lesson(lesson)})
        except ToolOperationalError as exc:
            return self._error_payload(
                "lesson_log_failed",
                str(exc),
                "Provide a concise retrospective statement that can be actioned later.",
            )


get_service_catalog = ServiceCatalogTool()
calculate_impact = ImpactTool()
query_database_replication_lag = DatabaseReplicationLagTool()
parse_observability_logs = LogSearchTool()
create_pagerduty_incident = PagerDutyIncidentTool()
escalate_pagerduty_incident = PagerDutyEscalationTool()
manage_jira_ticket = JiraTicketTool()
failover_service = FailoverTool()
send_notification = NotificationTool()
log_lesson = LogLessonTool()

__all__ = [
    "ToolOperationalError",
    "ToolRateLimitError",
    "ToolTimeoutError",
    "ToolPartialFailureError",
    "ServiceCatalogTool",
    "ImpactTool",
    "DatabaseReplicationLagTool",
    "LogSearchTool",
    "PagerDutyIncidentTool",
    "PagerDutyEscalationTool",
    "JiraTicketTool",
    "FailoverTool",
    "NotificationTool",
    "LogLessonTool",
    "get_service_catalog",
    "calculate_impact",
    "query_database_replication_lag",
    "parse_observability_logs",
    "create_pagerduty_incident",
    "escalate_pagerduty_incident",
    "manage_jira_ticket",
    "failover_service",
    "send_notification",
    "log_lesson",
]