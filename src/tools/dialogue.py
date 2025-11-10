from langchain_core.tools import tool
from src.config import config
@tool
def get_weather(location: str) -> str:
    """Get the current weather for a given location."""
    print("get_weather called with location:", location)
    if location.lower() == "chambéry":
        return "The weather in Chambéry is cloudy and 18°C."
    else:
        return f"The weather in {location} is sunny and 25°C."

@tool
def get_city_by_id(city_id: str) -> str:
    """Get city name by its ID."""
    return "The city with ID " + city_id + " is Chambery."

@tool
def end_discussion() -> str:
    """End the current discussion"""
    config.end_of_discussion = True
    print("end_discussion called, setting END_OF_DISCUSSION to", config.end_of_discussion)
    return "la discussion est terminée."