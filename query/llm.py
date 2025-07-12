import os
import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logs import setup_logging


class LLMResponder:
    """Class for generation answer using LLM and context."""
    def __init__(self, config):
        """Initialize Indexing with configuration parameters.

        Args:
            config : configuration object with parameters.
        """
        self.model_name = config.llm
        self.ollama_host = config.ollama_host
        self.prompt_template = ChatPromptTemplate.from_template(config.prompt_template)
        self.llm = OllamaLLM(model=self.model_name,
                             base_url=os.getenv("OLLAMA_HOST", self.ollama_host)
                             )
        self.chain = self.prompt_template | self.llm
        self.logger = setup_logging(config.logs_dir, 'RAG_LLM')


    def generate_answer(self, question, texts):
        """Generate answer using LLM and context.

        Args:
            question (str): question to answer.
            texts (list[str]): list of texts for context.

        Returns:
            Str: generated answer
        """
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question must be a non-empty string")
        
        try:
            context = '\n'.join(texts)
            response = self.chain.invoke({"question": question, "context": context})
            return response
        except Exception as e:
            self.logger.error(f'Answer generation failed: {str(e)}')
            raise