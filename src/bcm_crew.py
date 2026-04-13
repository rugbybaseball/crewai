"""Crew orchestration for the FinServe BCM simulation."""

from __future__ import annotations

from crewai import Crew, Process

from src.agents import create_agents
from src.tasks import create_incident_tasks


def create_bcm_crew() -> Crew:
    """Create the BCM crew with runtime task factories.

    Returns:
        A sequential CrewAI crew wired for the incident lifecycle.
    """
    agents = create_agents()
    tasks = create_incident_tasks(agents)
    return Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
        memory=False,
        cache=True,
    )