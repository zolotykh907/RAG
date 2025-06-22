import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM


class LLMResponder:
    def __init__(self, config):
        self.model_name = config.llm
        self.prompt_template = ChatPromptTemplate.from_template(config.prompt_template)
        self.llm = OllamaLLM(model="llama3",
                             base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434")
                             )

        self.chain = self.prompt_template | self.llm

    def generate_answer(self, question, texts):
        context = '\n'.join(texts)
        response = self.chain.invoke({"question": question, "context": context})

        return response