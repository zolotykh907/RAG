from unittest.mock import MagicMock
from query.llm import LLMResponder

class DummyConfig:
    llm = "dummy-model"
    prompt_template = (
        "Ты — интеллектуальный помощник, использующий информацию из базы знаний, чтобы точно ответить на вопрос.\n\n"
        "Вопрос: {question}\n\n"
        "Контекст:\n{context}\n\n"
        "Если точного ответа нет, напиши что не нашел информацию. Ответ пиши всегда на русском языке.\n\n"
        "Если нашел - то процитируй или перефразируй, оставляя только самое важное для ответа на вопрос"
    )
    ollama_host = "http://localhost:11434"

def test_generate_prompt_format_with_mock():
    config = DummyConfig()
    
    responder = LLMResponder(config)

    responder.chain = MagicMock()
    responder.chain.invoke.return_value = "Ответ: ЦСКА — армейский спортивный клуб."

    question = "Что такое ЦСКА?"
    chunks = ["ЦСКА — Центральный спортивный клуб армии."]

    result = responder.generate_answer(question, chunks)

    responder.chain.invoke.assert_called_once()
    
    called_args = responder.chain.invoke.call_args[0][0]
    assert called_args["question"] == question
    assert "ЦСКА" in called_args["context"]

    assert isinstance(result, str)
    assert len(result) > 0