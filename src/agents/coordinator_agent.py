import os
from langchain_ollama import ChatOllama
from langchain_mistralai import ChatMistralAI
from langchain.agents import create_agent
from dotenv import load_dotenv
import json


class CoordinatorAgent:

    def __init__(self, memory_module, dialogue_agent, exercises_agent, planner_agent):

        load_dotenv()

        # Persistent user profile memory
        self.memory_module = memory_module

        # Conversation-only short-term memory
        self.conversation_history = []

        # Sub-agents
        self.dialogue_agent = dialogue_agent
        self.exercises_agent = exercises_agent
        self.planner_agent = planner_agent

        # Internal LLM for decision making
        self.model = self._init_model()
        self.system_prompt = self._load_coord_system_prompt()

        self.agent = create_agent(
            model=self.model,
            tools=[],
            system_prompt=self.system_prompt
        )


    # -----------------------------------------------------------
    # INITIALIZATION
    # -----------------------------------------------------------

    def _init_model(self):
        model_name = os.getenv("MODEL", "ollama").lower()
        if model_name.startswith("m"):
            return ChatMistralAI(
                model=model_name,
                api_key=os.getenv("MISTRAL_API_KEY"),
                temperature=0
            )
        return ChatOllama(
            model=model_name,
            temperature=0
        )

    def _load_coord_system_prompt(self):
        with open("data/coordinator.system_prompt.md", "r") as f:
            return f.read()


    # -----------------------------------------------------------
    # MAIN ENTRY POINT
    # -----------------------------------------------------------

    def handle_user_input(self, user_message, from_subagent=False):
        """
        - If memory is empty → ask onboarding questions
        - If memory is filled → ask session start question
        - If response from user → classify with LLM and route
        - If callback from sub-agent → handle feedback and choose next step
        """

        if not from_subagent:
            self.conversation_history.append(("user", user_message))

        # CASE 1 : FIRST TIME USER
        if self.memory_module.is_empty():

            if not from_subagent and not self.memory_module.expecting_user_info:
                return self._ask_user_onboarding()

            if self.memory_module.expecting_user_info:
                return self._process_onboarding_user_response(user_message)

        # CASE 2 : USER ALREADY REGISTERED
        else:
            if not from_subagent and not self.memory_module.expecting_task_description:
                return self._ask_user_session_question()

            if self.memory_module.expecting_task_description:
                return self._process_user_task_request(user_message)

        # CASE 3 : SUB-AGENT CALLBACK
        return self._handle_subagent_callback(user_message)


    # -----------------------------------------------------------
    # CASE 1 — FIRST TIME USER
    # -----------------------------------------------------------

    def _ask_user_onboarding(self):
        """Just a static question, not LLM generated."""
        self.memory_module.expecting_user_info = True
        return (
            "Before we begin, I need a few details to personalize your learning.\n"
            "📌 What is your native language?\n"
            "📌 Which language do you want to learn?\n"
            "📌 What is your current level?\n"
            "📌 What are your interests and difficulties?"
        )

    def _process_onboarding_user_response(self, user_message):
        """
        Use LLM to:
        - Extract structured user profile
        - Create a prompt for the Planner Agent
        """

        llm_input = [
            ("system", self.system_prompt),
            ("user", f"Extract user information and prepare a JSON for the Planner Agent.\nUser said: {user_message}")
        ]

        result = self.agent.invoke({"messages": llm_input})
        json_out = json.loads(result["messages"][-1].content)

        user_profile = json_out["user_profile"]
        planner_prompt = json_out["prompt_for_planner"]

        # Update memory module
        self.memory_module.update_profile(user_profile)
        self.memory_module.save()
        self.memory_module.expecting_user_info = False

        # Call planner
        return self.planner_agent.run(
            memory_module=self.memory_module,
            prompt=planner_prompt,
            callback=self
        )


    # -----------------------------------------------------------
    # CASE 2 — MEMORY ALREADY FILLED
    # -----------------------------------------------------------

    def _ask_user_session_question(self):
        self.memory_module.expecting_task_description = True
        return "What would you like to do today?"

    def _process_user_task_request(self, user_message):

        llm_input = [
            ("system", self.system_prompt),
            ("user", f"Classify the user request and return JSON.\nUser message: {user_message}")
        ]

        result = self.agent.invoke({"messages": llm_input})
        json_out = json.loads(result["messages"][-1].content)

        action = json_out["action"]
        prompt = json_out["prompt_for_agent"]

        self.memory_module.expecting_task_description = False

        return self._route_action(action, prompt)


    # -----------------------------------------------------------
    # CASE 3 — SUB-AGENT CALLBACK HANDLING
    # -----------------------------------------------------------

    def _handle_subagent_callback(self, agent_output):

        llm_input = [
            ("system", self.system_prompt),
            ("user", f"Analyze this sub-agent output and return JSON with next action or ask_user flag.\nOutput: {agent_output}")
        ]

        result = self.agent.invoke({"messages": llm_input})
        json_out = json.loads(result["messages"][-1].content)

        if json_out["ask_user"]:
            return "What would you like to do next?"

        action = json_out["action"]
        prompt = json_out["prompt_for_agent"]

        return self._route_action(action, prompt)


    # -----------------------------------------------------------
    # ROUTING
    # -----------------------------------------------------------

    def _route_action(self, action, prompt):

        if action == "dialogue":
            return self.dialogue_agent.run(prompt, memory_module=self.memory_module, callback=self)

        if action == "exercises":
            return self.exercises_agent.run(prompt, memory_module=self.memory_module, callback=self)

        if action == "planner":
            return self.planner_agent.run(prompt, memory_module=self.memory_module, callback=self)

        return "❌ Unknown action returned by LLM."
