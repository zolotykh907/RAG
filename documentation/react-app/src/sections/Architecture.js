import React from 'react';

const Architecture = () => (
  <section id="architecture" className="fade-in">
    <h2>Архитектура</h2>
    <div className="image-container fade-in">
      <img src={process.env.PUBLIC_URL + '/shema.png'} alt="Интерфейс RAG системы" width="1000" />
      <p className="image-caption">Веб-интерфейс RAG системы</p>
    </div>
    <p>Система построена на взаимодействии следующих компонентов:</p>
    <ul>
      <li>Frontend (React)</li>
      <li>API Backend (FastAPI)</li>
      <li>Сервис индексации и поиска (FAISS, LangChain)</li>
      <li>OCR сервис (Tesseract)</li>
      <li>Кэширование (Redis)</li>
      <li>LLM (Llama3)</li>
    </ul>
  </section>
);

export default Architecture;
