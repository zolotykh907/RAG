import React, { useState } from 'react';
import { Search, Send, MessageSquare, FileText, Copy, Check } from 'lucide-react';
import axios from 'axios';

const QueryInterface = () => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post('/query', {
        question: question.trim()
      });

      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка при выполнении запроса');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Ошибка копирования:', err);
    }
  };

  const exampleQuestions = [
    "Какая информация содержится в документах о проекте?",
    "Что говорится о технологиях в документах?",
    "Какие основные темы обсуждаются в материалах?",
    "Есть ли информация о датах или событиях?"
  ];

  return (
    <div className="space-y-6">
      {/* Форма запроса */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <Search className="h-5 w-5 mr-2" />
          Выполнение RAG запросов
        </h2>
        
        <p className="text-gray-600 mb-6">
          Задайте вопрос к индексированным документам. Система найдет релевантную информацию и сгенерирует ответ.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
              Ваш вопрос
            </label>
            <textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Например: Какая информация содержится в документах о проекте?"
              className="input-field min-h-[120px] resize-y"
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="btn-primary w-full flex items-center justify-center space-x-2"
          >
            {loading ? (
              <>
                <div className="loading-spinner"></div>
                <span>Поиск ответа...</span>
              </>
            ) : (
              <>
                <Send className="h-4 w-4" />
                <span>Найти ответ</span>
              </>
            )}
          </button>
        </form>

        {/* Примеры вопросов */}
        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Примеры вопросов:</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {exampleQuestions.map((example, index) => (
              <button
                key={index}
                onClick={() => setQuestion(example)}
                className="text-left p-3 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors duration-200"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Ошибка */}
      {error && (
        <div className="card border-red-200 bg-red-50">
          <div className="flex items-center space-x-2 text-red-800">
            <MessageSquare className="h-5 w-5" />
            <span className="font-medium">Ошибка:</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Результат */}
      {result && (
        <div className="space-y-4">
          {/* Ответ */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <MessageSquare className="h-5 w-5 mr-2" />
                Ответ
              </h3>
              <button
                onClick={() => copyToClipboard(result.answer)}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
                title="Копировать ответ"
              >
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </button>
            </div>
            <div className="prose prose-sm max-w-none">
              <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                {result.answer}
              </p>
            </div>
          </div>

          {/* Источники */}
          {result.texts && result.texts.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <FileText className="h-5 w-5 mr-2" />
                Использованные источники ({result.texts.length})
              </h3>
              <div className="space-y-3">
                {result.texts.map((text, index) => (
                  <div
                    key={index}
                    className="p-4 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="text-sm text-gray-500 mb-2">
                          Источник {index + 1}
                        </div>
                        <p className="text-gray-800 text-sm leading-relaxed">
                          {text.length > 300 ? `${text.substring(0, 300)}...` : text}
                        </p>
                      </div>
                      <button
                        onClick={() => copyToClipboard(text)}
                        className="ml-2 text-gray-400 hover:text-gray-600 transition-colors duration-200"
                        title="Копировать текст"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default QueryInterface; 