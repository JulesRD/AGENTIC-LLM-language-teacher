from langchain_ollama import ChatOllama
from langchain_mistralai import ChatMistralAI
from langchain.agents import create_agent
from src.tools.dialogue import *
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()



def llm(user_message, model, system_prompt, tools):

    agent = create_agent(
        model=model,
        tools=[get_weather],
        system_prompt=system_prompt,
    )
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


# Determine model provider from environment
model_name = os.getenv("MODEL", "ollama").lower()

if model_name.startswith("mi") :
    model = ChatMistralAI(
        model=model_name,
        api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.8,
    )
else:
    model = ChatOllama(
        model=model_name,
        temperature=0.8,
    )

# Define a simple tool


# Define the system prompt
system_prompt = "You are a helpful assistant with access to tools. When asked about weather, use the get_weather tool."

user_message = "What's the weather in Paris? What can you conclude?"

llm(user_message, model, system_prompt, [get_weather])
