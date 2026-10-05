# ✈️ TripPilot AI

**▶ [Watch the demo video](https://youtu.be/IcvbpsOCr38)** · **[Try the live app](https://trippilot-ai-meepsrhytfe9nnb2q2rabr.streamlit.app/)** (click "View sample itinerary", no API keys needed) · **[See my portfolio](https://iliass-elguaari.github.io)**

*Extended from an open-source AI travel planner: I added budget levels and travel styles, deployed it, fixed the vanishing-itinerary and calendar start-date bugs, and added the no-keys sample itinerary.*

## 📸 Preview
![alt text](image.png)

TripPilot AI is an AI-powered travel planning application that researches destinations and creates personalized multi-day itineraries based on a traveler's budget, travel style, destination, and trip duration.

## 🚀 Features

- 🌍 Destination-based travel research
- 📅 Personalized multi-day itineraries
- 💰 Budget preferences: Budget, Moderate, or Luxury
- 🌴 Travel styles including Adventure, Relaxing, Food & Culture, Nightlife, and Family
- 🔎 Live destination research using SerpAPI
- 🤖 AI-powered itinerary generation
- 🍽️ Restaurant, attraction, and accommodation recommendations
- 📆 Export itinerary as an `.ics` calendar file

## 🛠️ Technologies

- Python
- Streamlit
- OpenAI API
- SerpAPI
- Agno
- iCalendar

## 🧠 How It Works

1. The user enters a destination and trip duration.
2. The user chooses a budget level and travel style.
3. A research agent gathers relevant destination information.
4. The research is passed to an AI planning agent.
5. TripPilot AI generates a personalized day-by-day itinerary.
6. The itinerary can be exported to a calendar file.

## ▶️ Running Locally

Install the dependencies:

```bash
pip install -r requirements.txt