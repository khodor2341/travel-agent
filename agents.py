import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

def _call_groq(system_prompt, user_prompt):
    """Helper to call Groq API."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=4000
    )
    return response.choices[0].message.content

def run_trip_planner(destination, duration, budget, currency, preferences):
    # ─── AGENT 1: Researcher ─────────────────────────────
    research = _call_groq(
        system_prompt="You are a seasoned travel blogger with 10 years of experience. You know every hidden spot and tourist trap. You prioritize authentic experiences.",
        user_prompt=f"""
Research {destination} for a {duration}-day trip.
The traveler likes: {preferences}.
Find:
1. Top 10 must-see attractions (mix famous + hidden gems)
2. 5 highly-rated local restaurants
3. Local transport options
4. Any current events or seasonal considerations

Return a structured list with names, brief descriptions, and why each is worth visiting.
"""
    )

    # ─── AGENT 2: Planner ────────────────────────────────
    itinerary = _call_groq(
        system_prompt="You are a logistics genius. You optimize routes, consider opening hours, group nearby attractions, and balance activity with rest.",
        user_prompt=f"""
Using this research, create a detailed day-by-day itinerary for {duration} days in {destination}.

RESEARCH:
{research}

Rules:
- Group nearby attractions on the same day
- Consider opening hours
- Include meal times at the researched restaurants
- Add 1-2 hours of buffer time each day
- Start days at 9 AM, end by 9 PM

Format as:
Day 1:
- 09:00: Activity (location)
- 12:30: Lunch at Restaurant
etc.
"""
    )

    # ─── AGENT 3: Budget Analyst ─────────────────────────
    budget_analysis = _call_groq(
        system_prompt="You are a meticulous accountant who loves travel. You estimate realistic costs and warn about hidden costs.",
        user_prompt=f"""
Review this itinerary and estimate costs in {currency}.

ITINERARY:
{itinerary}

Break down:
- Accommodation (per night estimate)
- Food (per meal estimate)
- Transport (local + between attractions)
- Activities/entrance fees
- Emergency buffer (10%)

Compare against the total budget of {budget} {currency}.
If over budget, suggest specific downgrades. If under, suggest upgrades.
"""
    )

    # ─── Combine Results ─────────────────────────────────
    result = f"""
# 🌍 Travel Plan for {destination}

## 📍 Research & Attractions
{research}

---

## 📅 Day-by-Day Itinerary
{itinerary}

---

## 💰 Budget Analysis
{budget_analysis}

---
*Planned by TravelAgent AI — Multi-Agent System*
"""
    return result

if __name__ == "__main__":
    result = run_trip_planner(
        destination="Lisbon, Portugal",
        duration=3,
        budget=800,
        currency="USD",
        preferences="seafood, vintage shops, walking tours, avoiding crowds"
    )
    print(result)