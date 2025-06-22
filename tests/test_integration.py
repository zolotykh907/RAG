import pytest
import requests


API_URL = "http://localhost:8000/query"
question = 'Что такое ЦСКА?'


def test_pipeline():
    json_question = {"question": question}
    response = requests.post(API_URL, json=json_question)

    assert response.status_code == 200

    data = response.json()
    
    assert isinstance(data['answer'], str)
    assert len(data['answer']) > 0
    assert isinstance(data['texts'], list)



