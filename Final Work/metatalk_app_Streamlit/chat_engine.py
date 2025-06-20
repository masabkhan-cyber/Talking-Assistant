from meta_ai_api import MetaAI
from rag_retriever import RAGRetriever

class ChatEngine:
    def __init__(self, config):
        self.ai = MetaAI()
        self.system_prompt = config.get("system_prompt", "")
        self.rag = None  # PDF context

    def attach_pdf(self, pdf_path):
        try:
            self.rag = RAGRetriever(pdf_path)
            return True, f"✅ Loaded context from {pdf_path}"
        except Exception as e:
            return False, f"❌ Error loading PDF: {str(e)}"

    def build_prompt(self, user_input):
        if self.rag:
            context = self.rag.retrieve_context(user_input, k=3)
            prompt = (
                f"{self.system_prompt}\n\n"
                f"Use the following context to answer the question:\n"
                f"{context}\n\n"
                f"User: {user_input}"
            )
            return prompt
        else:
            return f"{self.system_prompt}\nUser: {user_input}"

    def get_response(self, user_input):
        prompt = self.build_prompt(user_input)
        try:
            return self.ai.prompt(message=prompt).get('message', "❌ No response from MetaAI.")
        except Exception as e:
            return f"🛑 Error from MetaAI: {str(e)}"
