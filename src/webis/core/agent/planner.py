from typing import List, Dict, Any
from pydantic import BaseModel
from webis.core.llm.base import LLMFactory

class SubTask(BaseModel):
    id: str
    description: str
    dependencies: List[str] = []

class Planner:
    """
    Agentic planner to break down complex goals into subtasks.
    """
    def __init__(self, model_name: str = "gpt-4"):
        self.llm = LLMFactory.create_llm(model_name)

    def plan(self, goal: str) -> List[SubTask]:
        prompt = f"""
        You are an expert planner. Break down the following goal into a list of subtasks.
        Return the result as a JSON list of objects with 'id', 'description', and 'dependencies' fields.
        
        Goal: {goal}
        
        Example Output:
        [
            {{"id": "1", "description": "Search for Apple's latest financial report", "dependencies": []}},
            {{"id": "2", "description": "Extract revenue and profit figures", "dependencies": ["1"]}}
        ]
        """
        response = self.llm.generate(prompt)
        # Parse JSON from response (simplified)
        import json
        import re
        
        try:
            # Extract JSON block
            match = re.search(r"\[.*\]", response, re.DOTALL)
            if match:
                json_str = match.group(0)
                data = json.loads(json_str)
                return [SubTask(**item) for item in data]
            else:
                # Fallback if no JSON found
                return [SubTask(id="1", description=goal)]
        except Exception as e:
            print(f"Planning failed: {e}")
            return [SubTask(id="1", description=goal)]
