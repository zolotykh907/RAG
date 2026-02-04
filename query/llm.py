import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'shared'))
from logs import setup_logging


class LLMResponder:
    """Class for generation answer using LLM and context."""
    def __init__(self, config):
        """Initialize Indexing with configuration parameters.

        Args:
            config : configuration object with parameters.
        """
        self.model_name = config.llm
        self.lm_studio_host = config.lm_studio_host
        self.prompt_template = ChatPromptTemplate.from_template(config.prompt_template)
        self.llm = ChatOpenAI(
            model=self.model_name,
            base_url=os.getenv("LM_STUDIO_HOST", self.lm_studio_host),
            api_key="lm-studio",  # LM Studio doesn't require real API key
            temperature=0.7
        )
        self.chain = self.prompt_template | self.llm
        self.logger = setup_logging(config.logs_dir, 'RAG_LLM')


    def generate_answer(self, question, texts):
        """Generate answer using LLM and context.

        Args:
            question (str): question to answer.
            texts (list[str]): list of texts for context.

        Returns:
            str: generated answer
        """
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question must be a non-empty string")

        if not texts or not isinstance(texts, list):
            raise ValueError("Texts must be a non-empty list")

        try:
            context = '\n'.join(texts)
            response = self.chain.invoke({"question": question, "context": context})

            # Extract content from AIMessage object
            if hasattr(response, 'content'):
                answer = response.content
            else:
                answer = str(response)

            if not answer or not answer.strip():
                self.logger.warning("LLM returned empty response")
                return "Не удалось сгенерировать ответ."

            return answer.strip()
        except Exception as e:
            self.logger.error(f'Answer generation failed: {str(e)}')
            raise
