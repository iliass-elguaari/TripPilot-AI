import re
from datetime import date, datetime, timedelta
from pathlib import Path
from textwrap import dedent

import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.run.agent import RunOutput
from agno.tools.serpapi import SerpApiTools
from icalendar import Calendar, Event

# A saved example from a real run (optional). If this file exists next to
# this script, the app shows a "View sample itinerary" button that needs no keys.
SAMPLE_FILE = Path(__file__).parent / "sample_itinerary.md"


# ---------------------------------------------------------------------------
# PART 1: Calendar export
# ---------------------------------------------------------------------------
def generate_ics_content(plan_text: str, start_date: date) -> bytes:
    """Turn the itinerary text into an .ics calendar file (one all-day event per day)."""
    cal = Calendar()
    cal.add('prodid', '-//TripPilot AI//github.com//')
    cal.add('version', '2.0')

    # Find "Day 1 ...", "Day 2 ..." in the AI's text
    day_pattern = re.compile(r'Day (\d+)[:\s]+(.*?)(?=Day \d+|$)', re.DOTALL)
    days = day_pattern.findall(plan_text)

    if not days:
        # Fallback: the AI didn't use "Day N" headings, so make one event with everything
        event = Event()
        event.add('summary', "Travel Itinerary")
        event.add('description', plan_text)
        event.add('dtstart', start_date)
        event.add('dtend', start_date + timedelta(days=1))
        event.add('dtstamp', datetime.now())
        cal.add_component(event)
    else:
        for day_num, day_content in days:
            current_date = start_date + timedelta(days=int(day_num) - 1)

            event = Event()
            event.add('summary', f"Day {day_num} Itinerary")
            event.add('description', day_content.strip())
            event.add('dtstart', current_date)
            # For all-day events, the end date is the NEXT day
            event.add('dtend', current_date + timedelta(days=1))
            event.add('dtstamp', datetime.now())
            cal.add_component(event)

    return cal.to_ical()


# ---------------------------------------------------------------------------
# PART 2: The two AI agents
# ---------------------------------------------------------------------------
def build_agents(openai_api_key: str, serp_api_key: str):
    """Create the researcher and the planner. Returns both: (researcher, planner)."""
    researcher = Agent(
        name="Researcher",
        role="Searches for travel destinations, activities, and accommodations based on user preferences",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        description=dedent(
            """\
        You are a world-class travel researcher. Given a travel destination and the number of days the user wants to travel for,
        generate a list of search terms for finding relevant travel activities and accommodations.
        Then search the web for each term, analyze the results, and return the 10 most relevant results.
        """
        ),
        instructions=[
            "Given a travel destination and the number of days the user wants to travel for, first generate a list of 3 search terms related to that destination and the number of days.",
            "For each search term, `search_google` and analyze the results.",
            "From the results of all searches, return the 10 most relevant results to the user's preferences.",
            "Remember: the quality of the results is important.",
        ],
        tools=[SerpApiTools(api_key=serp_api_key)],
        add_datetime_to_context=True,
    )

    planner = Agent(
        name="Planner",
        role="Generates a draft itinerary based on user preferences and research results",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        description=dedent(
            """\
        You are a senior travel planner. Given a travel destination, the number of days the user wants to travel for, and a list of research results,
        your goal is to generate a draft itinerary that meets the user's needs and preferences.
        """
        ),
        instructions=[
            "Given a travel destination, the number of days the user wants to travel for, and a list of research results, generate a draft itinerary that includes suggested activities and accommodations.",
            "Ensure the itinerary is well-structured, informative, and engaging.",
            "Ensure you provide a nuanced and balanced itinerary, quoting facts where possible.",
            "Remember: the quality of the itinerary is important.",
            "Focus on clarity, coherence, and overall quality.",
            "Never make up facts or plagiarize. Always provide proper attribution.",
        ],
        add_datetime_to_context=True,
    )

    return researcher, planner


# ---------------------------------------------------------------------------
# PART 3: The Streamlit screen
# ---------------------------------------------------------------------------
st.set_page_config(page_title="TripPilot AI", page_icon="✈️")

st.title("✈️ TripPilot AI")
st.caption("Research a destination and get a personalized day-by-day itinerary, powered by GPT-4o")

# Streamlit re-runs this whole file from top to bottom every time you click
# something. session_state is how we remember things between those re-runs.
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = None
if 'is_sample' not in st.session_state:
    st.session_state.is_sample = False

# API keys live in the sidebar so the main page stays clean
with st.sidebar:
    st.header("🔑 API keys")
    openai_api_key = st.text_input("OpenAI API key (GPT-4o)", type="password")
    serp_api_key = st.text_input("SerpAPI key (web search)", type="password")
    st.caption("This app doesn't save your keys.")

# Trip options in two columns
col1, col2 = st.columns(2)
with col1:
    destination = st.text_input("Where do you want to go?")
    num_days = st.number_input("How many days?", min_value=1, max_value=30, value=7)
with col2:
    budget = st.selectbox("💰 Budget", ["Budget", "Moderate", "Luxury"])
    travel_style = st.selectbox(
        "🌴 Travel style",
        ["Adventure", "Relaxing", "Food & Culture", "Nightlife", "Family"],
    )

start_date = st.date_input("📅 Trip start date", value=date.today())

generate = st.button("Generate Itinerary", type="primary")

# Only show the sample button if sample_itinerary.md exists
if SAMPLE_FILE.exists():
    if st.button("View sample itinerary (no keys needed)"):
        st.session_state.itinerary = SAMPLE_FILE.read_text(encoding="utf-8")
        st.session_state.is_sample = True

# ---------------------------------------------------------------------------
# PART 4: What happens when you click "Generate Itinerary"
# ---------------------------------------------------------------------------
if generate:
    if not (openai_api_key and serp_api_key):
        st.warning("Add both API keys in the sidebar first, or try the sample itinerary.")
    elif not destination.strip():
        st.warning("Type a destination first.")
    else:
        try:
            researcher, planner = build_agents(openai_api_key, serp_api_key)

            # Step 1: the researcher searches the web
            with st.spinner("Researching your destination..."):
                research_results: RunOutput = researcher.run(
                    f"""
                    Research {destination} for a {num_days} day trip.

                    Traveler preferences:
                    - Budget level: {budget}
                    - Travel style: {travel_style}

                    Find activities, attractions, restaurants, and accommodations
                    that match these preferences.
                    """,
                    stream=False,
                )

            # Step 2: the planner turns that research into an itinerary
            with st.spinner("Creating your personalized itinerary..."):
                prompt = f"""
                Destination: {destination}
                Duration: {num_days} days
                Budget: {budget}
                Travel Style: {travel_style}
                Research Results: {research_results.content}

                Create a personalized day-by-day itinerary based on this research.

                Make sure to:
                - Respect the {budget} budget level
                - Prioritize {travel_style} experiences
                - Recommend matching attractions and activities
                - Suggest restaurants appropriate for the travel style
                - Suggest accommodations appropriate for the budget
                - Organize everything into a practical daily schedule
                """
                response: RunOutput = planner.run(prompt, stream=False)

            st.session_state.itinerary = response.content
            st.session_state.is_sample = False

        except Exception as e:
            # We are at the very top of the app, so we catch everything here and
            # show a friendly message instead of a crash. The details go to the logs.
            print(f"TripPilot error: {e}")
            st.error(
                "Something went wrong. Check that both API keys are correct "
                "and that your OpenAI account has credit, then try again."
            )

# ---------------------------------------------------------------------------
# PART 5: Show the itinerary + the calendar download
# ---------------------------------------------------------------------------
# This sits OUTSIDE the button code on purpose: clicking the download button
# re-runs the file, and the itinerary would disappear if it only lived inside
# the "if generate:" block.
if st.session_state.itinerary:
    if st.session_state.is_sample:
        st.info("This is a saved example from a real run, so you can see the output without any API keys.")

    st.markdown(st.session_state.itinerary)

    ics_content = generate_ics_content(st.session_state.itinerary, start_date)
    st.download_button(
        label="📅 Download as calendar (.ics)",
        data=ics_content,
        file_name="travel_itinerary.ics",
        mime="text/calendar",
    )
