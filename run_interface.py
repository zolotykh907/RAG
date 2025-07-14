 #!/usr/bin/env python3
"""
Скрипт для запуска RAG системы с веб-интерфейсом
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def check_docker():
    """Проверяет, установлен ли Docker"""
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_docker_compose():
    """Проверяет, установлен ли Docker Compose"""
    try:
        subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def start_system():
    """Запускает систему через Docker Compose"""
    print("🚀 Запуск RAG системы...")
    
    if not check_docker():
        print("❌ Docker не установлен. Пожалуйста, установите Docker.")
        return False
    
    if not check_docker_compose():
        print("❌ Docker Compose не установлен. Пожалуйста, установите Docker Compose.")
        return False
    
    try:
        # Запуск системы
        subprocess.run(["docker-compose", "up", "--build", "-d"], check=True)
        print("✅ Система запущена успешно!")
        
        # Ждем немного для инициализации
        print("⏳ Ожидание инициализации сервисов...")
        time.sleep(10)
        
        # Открываем браузер
        print("🌐 Открытие веб-интерфейса...")
        webbrowser.open("http://localhost:8000")
        
        print("\n🎉 Система готова к работе!")
        print("📱 Веб-интерфейс: http://localhost:8000")
        print("🔧 API: http://localhost:8000/query")
        print("\nДля остановки системы выполните: docker-compose down")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при запуске: {e}")
        return False

def stop_system():
    """Останавливает систему"""
    print("🛑 Остановка RAG системы...")
    try:
        subprocess.run(["docker-compose", "down"], check=True)
        print("✅ Система остановлена!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при остановке: {e}")
        return False

def show_status():
    """Показывает статус системы"""
    try:
        result = subprocess.run(["docker-compose", "ps"], check=True, capture_output=True, text=True)
        print("📊 Статус контейнеров:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при получении статуса: {e}")

def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("🤖 RAG Q&A Система")
        print("\nИспользование:")
        print("  python run_interface.py start   - Запустить систему")
        print("  python run_interface.py stop    - Остановить систему")
        print("  python run_interface.py status  - Показать статус")
        print("  python run_interface.py restart - Перезапустить систему")
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        start_system()
    elif command == "stop":
        stop_system()
    elif command == "status":
        show_status()
    elif command == "restart":
        stop_system()
        time.sleep(2)
        start_system()
    else:
        print(f"❌ Неизвестная команда: {command}")
        print("Доступные команды: start, stop, status, restart")

if __name__ == "__main__":
    main()