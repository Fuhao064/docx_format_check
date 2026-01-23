from agents.setting import LLMs

class AdviceAgent:
    def __init__(self, model_name='alibaba_qwen-flash'):
        self.llm = LLMs()
        try:
            self.llm.set_model(model_name)
            self.model = self.llm.model
            self.client = self.llm.client
        except ValueError as e:
            print(f"Error setting model: {e}")
            self.llm = None
            self.client = None
            self.model = None

    def provide_advice(self, doc_content):
        if not self.client:
            return "Error: LLM client not initialized."
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert academic advisor. Provide advice on the document structure and content."},
                    {"role": "user", "content": f"Please analyze this document and provide advice:\n\n{doc_content[:10000]}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error providing advice: {str(e)}"
