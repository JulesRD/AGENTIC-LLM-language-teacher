from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_core.tools import tool
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize the chat model using Ollama
model = ChatOllama(
    model="llama3.2:latest",
    temperature=0.8,
)

# Define a simple tool
@tool
def get_weather(location: str) -> str:
    """Get the current weather for a given location."""
    return f"The weather in {location} is sunny and 25°C."

# Define the system prompt
system_prompt = "You are a helpful assistant with access to tools. When asked about weather, use the get_weather tool."

# Create the agent without auto-execution of tools
agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt=system_prompt,
)

# Initial user message
user_message = "What's the weather in Paris? What can you conclude?"
messages = [("user", user_message)]

while True:
    # Call the agent
    response = agent.invoke({"messages": messages})
    final_message = response["messages"][-1].content
    print("Agent:", final_message)

    # Check if the agent wants to call a tool
    if "<|python_tag|>" in final_message:
        # Extraire le nom du tool et les arguments
        tag_start = final_message.index("<|python_tag|>") + len("<|python_tag|>")
        tag_end = final_message.index("\n", tag_start) if "\n" in final_message[tag_start:] else len(final_message)
        tool_call = final_message[tag_start:tag_end]

        # On parse le tool_call pour extraire location (très simple ici)
        # Exemple: get_weather properties="location: Paris" required=["location"]="true" type="string"
        location = tool_call.split('location:')[1].split('"')[0].strip()

        # Appeler la fonction Python correspondante
        tool_result = get_weather(location)

        # Ajouter la sortie du tool dans l'historique comme un message assistant
        messages.append(("assistant", final_message))  # réponse du modèle avant exécution
        messages.append(("tool", tool_result))        # sortie du tool

        # On boucle pour demander au modèle de continuer avec le résultat du tool
        continue
    else:
        # Plus de tool à appeler, fin de boucle
        break
