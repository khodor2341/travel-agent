import streamlit as st
from agents import run_trip_planner

st.set_page_config(page_title="TravelAgent AI", page_icon="✈️", layout="wide")

st.title("✈️ TravelAgent — AI-Powered Trip Planning")
st.markdown("Built with CrewAI • Multi-Agent System • Portfolio Project")

col1, col2 = st.columns(2)

with col1:
    destination = st.text_input("Where to?", "Lisbon, Portugal")
    duration = st.number_input("How many days?", min_value=1, max_value=14, value=3)
    budget = st.number_input("Budget?", min_value=100, value=800)

with col2:
    currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "JPY"])
    preferences = st.text_area("What do you love?", 
        "seafood, vintage shops, walking tours, avoiding crowds")

if st.button("🚀 Plan My Trip", type="primary", use_container_width=True):
    with st.spinner("Our agents are researching, planning, and budgeting..."):
        result = run_trip_planner(destination, duration, budget, currency, preferences)
    
    st.success("Trip planned!")
    st.markdown(result)
    
    st.download_button(
        label="📥 Download Itinerary",
        data=str(result),
        file_name=f"trip_to_{destination.replace(' ', '_')}.md",
        mime="text/markdown"
    )