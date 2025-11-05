from langchain_core.prompts import ChatPromptTemplate
from langchain_mistralai import ChatMistralAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    raise ValueError("MISTRAL_API_KEY not found in .env")

# Initialize model
model = ChatMistralAI(
    model="mistral-small-latest",
    temperature=0,
    api_key=api_key,
)

# Define a simple tool
@tool
def get_weather(location: str) -> str:
    """Get the current weather for a given location."""
    return f"The weather in {location} is sunny and 25°C."

# Define the system prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant with access to tools. "
               "When asked about weather, use the get_weather tool."),
    ("placeholder", "{messages}")
])

# Create the agent
agent = create_react_agent(
    model=model,
    tools=[get_weather],
    prompt=prompt,
)

# Run the agent
try:
    response = agent.invoke({
        "messages": [
            ("user", "What's the weather in Paris ? What can you conclude ?")
        ]
    })

    # Print results
    final_message = response["messages"][-1]
    print(final_message.content)
except Exception as e:
    print(f"Erreur lors de l'appel à l'API : {e}")
    print("Vérifiez votre connexion internet et la disponibilité de l'API Mistral.")
