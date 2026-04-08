import os
from dotenv import load_dotenv
load_dotenv()
key = os.environ.get("GEMINI_API_KEY", "NOT SET")
print(f"Key starts with: {key[:10]}... length: {len(key)}")

from src.bcm_crew import create_bcm_crew
from simulation_engine import SimulationEngine


# INSTRUCTOR: Change this before each live round
EVENT_SCENARIO = "ransomware"  # or "cloud_outage_ddos"

EVENTS = {
    "ransomware": "A ransomware attack has encrypted the primary data center. Mobile banking and transfers are down. No data exfiltrated yet.",
    "cloud_outage_ddos": "AWS us-east-1 is experiencing a major outage + simultaneous DDoS. All services degraded."
}

event_description = EVENTS[EVENT_SCENARIO]

print(f"🚨 INSTRUCTOR TRIGGERED EVENT: {EVENT_SCENARIO.upper()}")
print(f"Description: {event_description}\n")

crew = create_bcm_crew()
result = crew.kickoff(inputs={"event_description": event_description})

print("\n" + "="*80)
print("FINAL RECOVERY PLAN FROM STUDENT AGENTS:")
print(result)
print("="*80)

# Auto-grade
engine = SimulationEngine()
score = engine.evaluate(result, EVENT_SCENARIO)
print(f"\n🎯 OVERALL KPI SCORE: {score['overall_kpi_score']}%")