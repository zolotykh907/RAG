import subprocess

ollama_process = subprocess.Popen(['ollama', 'serve'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

uvicorn_process = subprocess.Popen(['uvicorn', '.app:app', '--host', '0.0.0.0', '--port', '8000'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

client_process = subprocess.Popen(['python', 'client.py'])

print("Оба процесса запущены. Для остановки нажмите Ctrl+C")

try:
    ollama_process.wait()
    uvicorn_process.wait()
except KeyboardInterrupt:
    print("Процессы остановлены пользователем")
    
