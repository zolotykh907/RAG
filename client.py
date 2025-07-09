import requests

API_URL = "http://localhost:8000/query"

def ask_question(question: str):
    json_question = {"question": question}
    response = requests.post(API_URL, json=json_question)
    if response.status_code == 200:
        data = response.json()
        print("Ответ:", data["answer"])
        #print(data['texts'])
    else:
        print(f"Ошибка {response.status_code}: {response.text}")

# question = input("Задай вопрос: ")
#ask_question(question)

ask_question("Когда была создана YOLOv4?")
