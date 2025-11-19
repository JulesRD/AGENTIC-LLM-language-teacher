from typing import Dict, List
from langgraph import Node
from tools.memory import MemoryModule

class PlannerAgent(Node):
    def __init__(self, llm, memory : ):
        super().__init__(name="Planner")
        self.llm = llm
        self.memory = memory

    def generate_learning_plan(self, user_info: Dict) -> List[Dict]:
        """
        Create a simple structured learning plan based on user data.
        Later, this can be replaced with more sophisticated rule-based or LLM-driven logic.
        """

        level = user_info.get("level", "beginner")
        interests = user_info.get("interests", ["general topics"])
        common_errors = user_info.get("errors", [])

        prompt = f"""
        You are an intelligent language tutor. Based on the user profile:
        - Level: {level}
        - Common errors: {', '.join(common_errors) if common_errors else 'None'}
        - Interests: {', '.join(interests)}

        Create a short 3-step personalized learning plan.
        Each step should specify:
        - Lesson type (dialogue, exercise, or review)
        - Topic
        - Objective
        Respond in JSON format.
        """

        # Simulated LLM response for now
        response = self.llm.generate(prompt)

        # Example fallback if LLM not available
        if not response:
            response = [
                {"type": "dialogue", "topic": f"{interests[0]} conversation", "objective": "practice fluency"},
                {"type": "exercise", "topic": "past tense verbs", "objective": "correct grammar"},
                {"type": "review", "topic": "error recap", "objective": "reinforce weak points"},
            ]
        else:
            try:
                response = eval(response) if isinstance(response, str) else response
            except Exception:
                response = [{"type": "dialogue", "topic": "general", "objective": "communicate naturally"}]

        return response

    def update_memory(self, user_info: Dict, plan: List[Dict]):
        """Merge new plan and metadata into shared memory."""
        updated_info = user_info.copy()
        updated_info["learning_plan"] = plan
        self.memory.update_user_profile(updated_info)

    def run(self, user_info: Dict):
        """Main planner entry point — called by Coordinator."""
        plan = self.generate_learning_plan(user_info)
        self.update_memory(user_info, plan)
        return {"plan": plan, "message": "New learning plan created and memory updated."}