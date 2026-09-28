import os
from dotenv import load_dotenv
from google import genai
from google.genai import types 
from pydantic import BaseModel, Field
load_dotenv()
class Activity(BaseModel):
    time_of_day: str = Field(description="Morning, Afternoon, or Evening")
    activity_name: str
    description: str
    location: str
    estimated_cost_usd: float

class DailyPlan(BaseModel):
    day_number: int
    summary: str
    activities: list[Activity]

class TravelItinerary(BaseModel):
    destination: str
    start_date: str
    end_date: str
    recommended_budget_usd: float = Field(description="Total estimated cost in USD for the entire trip")
    daily_plans: list[DailyPlan]

def generate_plan(destination: str, days: int, budget_style: str) -> TravelItinerary:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt = f"""
Create a detailed travel itinerary for {destination}.
Duration: {days} days.
Style: {budget_style}.
Provide realistic time-of-day breakdowns and estimated costs.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TravelItinerary,
            temperature=0.7,
        )
    )

    return TravelItinerary.model_validate_json(response.text)

if __name__ == "__main__":
    print("=== AI Travel Planner CLI ===")
    dest = input("Where do you want to go? ")
    days = int(input("How many days?"))
    budget = input("Budget style (e.g., Budget, Moderate, Luxury)?")

    print("\nGenerating your travel plan, please wait....\n")

    usd_to_inr_rate = 95.61

    try:
        itinerary = generate_plan(dest, days, budget)
        print(f"trip Destination: {itinerary.destination}")
        print(f"Total Estimated Budget: ${itinerary.recommended_budget_usd:.2f} (approx. ₹{total_budget_inr:,.2f} INR)\n")

        for day in itinerary.daily_plans:
            print(f"--- Day {day.day_number}: {day.summary} ---")
            for act in day.activities:
                act_cost_inr = act.estimated_cost_usd * usd_to_inr_rate
                print(f" •[{act.time_of_day}] {act.activity_name} -" f"${act.estimated_cost_usd:.2f} (₹{act_cost_inr:,.2f})")
                print(f" {act.description}")
                print(f" Location: {act.location}\n")
    except Exception as e:
        print(f"Error occurred: {e}")