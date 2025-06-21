import pytest
import requests


API_URL = "http://localhost:8000/query"
QUEST = "Что такое ЦСКА?"


def test_pipeline():
    payload = {"question": QUEST}
    response = requests.post(API_URL, json=payload)

    assert response.status_code == 200

    data = response.json()
    answer = data['answer']
    assert isinstance(answer, str)

