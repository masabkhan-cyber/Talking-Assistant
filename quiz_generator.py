import os
import streamlit as st
from meta_ai_api import MetaAI
from rag_retriever import RAGRetriever

class QuizGenerator:
    """
    A class to generate quizzes from topics or PDF documents using an AI model.
    """
    def __init__(self, config):
        self.ai = MetaAI()
        # A system prompt can be used here if specific persona is needed for quiz master
        self.system_prompt = config.get("system_prompt", "") 

    def _build_prompt(self, context, difficulty, num_questions=5):
        """
        Builds a detailed prompt for the AI to generate a quiz in JSON format.
        """
        prompt = (
            f"You are an expert quiz creator. Your task is to generate a multiple-choice quiz.\n"
            f"Based *only* on the context provided below, create a quiz with exactly {num_questions} questions.\n"
            f"The desired difficulty level for the quiz is: {difficulty}.\n"
            f"For each question, provide 4 distinct options and clearly indicate the single correct answer.\n\n"
            f"**Context:**\n---\n{context}\n---\n\n"
            f"**Instructions for Output:**\n"
            f"Generate the quiz in a valid, raw JSON format. The output must be a list of Python dictionaries.\n"
            f"Each dictionary must have these exact keys: 'question' (string), 'options' (a list of 4 strings), and 'answer' (the string of the correct option).\n"
            f"Do not include any text or explanations outside of the JSON structure.\n\n"
            f"**Example JSON format:**\n"
            f'[{{"question": "What is the primary color of the sky on a clear day?", "options": ["Green", "Blue", "Red", "Yellow"], "answer": "Blue"}}, ...]'
        )
        return prompt

    def generate_from_topic(self, topic, difficulty, num_questions=5):
        """
        Generates a quiz from a given topic using the AI's general knowledge.
        """
        # The context for a topic is the topic itself, relying on the AI's internal knowledge.
        context = f"General knowledge about the topic: {topic}"
        prompt = self._build_prompt(context, difficulty, num_questions)
        try:
            response = self.ai.prompt(message=prompt).get('message', "[]")
            return response
        except Exception as e:
            st.error(f"Error generating quiz from topic: {e}")
            return None

    def generate_from_pdf(self, pdf_path, difficulty, num_questions=5):
        """
        Generates a quiz from the content of a PDF file.
        """
        try:
            rag = RAGRetriever(pdf_path)
            # Retrieve a substantial amount of context to ensure good coverage of the PDF content.
            # The query is generic to pull key information from the document.
            context = rag.retrieve_context(f"Generate a quiz from the key information in this document.", k=15)

            if not context:
                st.error("Could not extract sufficient information from the PDF to create a quiz.")
                return None

            prompt = self._build_prompt(context, difficulty, num_questions)
            response = self.ai.prompt(message=prompt).get('message', "[]")
            return response
        except Exception as e:
            st.error(f"Error generating quiz from PDF: {e}")
            return None