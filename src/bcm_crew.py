from crewai import Crew, Process
from src.agents import create_agents
from src.tasks import task1, task2, task3, task4

def create_bcm_crew():
    agents = create_agents()
    return Crew(
        agents=agents,
        tasks=[task1, task2, task3, task4],
        process=Process.sequential,
        verbose=True,
        memory=False,
        cache=True
    )