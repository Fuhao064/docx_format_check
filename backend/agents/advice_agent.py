import os
from agents.setting import LLMs

class AdviceAgent:
    def __init__(self, model_name='qwen-plus'):
        self.llm = LLMs()
        try:
            self.llm.set_model(model_name)
        except ValueError as e:
            print(f"Error setting model: {e}")
            self.llm = None
        
    def get_advice(self, doc_content):
        if self.llm is None or self.llm.client is None or self.llm.model is None:
            return "LLM is not properly initialized. Please check the model configuration."

        try:
            response = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides suggestions for improving the content of a document."},
                    {"role": "user", "content": f"Please provide suggestions for improving the following document content:\n{doc_content}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"An error occurred while getting advice from the LLM: {e}"


