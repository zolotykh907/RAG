#!/bin/bash

# Скрипт для запуска RAG Desktop приложения

echo "🚀 Запуск RAG Desktop Application..."
echo ""

# Проверка Rust
if ! command -v rustc &> /dev/null
then
    echo "⚠️  Rust не установлен!"
    echo ""
    echo "Для установки выполните:"
    echo "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    echo ""
    echo "После установки перезапустите терминал и запустите этот скрипт снова."
    exit 1
fi

# Проверка Node.js
if ! command -v node &> /dev/null
then
    echo "❌ Node.js не установлен!"
    echo "Установите Node.js с https://nodejs.org/"
    exit 1
fi

# Переход в директорию фронтенда
cd react_frontend || exit 1

# Проверка node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 Установка зависимостей..."
    npm install
fi

# Запуск приложения
echo "✨ Запуск десктопного приложения..."
echo ""
npm run tauri:dev
