import os
from crewai import Agent, LLM
from src.tools import get_service_catalog, calculate_impact, failover_service, send_notification, log_lesson

gemini_llm = LLM(
    model="gemini/gemini-2.5-flash",
    api_key=os.environ.get("GEMINI_API_KEY")
)


def create_agents():
    detection_agent = Agent(
        role="Vigilant Monitoring Specialist",
        goal="Detect disruption within 60 seconds, classify severity, and invoke BCM per ITIL Service Continuity Management",
        backstory="You are FinServe's always-on guardian. You embody ITIL 'Think and Work Holistically' and 'Progress Iteratively with Feedback'.",
        tools=[get_service_catalog],
        verbose=True,
        llm=gemini_llm,
        allow_delegation=False
    )

    impact_agent = Agent(
        role="Holistic Risk Analyst",
        goal="Calculate exact RTO/RPO impact, prioritize services, and align to business value (ITIL Guiding Principle: Focus on Value)",
        backstory="You translate outages into regulatory, customer, and financial risk using the full Service Value System.",
        tools=[calculate_impact],
        llm=gemini_llm,
        verbose=True
    )

    recovery_agent = Agent(
        role="DevOps Recovery Engineer",
        goal="Orchestrate automated recovery using DevOps Three Ways (Flow, Feedback, Continual Learning) and CALMS automation",
        backstory="You live by the Three Ways. You optimize flow with automation, close feedback loops instantly, and capture lessons for improvement.",
        tools=[failover_service, log_lesson],
        llm=gemini_llm,
        verbose=True
    )

    comms_agent = Agent(
        role="Transparent Communicator",
        goal="Deliver calm, clear, timely updates to all stakeholders per ITIL 'Collaborate and Promote Visibility'",
        backstory="You ensure every message builds trust and meets regulatory requirements.",
        tools=[send_notification],
        llm=gemini_llm,
        verbose=True
    )

    return [detection_agent, impact_agent, recovery_agent, comms_agent]