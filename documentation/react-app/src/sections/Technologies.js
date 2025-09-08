import React from 'react';

const Technologies = () => (
  <section id="technologies" className="fade-in">
    <h2>Используемые технологии</h2>

    <h3>Backend</h3>
    <div className="tech-stack">
      <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white&logoWidth=40" alt="Python" height="30" />
      <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white&logoWidth=40" alt="FastAPI" height="30" />
      <img src="https://img.shields.io/badge/LangChain-00A67D?logo=chainlink&logoColor=white&logoWidth=40" alt="LangChain" height="30" />
      <img src="https://img.shields.io/badge/FAISS-00C4CC?logo=facebook&logoColor=white&logoWidth=40" alt="FAISS" height="30" />
      <img src="https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white&logoWidth=40" alt="Redis" height="30" />
      <img src="https://img.shields.io/badge/OCR-Tesseract-FF9900?logo=tesseract&logoColor=white&logoWidth=40" alt="OCR Tesseract" height="30" />
      <img src="https://img.shields.io/badge/Llama3-FF6600?logo=meta&logoColor=white&logoWidth=40" alt="Llama3" height="30" />
    </div>

    <h3>Frontend</h3>
    <div className="tech-stack">
      <img src="https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=white&logoWidth=40" alt="React" height="30" />
      <img src="https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white&logoWidth=40" alt="CSS3" height="30" />
      <img src="https://img.shields.io/badge/Axios-5A29E4?logo=axios&logoColor=white&logoWidth=40" alt="Axios" height="30" />
      <img src="https://img.shields.io/badge/React%20Router-CA4245?logo=reactrouter&logoColor=white&logoWidth=40" alt="React Router" height="30" />
    </div>

    <h3>Развертывание</h3>
    <div className="tech-stack">
      <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white&logoWidth=40" alt="Docker" height="30" />
      <img src="https://img.shields.io/badge/Uvicorn-000000?logo=uvicorn&logoColor=white&logoWidth=40" alt="Uvicorn" height="30" />
    </div>

    <h3>Модели и алгоритмы</h3>
    <ul>
      <li><strong>LLM:</strong> Llama3 (8b) - языковая модель с поддержкой русского языка</li>
      <li><strong>Эмбеддинги:</strong> sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2</li>
      <li><strong>Векторный поиск:</strong> FAISS для быстрого поиска похожих векторов</li>
      <li><strong>OCR:</strong> Tesseract для извлечения текста из изображений</li>
    </ul>
  </section>
);

export default Technologies;
