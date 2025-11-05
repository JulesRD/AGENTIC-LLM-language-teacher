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
        tools=tools,
        system_prompt=system_prompt,
    )
    messages = [("user", user_message)]
    response = agent.invoke({"messages": messages})
    final_message = response["messages"][-1].content
    print("Agent:", final_message)
        


# Determine model provider from environment
model_name = os.getenv("MODEL", "ollama").lower()

if model_name.startswith("m") :
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

system_prompt = """
You are a helpful assistant with access to tools.
When asked about weather, use the get_weather tool.
When asked about city id, use the get_city_by_id tool.
"""

user_message = "What's the weather in the city with id AZéB7U? What can you conclude?"

tools = [get_weather, get_city_by_id]

llm(
    user_message,
    model,
    system_prompt,
    tools)
