import os 
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import streamlit as st 

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
    provide realistic time-of-day breakdowns, estimated costs, and recommended total budget.
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TravelItinerary,
            temperature=0.7,
        )
    )
    return TravelItinerary.model_validate_json(response.text)

st.set_page_config(page_title="AI Travel Planner", page_icon="✈️", layout="wide")

st.title("✈️ AI-Powered Travel Planner")
st.write("Generate a structural travel itinerary in seconds!")

st.sidebar.header("Trip Controls")
destination = st.sidebar.text_input("Destination", "Goa")
days = st.sidebar.slider("Duration (Days)", min_value=1, max_value=14, value=3)
budget_style = st.sidebar.selectbox("Budget style", ["Budget", "Moderate", "Luxury"])

if st.sidebar.button("Generate Itinerary", type="primary"):
    with st.spinner("Asking Gemini to curate your plan..."):
        try:
            itinerary = generate_plan(destination, days, budget_style)

            usd_to_inr = 95.61
            total_inr = itinerary.recommended_budget_usd * usd_to_inr

            st.success(f"Itinerary created for **{itinerary.destination}**!")

            col1,  col2, col3 = st.columns(3)
            col1.metric("Trip Dates", f"{itinerary.start_date}- {itinerary.end_date}")
            col2.metric("Total Budget ($)", f"${itinerary.recommended_budget_usd:,.2f}")
            col3.metric("Total Budget (₹)", f"₹{total_inr:,.2f}")

            st.divider()

            for day in itinerary.daily_plans:
                with st.expander(f"📌 Day {day.day_number}: {day.summary}", expanded=True):
                    for act in day.activities:
                        act_inr = act.estimated_cost_usd * usd_to_inr
                        st.markdown(f"### **[{act.time_of_day}] {act.activity_name}**")
                        st.write(act.description)
                        st.caption(f"📍**Location:** {act.location} | 💰 **Cost:** ${act.estimated_cost_usd:.2f} (₹{act_inr:,.2f})")
                        st.write("---")
        except Exception as e:
            st.error(f"Error generating plan: {e}")
