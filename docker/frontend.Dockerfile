FROM node:20

# Устанавливаем рабочую директорию
WORKDIR /app/frontend

# Копируем только package.json и lock-файл для install
COPY frontend/package*.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем остальной исходный код
COPY frontend/ ./

# Открываем порт dev-сервера
EXPOSE 3000

# Запускаем dev-сервер React
CMD ["npm", "start"]
