// import ExpandableBlock from '../components/ExpandableBlock';

// const Api = () => (
//   <section id="api" className="fade-in">
//     <h2>API</h2>
//     <p>Система предоставляет REST API для интеграции и автоматизации:</p>
//     <div>
//       <ExpandableBlock title={<h4>POST <mark>/query</mark> </h4>}>
//         <p>Эндпоинт для введения вопроса.</p>
//         <p>Возвращает сгенерированный ответ и тексты, которые были использованы в качестве контекста.</p>
//         <p>📤 Формат запроса:</p>
//         <pre className='code-block'>{`{
//   "question": "..."
// }`}</pre>

//         <p>📥 Формат ответа:</p>
//         <pre className='code-block'>{`{
//   "answer": "...",
//   "texts": [
//     {
//       ...
//     },
//     ...
//   ]
// }`}</pre>
//       </ExpandableBlock>    
//     </div>
//     <ExpandableBlock title={<h4>POST <mark>/upload-files</mark> </h4>}>
//       <p>Эндпоинт для загрузки файлов для дальнейшого индексирования</p>

//     </ExpandableBlock> 
//   </section>
// );

// export default Api;

import SwaggerUI from "swagger-ui-react";
import "swagger-ui-react/swagger-ui.css";
import usePageTracking from '../hooks/usePageTracking';
import './Api.css';

const Api = () => {
  usePageTracking(4);

  return (
    <section id="api" className="api-section fade-in">
      <div className="api-header">
        <h1>📚 API Документация</h1>
        <p className="api-description">
          Интерактивная документация REST API с возможностью тестирования эндпоинтов
        </p>
        <div className="api-info-cards">
          <div className="info-card">
            <span className="card-icon">🔗</span>
            <div className="card-content">
              <h3>Base URL</h3>
              <code>http://localhost:8000</code>
            </div>
          </div>
          <div className="info-card">
            <span className="card-icon">🔐</span>
            <div className="card-content">
              <h3>Авторизация</h3>
              <code>Bearer Token</code>
            </div>
          </div>
          <div className="info-card">
            <span className="card-icon">📄</span>
            <div className="card-content">
              <h3>Формат</h3>
              <code>JSON</code>
            </div>
          </div>
        </div>
      </div>

      <div className="swagger-container">
        <SwaggerUI
          url="http://127.0.0.1:8000/openapi.json"
          docExpansion="list"
          defaultModelsExpandDepth={1}
          displayRequestDuration={true}
        />
      </div>
    </section>
  );
};

export default Api;

