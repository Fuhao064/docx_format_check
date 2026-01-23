from agents.setting import LLMs

class EditorAgent:
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

    def get_image_caption(self, message):
        if not self.client:
            return "Error: LLM client not initialized."
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert editor capable of generating captions for images based on context."},
                    {"role": "user", "content": message}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating caption: {str(e)}"

    def enhance_content(self, content, type):
        if not self.client:
            return "Error: LLM client not initialized."
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert editor. Improve the content provided."},
                    {"role": "user", "content": content}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error enhancing content: {str(e)}"

    def enhance_paragraph_manager(self, para_manager, para_indices):
        """
        Enhance specific paragraphs in the paragraph manager.
        """
        if not self.client:
            return "Error: LLM client not initialized."
            
        results = {}
        for idx in para_indices:
            if 0 <= idx < len(para_manager.paragraphs):
                para = para_manager.paragraphs[idx]
                content = para.content
                enhanced = self.enhance_content(f"Please improve the following text:\n{content}", "text")
                results[idx] = enhanced
        return results
