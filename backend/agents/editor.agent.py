import os
from agents.setting import LLMs

class EditorAgent:
    def __init__(self, model_name='qwen-plus'):
        self.llm = LLMs()
        try:
            self.llm.set_model(model_name)
        except ValueError as e:
            print(f"Error setting model: {e}")
            self.llm = None
            self.llm.tools 

   