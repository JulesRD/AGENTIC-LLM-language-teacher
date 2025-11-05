from langchain_core.tools import tool
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

END_OF_DISCUSSION = False
@tool
def end_discussion() -> str:
    """End the current discussion"""
    global END_OF_DISCUSSION
    END_OF_DISCUSSION = True
    print("end_discussion called, setting END_OF_DISCUSSION to", END_OF_DISCUSSION)
    return "la discussion est terminée."