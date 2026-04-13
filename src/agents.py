"""Agent factory for the FinServe Digital Bank BCM simulation."""

from __future__ import annotations

import os
from typing import List

from crewai import Agent, LLM

from src.agent_policies import build_role_prompt
from src.tools import (
    calculate_impact,
    create_pagerduty_incident,
    escalate_pagerduty_incident,
    failover_service,
    get_service_catalog,
    log_lesson,
    manage_jira_ticket,
    parse_observability_logs,
    query_database_replication_lag,
    send_notification,
)


def _create_llm() -> LLM:
    """Create the default LLM configuration for BCM agents.

    Returns:
        Configured CrewAI LLM instance.

    Raises:
        ValueError: If no supported API key is available.
    """

    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    groq_api_key = os.environ.get("GROQ_API_KEY")

    if gemini_api_key:
        return LLM(model="gemini/gemini-2.5-flash", api_key=gemini_api_key)

    if groq_api_key:
        return LLM(model="groq/llama-3.1-70b-versatile", api_key=groq_api_key)

    raise ValueError("Missing GEMINI_API_KEY or GROQ_API_KEY for CrewAI agent initialization.")


def create_agents() -> List[Agent]:
    """Create the production-grade BCM agent set.

    Returns:
        List[Agent]: Agents ordered for incident lifecycle execution:
        Lead Incident Commander, Infrastructure SRE, Compliance Officer,
        Crisis Communications Lead.
    """

    llm = _create_llm()

    lead_incident_commander = Agent(
        role="Lead Incident Commander",
        goal=(
            "Establish incident command, classify severity using the formal matrix, "
            "coordinate cross-functional triage, enforce evidence quality, and decide "
            "when ambiguous telemetry requires clarification or human escalation."
        ),
        backstory=build_role_prompt(
            role_summary=(
                "You are the senior incident commander for FinServe Digital Bank, "
                "experienced in cyber response, major incident management, and BCM governance."
            ),
            responsibilities=(
                "- Open the incident record with an auditable summary.\n"
                "- Use service catalog evidence to identify blast radius and dependency risk.\n"
                "- Apply the severity matrix and justify the selected severity.\n"
                "- If telemetry is incomplete, contradictory, or stale, explicitly request clarification "
                "or escalate to a human executive sponsor/security lead.\n"
                "- Define the initial command objectives, decision log, and escalation path."
            ),
        ),
        tools=[
            get_service_catalog,
            parse_observability_logs,
            calculate_impact,
            create_pagerduty_incident,
            escalate_pagerduty_incident,
            manage_jira_ticket,
        ],
        verbose=True,
        llm=llm,
        allow_delegation=False,
    )

    infrastructure_sre = Agent(
        role="Infrastructure SRE",
        goal=(
            "Diagnose infrastructure failure modes, validate dependency-aware recovery steps, "
            "execute or recommend failover actions, and protect RTO/RPO commitments with evidence."
        ),
        backstory=build_role_prompt(
            role_summary=(
                "You are the principal Infrastructure SRE responsible for resilient service recovery, "
                "observability interpretation, and safe failover execution across critical banking platforms."
            ),
            responsibilities=(
                "- Analyze likely technical fault domains and dependencies.\n"
                "- Confirm whether available telemetry is sufficient for action.\n"
                "- Execute failover only when bounded by service-specific RTO/RPO constraints.\n"
                "- If telemetry is degraded or tooling errors occur, propose the next safe diagnostic step "
                "or escalate to human infrastructure leadership.\n"
                "- Capture verification evidence, residual risk, and lessons learned."
            ),
        ),
        tools=[
            get_service_catalog,
            parse_observability_logs,
            query_database_replication_lag,
            failover_service,
            manage_jira_ticket,
            log_lesson,
        ],
        verbose=True,
        llm=llm,
        allow_delegation=False,
    )

    compliance_officer = Agent(
        role="Compliance Officer",
        goal=(
            "Assess regulatory exposure, ensure evidence and decision trails are audit-ready, "
            "validate RTO/RPO and notification obligations, and escalate when legal or regulatory "
            "thresholds may be crossed."
        ),
        backstory=build_role_prompt(
            role_summary=(
                "You are the bank's Compliance Officer specializing in financial-services operational resilience, "
                "incident notification requirements, and defensible evidence handling."
            ),
            responsibilities=(
                "- Translate the incident into regulatory, fraud, privacy, and customer-impact obligations.\n"
                "- Review whether evidence supports severity and recovery assertions.\n"
                "- Call out any likely breaches of service recovery commitments or notifiable incident thresholds.\n"
                "- If facts are incomplete, require clarification and identify which legal/compliance stakeholders "
                "must be looped in.\n"
                "- Produce a concise compliance posture and approval constraints for communications and recovery."
            ),
        ),
        tools=[
            get_service_catalog,
            calculate_impact,
            query_database_replication_lag,
            manage_jira_ticket,
            escalate_pagerduty_incident,
        ],
        verbose=True,
        llm=llm,
        allow_delegation=False,
    )

    crisis_communications_lead = Agent(
        role="Crisis Communications Lead",
        goal=(
            "Deliver factual, audience-specific stakeholder communications that reflect confirmed status, "
            "known customer impact, recovery expectations, and any limits caused by ambiguous telemetry."
        ),
        backstory=build_role_prompt(
            role_summary=(
                "You lead crisis communications for FinServe Digital Bank and are accountable for timely, "
                "clear, and compliant updates to customers, executives, and regulators."
            ),
            responsibilities=(
                "- Draft customer, executive, and regulator communications with explicit audience labels.\n"
                "- Separate confirmed facts from assumptions or pending validation.\n"
                "- If legal/compliance approval or technical clarification is required, state that clearly.\n"
                "- Use delivery tooling and report message status, channel, and follow-up cadence.\n"
                "- Avoid overpromising restoration time when telemetry is ambiguous."
            ),
        ),
        tools=[send_notification, manage_jira_ticket, escalate_pagerduty_incident],
        verbose=True,
        llm=llm,
        allow_delegation=False,
    )

    return [
        lead_incident_commander,
        infrastructure_sre,
        compliance_officer,
        crisis_communications_lead,
    ]


__all__ = ["create_agents"]
