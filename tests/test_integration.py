import requests
import pytest


API_URL = "http://localhost:8000/query"
question = 'Что такое ЦСКА?'


def test_pipeline():
    json_question = {"question": question}
    try:
        response = requests.post(API_URL, json=json_question, timeout=5)
    except requests.ConnectionError:
        pytest.skip("RAG API is not running on localhost:8000")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data['answer'], str)
    assert len(data['answer']) > 0
    assert isinstance(data['texts'], list)
