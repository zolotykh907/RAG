import ExpandableBlock from '../components/ExpandableBlock';

const Api = () => (
  <section id="api" className="fade-in">
    <h2>API</h2>
    <p>Система предоставляет REST API для интеграции и автоматизации:</p>
    <div>
      <ExpandableBlock title={<h4>POST <mark>/query</mark> </h4>}>
        <p>Эндпоинт для введения вопроса.</p>
        <p>Возвращает сгенерированный ответ и тексты, которые были использованы в качестве контекста.</p>
        <p>📤 Формат запроса:</p>
        <pre className='code-block'>{`{
  "question": "..."
}`}</pre>

        <p>📥 Формат ответа:</p>
        <pre className='code-block'>{`{
  "answer": "...",
  "texts": [
    {
      ...
    },
    ...
  ]
}`}</pre>
      </ExpandableBlock>    
    </div>
    <ExpandableBlock title={<h4>POST <mark>/upload-files</mark> </h4>}>
      <p>Эндпоинт для загрузки файлов для дальнейшого индексирования</p>

    </ExpandableBlock> 
  </section>
);

export default Api;
