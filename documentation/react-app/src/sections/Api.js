import React from 'react';

const Api = () => (
  <section id="api" className="fade-in">
    <h2>API</h2>
    <p>Система предоставляет REST API для интеграции и автоматизации:</p>
    <ul>
      <li><b>POST /query</b> — получить ответ на вопрос</li>
      <li><b>POST /upload-files</b> — загрузить и проиндексировать файлы</li>
      <li><b>GET /docs</b> — интерактивная документация Swagger</li>
    </ul>
  </section>
);

export default Api;
