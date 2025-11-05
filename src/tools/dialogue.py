from langchain_core.tools import tool
@tool
def get_weather(location: str) -> str:
    """Get the current weather for a given location."""
    return f"The weather in {location} is sunny and 25°C."

@tool
def get_city_by_id(city_id: str) -> str:
    """Get city name by its ID."""
    return "The city with ID " + city_id + " is Chambery."