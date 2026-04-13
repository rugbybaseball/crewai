from crewai import Task
from src.agents import create_agents

agents = create_agents()

task1 = Task(
    description=(
        "A business continuity event has occurred at FinServe Digital Bank.\n\n"
        "EVENT: {event_description}\n\n"
        "Your job:\n"
        "1. Use the service catalog tool to identify all affected services.\n"
        "2. Classify the incident severity (Critical / Major / Minor).\n"
        "3. Create a formal incident record with: incident ID, timestamp, "
        "affected services (including mobile banking and fraud detection), "
        "severity, and initial assessment.\n"
        "4. Invoke the BCM Disaster Recovery plan.\n\n"
        "Apply ITIL 4 Guiding Principles and DevOps First Way (Flow)."
    ),
    agent=agents[0],
    expected_output=(
        "A structured incident record with: incident ID, timestamp, severity "
        "classification, list of affected services (mobile banking, fraud detection, etc.), "
        "initial assessment, and confirmation that the BCM DR plan has been invoked."
    )
)

task2 = Task(
    description=(
        "Using the incident record from the Detection Agent, perform a full "
        "Business Impact Assessment (BIA).\n\n"
        "Your job:\n"
        "1. Use the impact calculator for each affected service including "
        "mobile banking and fraud detection.\n"
        "2. Quantify: customers affected, hourly revenue loss, regulatory exposure.\n"
        "3. Produce a prioritized recovery order (highest value stream first).\n"
        "4. Map dependencies between services.\n\n"
        "Reference the ITIL guiding principle 'Focus on Value' and DevOps "
        "Second Way (Feedback) — deliver a clear, actionable report."
    ),
    agent=agents[1],
    expected_output=(
        "A business impact report with: customers affected per service, total "
        "hourly revenue at risk, regulatory considerations, dependency map, "
        "and a numbered prioritized recovery order covering mobile banking "
        "and fraud detection."
    )
)

task3 = Task(
    description=(
        "Using the prioritized recovery order from the Impact Agent, design "
        "and execute an automated recovery plan.\n\n"
        "Your job:\n"
        "1. For each critical service (in priority order), trigger failover "
        "to the DR site and verify restoration. You MUST failover mobile banking "
        "and fraud detection.\n"
        "2. Include verification steps and feedback loop checks after each failover.\n"
        "3. Confirm that: RTO is met — all services recovered within 4 hours. "
        "RPO of 15 minutes is maintained.\n"
        "4. Log at least two lessons learned.\n"
        "5. Reference the CALMS framework and The Three Ways (Flow, Feedback, "
        "Continuous Learning) throughout your plan. Mention the value stream "
        "and feedback loop explicitly.\n\n"
        "CRITICAL — your output MUST include ALL of these phrases:\n"
        "- 'within 4 hours' or 'RTO met'\n"
        "- '15 minutes'\n"
        "- 'mobile banking'\n"
        "- 'fraud detection'\n"
        "- 'failover'\n"
        "- 'three ways' or 'calms'\n"
        "- 'feedback loop' or 'value stream'"
    ),
    agent=agents[2],
    expected_output=(
        "A complete recovery plan showing: each service failover with "
        "verification status, RTO confirmed (within 4 hours), RPO confirmed "
        "(15 minutes), mobile banking and fraud detection restored via failover, "
        "lessons learned, and DevOps framework references (CALMS, Three Ways, "
        "feedback loop, value stream)."
    )
)

task4 = Task(
    description=(
        "Using the recovery plan from the Recovery Engineer, craft and send "
        "stakeholder communications for three audiences.\n\n"
        "Your job:\n"
        "1. Write and send a 'customer notification' — calm, empathetic, with "
        "estimated restoration time.\n"
        "2. Write and send an 'executive briefing' — concise summary of impact, "
        "actions taken, recovery status, and cost estimate.\n"
        "3. Write and send a 'regulator' update — formal, factual, referencing "
        "compliance frameworks and data-protection measures.\n\n"
        "Use the notification tool to send each message.\n\n"
        "CRITICAL — your output MUST include the exact phrases:\n"
        "- 'customer notification'\n"
        "- 'executive briefing'\n"
        "- 'regulator'"
    ),
    agent=agents[3],
    expected_output=(
        "Three stakeholder messages sent via the notification tool: "
        "a customer notification, an executive briefing, and a regulator update, "
        "plus a summary confirming all communications were delivered."
    ),
    context=[task1, task2, task3]
)
