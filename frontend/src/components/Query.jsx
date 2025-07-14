import { useState } from 'react';
import axios from 'axios';

export default function Query() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError('');
    setAnswer('');
    setSources([]);

    try {
      const response = await axios.post('http://localhost:8000/query', {
        question: question.trim()
      });
      setAnswer(response.data.answer);
      setSources(response.data.texts || []);
    } catch (error) {
      console.error('Error:', error);
      setError(error.response?.data?.detail || 'Ошибка при выполнении запроса');
    } finally {
      setLoading(false);
    }
  };

  const exampleQuestions = [
    "Какая информация содержится в документах о проекте?",
    "Что говорится о технологиях в документах?",
    "Какие основные темы обсуждаются в материалах?"
  ];

  return (
    <div className="card">
      <h2>🔍 Выполнение RAG запросов</h2>
      <p style={{ color: '#666', marginBottom: '1.5rem' }}>
        Задайте вопрос к индексированным документам. Система найдет релевантную информацию и сгенерирует ответ.
      </p>
      
      <form onSubmit={handleSubmit}>
        <label htmlFor="question" style={{ fontWeight: '500', color: '#333' }}>
          Ваш вопрос:
        </label>
        <textarea
          id="question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Например: Какая информация содержится в документах о проекте?"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !question.trim()}>
          {loading ? (
            <div className="loading">
              <div className="spinner"></div>
              <span>Поиск ответа...</span>
            </div>
          ) : (
            '🔍 Найти ответ'
          )}
        </button>
      </form>

      {/* Примеры вопросов */}
      <div style={{ marginTop: '2rem' }}>
        <h4 style={{ color: '#667eea', marginBottom: '1rem' }}>Примеры вопросов:</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '0.5rem' }}>
          {exampleQuestions.map((example, index) => (
            <button
              key={index}
              onClick={() => setQuestion(example)}
              style={{
                background: 'none',
                border: '1px solid #e1e5e9',
                color: '#666',
                textAlign: 'left',
                padding: '0.75rem',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseOver={(e) => {
                e.target.style.background = '#f8f9fa';
                e.target.style.borderColor = '#667eea';
              }}
              onMouseOut={(e) => {
                e.target.style.background = 'none';
                e.target.style.borderColor = '#e1e5e9';
              }}
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {/* Ошибка */}
      {error && (
        <div className="message error">
          <strong>Ошибка:</strong> {error}
        </div>
      )}
      
      {/* Результаты */}
      {answer && (
        <div className="results">
          <h3>💡 Ответ:</h3>
          <p style={{ whiteSpace: 'pre-wrap' }}>{answer}</p>
          
          {sources.length > 0 && (
            <>
              <h4>📚 Использованные источники ({sources.length}):</h4>
              <ul>
                {sources.map((text, index) => (
                  <li key={index}>
                    <strong>Источник {index + 1}:</strong><br />
                    {text.length > 200 ? `${text.substring(0, 200)}...` : text}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}