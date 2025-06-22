from langchain.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import os

class LLMResponder:
    def __init__(self, config):
        self.model_name = config.llm
        self.llm = Ollama(
            model=self.model_name,
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434")
        )
        # self.prompt_template = PromptTemplate(
        #     input_variables=["question", "context"],
        #     template=(
        #         "Ты — интеллектуальный помощник, использующий информацию из базы знаний, чтобы точно ответить на вопрос.\n\n"
        #         "Вопрос: {question}\n\n"
        #         "Контекст:\n{context}\n\n"
        #         "Если точного ответа нет, напиши что не нашел информацию. Ответ пиши всегда на русском языке.\n\n"
        #         "Если нашел - то процитируй или перефразируй, оставляя только самое важное для ответа на вопрос"
        #     )
        # )
        self.prompt_template = PromptTemplate(
            input_variables=["question", "context"],
            template = config.prompt_template
        )

        self.chain = LLMChain(prompt=self.prompt_template, llm=self.llm)

    def generate_answer(self, question: str, texts: list[str]) -> str:
        context = "\n\n".join(texts)
        response = self.chain.run(question=question, context=context)
        return response.strip()
