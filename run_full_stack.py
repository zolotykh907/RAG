#!/usr/bin/env python3
"""
Скрипт для запуска полного стека RAG System
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def run_command(command, cwd=None, shell=True):
    """Запуск команды с выводом в реальном времени"""
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        for line in process.stdout:
            print(line, end='')
            
        process.wait()
        return process.returncode == 0
    except Exception as e:
        print(f"Ошибка выполнения команды: {e}")
        return False

def check_node_installed():
    """Проверка установки Node.js"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def check_npm_installed():
    """Проверка установки npm"""
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def main():
    print("🚀 Запуск полного стека RAG System...")
    print("=" * 50)
    
    # Проверка зависимостей
    print("📋 Проверка зависимостей...")
    
    if not check_node_installed():
        print("❌ Node.js не установлен. Установите Node.js с https://nodejs.org/")
        return False
        
    if not check_npm_installed():
        print("❌ npm не установлен. Установите npm")
        return False
    
    print("✅ Node.js и npm установлены")
    
    # Проверка существования frontend папки
    frontend_path = Path("frontend")
    if not frontend_path.exists():
        print("❌ Папка frontend не найдена")
        return False
    
    # Установка зависимостей frontend
    print("\n📦 Установка зависимостей frontend...")
    if not run_command("npm install", cwd="frontend"):
        print("❌ Ошибка установки зависимостей frontend")
        return False
    
    print("✅ Зависимости frontend установлены")
    
    # Запуск backend
    print("\n🔧 Запуск backend API...")
    backend_process = subprocess.Popen([
        sys.executable, "app.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Ждем запуска backend
    print("⏳ Ожидание запуска backend...")
    time.sleep(3)
    
    # Проверка статуса backend
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API запущен на http://localhost:8000")
        else:
            print("⚠️ Backend API может быть недоступен")
    except:
        print("⚠️ Не удалось проверить статус backend API")
    
    # Запуск frontend
    print("\n🌐 Запуск frontend...")
    frontend_process = subprocess.Popen([
        "npm", "start"
    ], cwd="frontend", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Ждем запуска frontend
    print("⏳ Ожидание запуска frontend...")
    time.sleep(5)
    
    print("\n🎉 Полный стек запущен!")
    print("=" * 50)
    print("🌐 Frontend: http://localhost:3000")
    print("🔧 Backend API: http://localhost:8000")
    print("📖 API документация: http://localhost:8000/docs")
    print("⏹️ Для остановки нажмите Ctrl+C")
    
    # Открываем браузер
    try:
        webbrowser.open("http://localhost:3000")
    except:
        pass
    
    try:
        # Ждем завершения процессов
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Остановка процессов...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ Процессы остановлены")

if __name__ == "__main__":
    main() 