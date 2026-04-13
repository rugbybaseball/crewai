"""Entry point for the FinServe BCM CrewAI simulation."""

from __future__ import annotations

import os

from dotenv import load_dotenv

from simulation_engine import SimulationEngine
from src.bcm_crew import create_bcm_crew

load_dotenv()


EVENT_SCENARIO = "ransomware"

EVENTS = {
    "ransomware": (
        "A ransomware attack has encrypted the primary data center. "
        "Mobile banking and transfers are down. No data exfiltrated yet."
    ),
    "cloud_outage_ddos": (
        "AWS us-east-1 is experiencing a major outage with simultaneous DDoS activity. "
        "Authentication, payments, and customer-facing channels are degraded."
    ),
}


def main() -> None:
    """Run the BCM simulation and print the evaluation summary."""
    key = os.environ.get("GEMINI_API_KEY", "NOT SET")
    print(f"Key starts with: {key[:10]}... length: {len(key)}")

    event_description = EVENTS[EVENT_SCENARIO]
    print(f"🚨 INSTRUCTOR TRIGGERED EVENT: {EVENT_SCENARIO.upper()}")
    print(f"Description: {event_description}\n")

    crew = create_bcm_crew()
    result = crew.kickoff(inputs={"event_description": event_description})

    print("\n" + "=" * 80)
    print("FINAL BCM LIFECYCLE OUTPUT FROM STUDENT AGENTS:")
    print(result)
    print("=" * 80)

    engine = SimulationEngine()
    score = engine.evaluate(str(result), EVENT_SCENARIO)
    print(f"\n🎯 OVERALL KPI SCORE: {score['overall_kpi_score']}%")


if __name__ == "__main__":
    main()