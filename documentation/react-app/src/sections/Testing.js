import usePageTracking from '../hooks/usePageTracking';

const Testing = () => {
  usePageTracking(3); // ID страницы "Заключение"

  return (
  <section id="testing" className="fade-in">
    <h2>Тестирование</h2>
    <ul>
      <li className="base">Покрытие unit-тестами ключевых компонентов</li>
      <li className="base">Интеграционные тесты пайплайна Q&A</li>
      <li className="base">Проверка доступности API и корректности ответов</li>
      <li className="base">Использование <code>pytest</code> для запуска тестов</li>
    </ul>
  </section>
  );
};

export default Testing;
