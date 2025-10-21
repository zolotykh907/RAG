import requests
import json


API_URL = "http://localhost:8000/posts"

data = requests.get(API_URL).json()

print(data)