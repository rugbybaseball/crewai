"""Typed domain models for the FinServe BCM simulation."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


SeverityLevel = Literal["SEV-1", "SEV-2", "SEV-3"]
ConfidenceLevel = Literal["high", "medium", "low"]
TelemetryHealth = Literal["healthy", "degraded", "ambiguous"]


class EvidenceItem(BaseModel):
    """Evidence collected during triage, diagnosis, recovery, or communications."""

    source: str = Field(..., description="Tool, system, or human source of the evidence.")
    summary: str = Field(..., description="Short description of the observed fact or output.")
    timestamp: Optional[str] = Field(
        default=None,
        description="ISO-8601 timestamp if the evidence source provides one.",
    )
    confidence: ConfidenceLevel = Field(
        default="medium",
        description="Confidence assigned to the evidence item.",
    )


class HumanEscalationRequest(BaseModel):
    """Represents a human-in-the-loop escalation requirement."""

    target_role: str = Field(..., description="Human stakeholder or team to engage.")
    reason: str = Field(..., description="Why automated handling is insufficient.")
    decision_required: str = Field(..., description="Decision or approval needed from the human.")
    urgency: SeverityLevel = Field(..., description="Escalation urgency tied to severity policy.")


class RecoveryConstraint(BaseModel):
    """RTO/RPO and dependency constraints for a service."""

    service: str = Field(..., description="Service name.")
    rto_minutes: int = Field(..., ge=0, description="Recovery Time Objective in minutes.")
    rpo_minutes: int = Field(..., ge=0, description="Recovery Point Objective in minutes.")
    dependencies: List[str] = Field(
        default_factory=list,
        description="Upstream or downstream dependencies relevant to recovery ordering.",
    )


class ServiceImpact(BaseModel):
    """Structured business and technical impact for a service."""

    service: str
    status: str
    customers_affected: int = Field(..., ge=0)
    revenue_loss_per_hour: int = Field(..., ge=0)
    telemetry_health: TelemetryHealth
    regulators: List[str] = Field(default_factory=list)
    impact_level: str
    recovery_constraint: Optional[RecoveryConstraint] = None


class IncidentSnapshot(BaseModel):
    """Normalized incident representation shared across lifecycle stages."""

    incident_id: str
    stage: str
    event_summary: str
    severity_classification: SeverityLevel
    confidence_level: ConfidenceLevel
    affected_services: List[str] = Field(default_factory=list)
    ambiguous_signals: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    human_escalations: List[HumanEscalationRequest] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional stage-specific structured fields.",
    )
