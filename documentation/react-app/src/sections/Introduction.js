import usePageTracking from '../hooks/usePageTracking';

const Introduction = () => {
  usePageTracking(1); // ID страницы "Введение"

  return (
  <section id="introduction" className="fade-in">
    <h1 className="fade-in">RAG Q&A System</h1>

    <div style={{ textAlign: "center", margin: "20px 0" }}>
      <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white&logoWidth=40" alt="Python" height="30" />
      <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white&logoWidth=40" alt="Docker" height="30" />
      <img src="https://img.shields.io/badge/Llama3-FF6600?logo=meta&logoColor=white&logoWidth=40" alt="Llama3" height="30" />
      <img src="https://img.shields.io/badge/LangChain-00A67D?logo=chainlink&logoColor=white&logoWidth=40" alt="LangChain" height="30" />
      <img src="https://img.shields.io/badge/FAISS-00C4CC?logo=facebook&logoColor=white&logoWidth=40" alt="FAISS" height="30" />
      <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white&logoWidth=40" alt="FastAPI" height="30" />
      <img src="https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white&logoWidth=40" alt="Redis" height="30" />
      <img src="https://img.shields.io/badge/OCR-Tesseract-FF9900?logo=tesseract&logoColor=white&logoWidth=40" alt="OCR Tesseract" height="30" />
      <img src="https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=white&logoWidth=40" alt="React" height="30" />
    </div>

    <div className="image-container fade-in">
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
        <img src="/web_interface.png" alt="Интерфейс RAG системы" width="1000" />
        <p className="image-caption" style={{ textAlign: "center", width: "100%" }}>
          Веб-интерфейс RAG системы
        </p>
      </div>
    </div>

    <h2>Введение</h2>
    <p>Q&A сервис на основе RAG архитектуры, с использованием OCR.</p>
    <p>Система разработана как набор взаимодействующих микросервисов, готовых к контейнеризации и развертыванию в различных средах.</p>
    <p>RAG система реализует следующий пайплайн обработки запросов:</p>
    <ol>
      <li><strong>Прием запроса</strong> — пользователь отправляет текстовый вопрос через веб-интерфейс или API</li>
      <li><strong>Поиск релевантной информации</strong> — система находит наиболее подходящие фрагменты из базы знаний</li>
      <li><strong>Генерация ответа</strong> — LLM создает полный ответ на основе найденного контекста</li>
      <li><strong>Кэширование</strong> — часто задаваемые вопросы сохраняются в Redis для ускорения ответов</li>
    </ol>
  </section>
  );
};

export default Introduction;
