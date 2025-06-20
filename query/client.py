import requests

API_URL = "http://localhost:8000/query"

def ask_question(question: str):
    payload = {"question": question}
    response = requests.post(API_URL, json=payload)
    if response.status_code == 200:
        data = response.json()
        print("Ответ:", data["answer"])
        print("\nИспользованные фрагменты:")
        for i, chunk in enumerate(data["retrieved_chunks"], 1):
            print(f"{i}. {chunk.get('text', '')[:200]}...") 
    else:
        print(f"Ошибка {response.status_code}: {response.text}")

if __name__ == "__main__":
    question = input("Задай вопрос: ")
    ask_question(question)
