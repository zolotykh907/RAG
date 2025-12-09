# Документация системы аутентификации

## Обзор

Реализована полная система аутентификации и авторизации с использованием JWT токенов, ролевой модели и защитой всех эндпоинтов.

## Структура базы данных

### Таблица `roles`
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Primary Key |
| name | String(50) | Название роли (уникальное) |

**Роли:**
- `user` - обычный пользователь
- `admin` - администратор

### Таблица `users`
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Primary Key |
| email | String(255) | Email пользователя (уникальный, индексированный) |
| password | String(255) | Хеш пароля (SHA-256) |
| role_id | Integer | Foreign Key на `roles.id` |

## Backend API

### Публичные эндпоинты (без авторизации)

#### POST /auth/register
Регистрация нового пользователя. Автоматически назначается роль `user`.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (201):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": {
    "id": 1,
    "name": "user"
  }
}
```

#### POST /auth/token
Вход в систему и получение JWT токена.

**Request (Form Data):**
```
username=user@example.com
password=password123
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Защищенные эндпоинты (требуют авторизации)

Все запросы должны содержать заголовок:
```
Authorization: Bearer <token>
```

#### GET /auth/me
Получить информацию о текущем пользователе.

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": {
    "id": 1,
    "name": "user"
  }
}
```

#### POST /pages
Создать новую страницу (доступно всем авторизованным).

#### GET /pages/{page_id}
Получить страницу по ID (доступно всем авторизованным).

#### POST /pages/{page_id}/visit
Зарегистрировать посещение страницы (доступно всем авторизованным).

#### POST /pages/{page_id}/time
Обновить время на странице (доступно всем авторизованным).

#### GET /kpi
**ТОЛЬКО ДЛЯ АДМИНОВ** - Получить статистику по всем страницам.

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Введение",
    "url": "/introduction",
    "kpi": {
      "id": 1,
      "page_id": 1,
      "visits": 5,
      "total_time_seconds": 120
    }
  }
]
```

**Response (403) если не админ:**
```json
{
  "detail": "Not enough permissions"
}
```

#### POST /flip
Перевернуть изображение (доступно всем авторизованным).

#### GET /posts
Получить посты (доступно всем авторизованным).

## Frontend

### Структура файлов

```
src/
├── contexts/
│   └── AuthContext.js          # Контекст аутентификации
├── pages/
│   ├── Login.js                # Страница входа
│   ├── Register.js             # Страница регистрации
│   └── Auth.css                # Стили для auth страниц
├── components/
│   ├── ProtectedRoute.js       # Компонент защиты роутов
│   ├── Sidebar.js              # Обновлен для показа юзера и кнопки выхода
│   └── MainPanel.js            # Обновлен с защищенными роутами
├── utils/
│   └── api.js                  # Обновлен для отправки JWT токенов
└── App.js                      # Обернут в AuthProvider
```

### AuthContext

Предоставляет:
- `user` - текущий пользователь или null
- `loading` - состояние загрузки
- `login(email, password)` - функция входа
- `register(email, password)` - функция регистрации
- `logout()` - функция выхода
- `isAdmin()` - проверка прав админа

### ProtectedRoute

Компонент для защиты роутов:
```jsx
<ProtectedRoute>
  <SomePage />
</ProtectedRoute>

// Только для админов
<ProtectedRoute adminOnly>
  <Statistics />
</ProtectedRoute>
```

### Автоматическая авторизация

JWT токен сохраняется в `localStorage` и автоматически:
- Проверяется при загрузке приложения
- Добавляется ко всем API запросам
- Удаляется при выходе

### Редирект

- Неавторизованные пользователи → `/login`
- Не-админы на админских страницах → `/`
- После успешного входа/регистрации → `/`

## Тестовые аккаунты

### Администратор
```
Email: admin@test.com
Пароль: admin123
```
**Доступ:** Все страницы + Статистика

### Обычный пользователь
```
Email: user@test.com
Пароль: user123
```
**Доступ:** Все страницы кроме Статистики

## Запуск системы

### 1. Backend

```bash
cd /Users/igorzolotyh/RAG/documentation/backend

# Активировать виртуальное окружение
source venv/bin/activate

# Запустить сервер
python3 main.py
```

Сервер будет доступен на http://localhost:8000
Swagger UI: http://localhost:8000/docs

### 2. Frontend

```bash
cd /Users/igorzolotyh/RAG/documentation/react-app

# Запустить React приложение
npm start
```

Приложение откроется на http://localhost:3000

## Особенности реализации

### Безопасность

1. **Хеширование паролей:** Используется SHA-256 через passlib
2. **JWT токены:** Срок действия 24 часа
3. **HTTPS-ready:** Можно легко добавить SSL сертификат
4. **CORS:** Настроен для работы с frontend

### Ролевая модель

- Роли хранятся в отдельной таблице
- Связь user → role через Foreign Key
- Легко расширяется (можно добавить новые роли)
- Проверка прав на уровне backend и frontend

### Пользовательский опыт

- Автоматический редирект неавторизованных
- Сохранение сессии после перезагрузки
- Показ email и роли в sidebar
- Скрытие админских функций для обычных пользователей
- Красивые страницы входа/регистрации с анимациями

## Возможные улучшения

1. **Восстановление пароля** через email
2. **Refresh tokens** для продления сессии
3. **Rate limiting** для защиты от брутфорса
4. **2FA** для повышенной безопасности
5. **Аудит логи** действий пользователей
6. **Управление пользователями** для админов
7. **Подтверждение email** при регистрации

## Troubleshooting

### Ошибка "Could not validate credentials"
- Проверьте, что токен актуален (не истек)
- Проверьте формат заголовка: `Authorization: Bearer <token>`

### Ошибка "Not enough permissions"
- Убедитесь, что у пользователя правильная роль
- Проверьте роль через `GET /auth/me`

### Redirect loop на /login
- Очистите localStorage: `localStorage.clear()`
- Убедитесь, что backend запущен

### CORS ошибки
- Убедитесь, что backend настроен на `allow_origins=["*"]`
- Проверьте, что используете правильные URL

## Миграции

Создание новой миграции:
```bash
cd /Users/igorzolotyh/RAG/documentation/backend
source venv/bin/activate
alembic revision --autogenerate -m "Description"
```

Применение миграций:
```bash
alembic upgrade head
```

Откат миграции:
```bash
alembic downgrade -1
```
