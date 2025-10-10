const Architecture = () => (
  <section id="architecture" class="fade-in">
    <h2>Архитектура веб-приложения</h2>
    
    <div class="image-container">
        <img src="/shema.png" alt="Интерфейс RAG системы" width="1000" />
        <p class="image-caption">Веб-интерфейс RAG системы</p>
    </div>

    <p>Система включает в себя два интерфейса:</p>

    <h3>1. React Frontend</h3>
    <p>Современный React интерфейс с расширенной функциональностью:</p>
    <ul>
        <li className="base">Drag & Drop загрузка файлов</li>
        <li className="base">Интуитивный интерфейс запросов</li>
        <li className="base">Детальная настройка системы</li>
        <li className="base">Современный и Адаптивный дизайн с анимациями</li>
    </ul>
    <p><strong>Доступ:</strong> <a href="http://localhost:3000" class="my-link">http://localhost:3000</a></p>

    <h3>2. API Backend</h3>
    <p>FastAPI сервер с автоматической документацией:</p>
    <ul>
        <li className="base">REST API для интеграции</li>
        <li className="base">Интерактивная документация Swagger</li>
        <li className="base">Встроенная валидация данных</li>
    </ul>
    <p><strong>Доступ:</strong> <a href="http://localhost:8000" class="my-link">http://localhost:8000</a></p>
    <p><strong>Документация:</strong> <a href="http://localhost:8000/docs" class="my-link">http://localhost:8000/docs</a></p>
</section>
);

export default Architecture;
