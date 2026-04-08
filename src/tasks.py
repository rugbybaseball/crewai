from crewai import Task
from src.agents import create_agents

agents = create_agents()

task1 = Task(
    description="Detect the event, classify severity (minor/major/catastrophic), and create the initial incident record. Event: {event_description}",
    agent=agents[0],
    expected_output="Clear severity classification + incident ID + immediate invocation of BCM plan"
)

task2 = Task(
    description="Perform full business impact assessment. Map every affected service to RTO/RPO, customer count, revenue loss, and regulatory risk. Prioritize recovery order.",
    agent=agents[1],
    expected_output="Prioritized recovery list with exact impact numbers and business justification"
)

task3 = Task(
    description="Build and execute the automated recovery plan using DevOps automation. Include failover steps, feedback loops, and estimated timestamps that meet the 4-hour RTO.",
    agent=agents[2],
    expected_output="Step-by-step numbered recovery plan with automation commands and verification steps"
)

task4 = Task(
    description="Generate and send all stakeholder communications (customers, executives, regulators). Keep messages calm, transparent, and actionable.",
    agent=agents[3],
    expected_output="Full set of ready-to-send messages with timestamps",
    context=[task1, task2, task3]
)