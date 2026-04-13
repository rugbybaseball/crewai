"""Task factory definitions for the FinServe BCM simulation."""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from crewai import Task


def _structured_output_instructions(stage_name: str, required_keys: Sequence[str]) -> str:
    """Build consistent JSON-style output guidance for a task."""
    key_list = ", ".join(required_keys)
    return (
        f"Return a single valid JSON object for the {stage_name} stage. "
        f"Do not wrap the JSON in markdown fences. "
        f"Include at minimum these top-level keys: {key_list}. "
        "When telemetry is incomplete or contradictory, explicitly capture uncertainty, "
        "bounded assumptions, and whether human escalation is required."
    )


def create_incident_tasks(agents: Sequence[Any]) -> List[Task]:
    """Create the ordered BCM lifecycle tasks for the crew.

    Args:
        agents: Sequence of initialized CrewAI agents in lifecycle order.

    Returns:
        A list of Task instances ordered for sequential execution.

    Raises:
        ValueError: If fewer than four agents are provided.
    """
    if len(agents) < 4:
        raise ValueError("create_incident_tasks requires four agents in lifecycle order.")

    triage_task = Task(
        description=(
            "You are handling a FinServe Digital Bank business continuity incident.\n\n"
            "EVENT SCENARIO: {event_description}\n\n"
            "Stage 1: triage and incident command initialization.\n"
            "Use available tooling to identify impacted services, ambiguous telemetry, likely blast radius, "
            "and whether immediate human escalation is needed.\n"
            "Apply a severity matrix grounded in customer impact, regulatory exposure, and operational degradation.\n"
            "Open or reference the incident record and declare the command posture.\n\n"
            "Your output must include:\n"
            "- incident_id\n"
            "- event_summary\n"
            "- affected_services\n"
            "- suspected_root_cause\n"
            "- severity_classification\n"
            "- confidence_level\n"
            "- ambiguous_signals\n"
            "- assumptions\n"
            "- human_escalations\n"
            "- immediate_actions\n"
            "- evidence\n"
            "- bcm_activation_decision\n\n"
            + _structured_output_instructions(
                "triage",
                [
                    "incident_id",
                    "stage",
                    "event_summary",
                    "affected_services",
                    "severity_classification",
                    "ambiguous_signals",
                    "human_escalations",
                    "immediate_actions",
                    "evidence",
                    "bcm_activation_decision",
                ],
            )
        ),
        agent=agents[0],
        expected_output=(
            "A valid JSON object representing structured incident triage with severity, "
            "ambiguity handling, evidence, and escalation decisions."
        ),
    )

    diagnosis_task = Task(
        description=(
            "Stage 2: technical diagnosis and recovery prerequisites.\n"
            "Use the structured triage output as the source of truth.\n"
            "Validate dependencies, isolate probable failure domains, identify monitoring gaps, "
            "and propose the safest technical recovery options.\n"
            "Where telemetry is ambiguous, either request clarification, escalate to a human, "
            "or proceed with bounded assumptions.\n\n"
            "Your output must include:\n"
            "- incident_id\n"
            "- diagnosis_summary\n"
            "- confirmed_impacted_services\n"
            "- service_dependencies\n"
            "- telemetry_findings\n"
            "- telemetry_gaps\n"
            "- likely_failure_domains\n"
            "- recommended_recovery_preconditions\n"
            "- proposed_recovery_sequence\n"
            "- escalations\n"
            "- evidence\n\n"
            + _structured_output_instructions(
                "diagnosis",
                [
                    "incident_id",
                    "stage",
                    "diagnosis_summary",
                    "confirmed_impacted_services",
                    "service_dependencies",
                    "telemetry_findings",
                    "telemetry_gaps",
                    "proposed_recovery_sequence",
                    "escalations",
                    "evidence",
                ],
            )
        ),
        agent=agents[1],
        expected_output=(
            "A valid JSON object representing structured diagnosis, dependency analysis, telemetry ambiguity, "
            "and a technically credible recovery sequence."
        ),
        context=[triage_task],
    )

    business_assessment_task = Task(
        description=(
            "Stage 3: business impact and compliance assessment.\n"
            "Use the prior triage and diagnosis outputs.\n"
            "Quantify customer impact, revenue risk, regulatory obligations, and service-level objectives "
            "including RTO and RPO constraints. Validate whether the proposed recovery order aligns with "
            "business criticality and compliance exposure.\n\n"
            "Your output must include:\n"
            "- incident_id\n"
            "- business_impact_summary\n"
            "- service_impacts\n"
            "- total_customers_affected\n"
            "- estimated_hourly_revenue_at_risk\n"
            "- regulatory_obligations\n"
            "- compliance_risks\n"
            "- rto_rpo_requirements\n"
            "- approved_recovery_priorities\n"
            "- required_executive_or_regulatory_escalations\n"
            "- evidence\n\n"
            + _structured_output_instructions(
                "business_assessment",
                [
                    "incident_id",
                    "stage",
                    "business_impact_summary",
                    "service_impacts",
                    "estimated_hourly_revenue_at_risk",
                    "regulatory_obligations",
                    "rto_rpo_requirements",
                    "approved_recovery_priorities",
                    "required_executive_or_regulatory_escalations",
                    "evidence",
                ],
            )
        ),
        agent=agents[2],
        expected_output=(
            "A valid JSON object representing business impact, compliance exposure, "
            "RTO/RPO analysis, and approved recovery priorities."
        ),
        context=[triage_task, diagnosis_task],
    )

    recovery_coordination_task = Task(
        description=(
            "Stage 4: recovery coordination.\n"
            "Use the technical diagnosis and business/compliance assessment outputs.\n"
            "Coordinate recovery in dependency-aware order, confirm preconditions, note any failover decisions, "
            "and track whether RTO and RPO remain achievable. If ambiguity prevents safe action, escalate instead of guessing.\n\n"
            "Your output must include:\n"
            "- incident_id\n"
            "- recovery_strategy\n"
            "- dependency_aware_recovery_sequence\n"
            "- recovery_actions\n"
            "- verification_checks\n"
            "- rto_status\n"
            "- rpo_status\n"
            "- blockers\n"
            "- escalations\n"
            "- lessons_logged\n"
            "- evidence\n\n"
            + _structured_output_instructions(
                "recovery_coordination",
                [
                    "incident_id",
                    "stage",
                    "recovery_strategy",
                    "dependency_aware_recovery_sequence",
                    "recovery_actions",
                    "verification_checks",
                    "rto_status",
                    "rpo_status",
                    "blockers",
                    "escalations",
                    "lessons_logged",
                    "evidence",
                ],
            )
        ),
        agent=agents[1],
        expected_output=(
            "A valid JSON object representing dependency-aware recovery coordination with "
            "verification, escalation handling, and RTO/RPO status."
        ),
        context=[triage_task, diagnosis_task, business_assessment_task],
    )

    communications_task = Task(
        description=(
            "Stage 5: stakeholder communications.\n"
            "Use all prior structured outputs to craft communications for customers, executives, and regulators.\n"
            "Messages must be truthful, audience-appropriate, and aligned with the current recovery status. "
            "If certainty is low, say so clearly. Confirm delivery tracking and follow-up commitments.\n\n"
            "Your output must include:\n"
            "- incident_id\n"
            "- overall_status_summary\n"
            "- communications\n"
            "- delivery_tracking\n"
            "- next_update_commitments\n"
            "- open_risks\n\n"
            "The communications field must contain nested objects for exactly these audiences:\n"
            "- customer_notification\n"
            "- executive_briefing\n"
            "- regulator_update\n\n"
            + _structured_output_instructions(
                "stakeholder_communications",
                [
                    "incident_id",
                    "stage",
                    "overall_status_summary",
                    "communications",
                    "delivery_tracking",
                    "next_update_commitments",
                    "open_risks",
                ],
            )
        ),
        agent=agents[3],
        expected_output=(
            "A valid JSON object representing delivered stakeholder communications, "
            "delivery tracking, follow-up commitments, and disclosed risks."
        ),
        context=[triage_task, diagnosis_task, business_assessment_task, recovery_coordination_task],
    )

    return [
        triage_task,
        diagnosis_task,
        business_assessment_task,
        recovery_coordination_task,
        communications_task,
    ]


def build_incident_task_payload(agents: Sequence[Any]) -> Dict[str, Task]:
    """Return named task objects for callers needing explicit stage access."""
    tasks = create_incident_tasks(agents)
    return {
        "triage": tasks[0],
        "diagnosis": tasks[1],
        "business_assessment": tasks[2],
        "recovery_coordination": tasks[3],
        "stakeholder_communications": tasks[4],
    }