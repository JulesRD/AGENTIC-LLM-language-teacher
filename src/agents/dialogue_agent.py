from langchain_ollama import ChatOllama
from langchain_mistralai import ChatMistralAI
from langchain.agents import create_agent
from src.tools.dialogue import *
from src.config import config
import os
from dotenv import load_dotenv
import json
import sys

# Force UTF-8 encoding for input/output
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()
NUMBER_WINDOWS = 2


# Determine model provider from environment
model_name = os.getenv("MODEL", "ollama").lower()

if model_name.startswith("m") :
    model = ChatMistralAI(
        model=model_name,
        api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0,
    )
else:
    model = ChatOllama(
        model=model_name,
        temperature=0.8,
    )

user_description = "Dimitri, 21 years old, student at Epita in AI"
theme = "past simple vs present perfect"
language = "English"
level = "B2-C1, TOEIC 815/990"
teacher_style = "formal"


with open('data/dialogue.system_prompt.md', 'r') as f:
    system_prompt = f.read()
system_prompt = system_prompt.format(
    user_description=user_description,
    theme=theme,
    language=language,
    level=level,
    teacher_style=teacher_style
)

tools = [end_discussion]

first_user_message = "Start the language learning dialogue by introducing yourself and asking the first specific question about the theme."


def run_dialogue_agent(model, system_prompt, tools, first_user_message):
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )

    messages = []

    # Initial prompt to start the conversation
    messages.append(("user", first_user_message))
    response = agent.invoke({"messages": messages})
    initial_message = response["messages"][-1].content
    print("")
    print("------------- Type /quit to exit. -------------", end="\n\n\n")
    print("Agent:", initial_message, end="\n\n")
    messages.append(("assistant", initial_message))


    while True:
        user_input = input("You: ")
        if user_input.strip() == "/quit":
            print("Goodbye!")
            break
        messages.append(("user", user_input))
        response = agent.invoke({"messages": messages})
        agent_message = response["messages"][-1].content
        print("\n------------ Agent ------------")
        if config.end_of_discussion:
            print("\nDiscussion ended by the agent.")
            break
        print(agent_message, end="\n\n")
        messages.append(("assistant", agent_message))


if __name__ == "__main__":
    run_dialogue_agent(model, system_prompt, tools, first_user_message)
