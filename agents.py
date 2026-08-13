import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
from dotenv import load_dotenv

load_dotenv()

# Tool: Web search (get free key at serper.dev)
search_tool = SerperDevTool()

# ─── AGENT 1: The Researcher ─────────────────────────────
researcher = Agent(
    role="Tourism Research Specialist",
    goal="Find the best attractions, restaurants, and hidden gems for a destination",
    backstory="You are a seasoned travel blogger with 10 years of experience. "
              "You know every hidden spot and tourist trap. You prioritize authentic experiences.",
    tools=[search_tool],
    verbose=True,
    allow_delegation=False
)

# ─── AGENT 2: The Itinerary Planner ──────────────────────
planner = Agent(
    role="Smart Itinerary Architect",
    goal="Create a day-by-day travel plan that maximizes experience and minimizes travel time",
    backstory="You are a logistics genius. You optimize routes, consider opening hours, "
              "group nearby attractions, and balance activity with rest.",
    verbose=True,
    allow_delegation=False
)

# ─── AGENT 3: The Budget Analyst ─────────────────────────
budget_analyst = Agent(
    role="Travel Budget Analyst",
    goal="Estimate realistic costs and ensure the plan stays within budget",
    backstory="You are a meticulous accountant who loves travel. You check current prices "
              "for food, transport, and activities. You warn about hidden costs.",
    tools=[search_tool],
    verbose=True,
    allow_delegation=False
)

# ─── TASKS ───────────────────────────────────────────────
research_task = Task(
    description="""
    Research {destination} for a {duration}-day trip.
    The traveler likes: {preferences}.
    Find:
    1. Top 10 must-see attractions (mix famous + hidden gems)
    2. 5 highly-rated local restaurants
    3. Local transport options
    4. Any current events or seasonal considerations
    
    Return a structured list with names, brief descriptions, and why each is worth visiting.
    """,
    expected_output="A structured markdown list of attractions, restaurants, and transport options.",
    agent=researcher
)

planning_task = Task(
    description="""
    Using the research provided, create a detailed day-by-day itinerary for {duration} days in {destination}.
    
    Rules:
    - Group nearby attractions on the same day
    - Consider opening hours (don't schedule museums on Mondays if they close)
    - Include meal times at the researched restaurants
    - Add 1-2 hours of buffer time each day
    - Start days at 9 AM, end by 9 PM
    
    Format as:
    Day 1:
    - 09:00: Activity (location)
    - 12:30: Lunch at Restaurant
    etc.
    """,
    expected_output="A detailed markdown itinerary with times and locations.",
    agent=planner,
    context=[research_task]  # Waits for research to finish
)

budget_task = Task(
    description="""
    Review the itinerary and estimate costs in {currency}.
    
    Break down:
    - Accommodation (per night estimate)
    - Food (per meal estimate)
    - Transport (local + between attractions)
    - Activities/entrance fees
    - Emergency buffer (10%)
    
    Compare against the total budget of {budget} {currency}.
    If over budget, suggest specific downgrades. If under, suggest upgrades.
    """,
    expected_output="A markdown budget breakdown with final verdict (over/under budget).",
    agent=budget_analyst,
    context=[planning_task]
)

# ─── CREW (Orchestrator) ─────────────────────────────────
crew = Crew(
    agents=[researcher, planner, budget_analyst],
    tasks=[research_task, planning_task, budget_task],
    process=Process.sequential,  # Research → Plan → Budget
    verbose=True
)

def run_trip_planner(destination, duration, budget, currency, preferences):
    result = crew.kickoff(inputs={
        "destination": destination,
        "duration": duration,
        "budget": budget,
        "currency": currency,
        "preferences": preferences
    })
    return result

if __name__ == "__main__":
    # Test run
    result = run_trip_planner(
        destination="Lisbon, Portugal",
        duration=3,
        budget=800,
        currency="USD",
        preferences="seafood, vintage shops, walking tours, avoiding crowds"
    )
    print("\n" + "="*60)
    print("YOUR TRAVEL PLAN")
    print("="*60)
    print(result)