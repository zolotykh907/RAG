// import CodeBlock from "../components/CodeBlock";

const Installation = () => (
  <section id="installation" className="fade-in">
    <h2>Установка</h2>

    <h3>1. Клонирование репозитория</h3>
    <pre className="code-block">{`
git clone https://github.com/zolotykh907/RAG.git
cd RAG
python3 -m venv .venv && source .venv/bin/activate
    `}</pre>

    <h3>2. Установка зависимостей</h3>
    <p><strong>Для индексации:</strong></p>
    <pre className="code-block">{`
pip install -r indexing/requirements.txt
    `}</pre>

    <p><strong>Для запросов:</strong></p>
    <pre className="code-block">{`
pip install -r query/requirements.txt
    `}</pre>

    <p><strong>Frontend (Node.js):</strong></p>
    <pre className="code-block">{`
cd frontend
npm install
    `}</pre>

    <h3>3. Запуск</h3>
    <p>Систему можно запустить локально или через Docker.</p>

    <h4>💻 Локально</h4>
    <p>Установка Ollama:</p>
    <pre className="code-block">{`
ollama pull llama3
ollama serve
    `}</pre>

    <h4>Варианты запуска:</h4>
    <p><strong>React + API:</strong></p>
    <pre className="code-block">{`
# Запуск API
python run_api.py

# В другом терминале запуск frontend
python run_frontend.py
    `}</pre>

    <p><strong>Отдельные компоненты:</strong></p>
    <pre className="code-block">{`
python indexing/run_indexing.py
uvicorn query.app:app --host 0.0.0.0 --port 8000
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && npm start
# или
python run_frontend.py
    `}</pre>

    <p><strong>Ручной запуск frontend:</strong></p>
    <pre className="code-block">{`
cd frontend
npm install
npm start
    `}</pre>

    <h4>🐳 Docker</h4>
    <pre className="code-block">{`
docker-compose up --build
    `}</pre>

    <h3>После запуска доступно:</h3>
    <ul>
      <li>🌐 React Frontend: <code>http://localhost:3000</code></li>
      <li>🔧 API Backend:
        <ul>
          <li><code>http://localhost:8000/query</code> — для запросов</li>
          <li><code>http://localhost:8000/upload-files</code> — для загрузки файлов</li>
        </ul>
      </li>
      <li>📖 Swagger UI: <code>http://localhost:8000/docs</code></li>
      <li>💻 CLI клиент: <code>python client.py</code></li>
    </ul>
  </section>
);

export default Installation;
