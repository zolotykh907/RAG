import { useState, useEffect, useCallback } from 'react';
import apiService from '../services/api';
import Tooltip from './Tooltip';
import './Settings.css';

// Описания для настроек
const CONFIG_DESCRIPTIONS = {
  query: {
    'top_k': 'Количество наиболее релевантных фрагментов текста, извлекаемых из базы данных для ответа',
    'chunk_size': 'Размер одного фрагмента текста в символах при разбиении документа',
    'chunk_overlap': 'Количество символов перекрытия между соседними фрагментами для сохранения контекста',
    'model_name': 'Название языковой модели для генерации ответов (например, llama3.2, gpt-4)',
    'temperature': 'Креативность ответов модели (0 = точные, 1 = креативные)',
    'max_tokens': 'Максимальная длина генерируемого ответа в токенах',
    'collection_name': 'Название коллекции в векторной базе данных Qdrant',
    'llm.provider': 'Провайдер LLM: ollama (локальный) или openai (облачный)',
    'llm.base_url': 'URL API для запросов к языковой модели',
    'llm.model_name': 'Название модели для генерации ответов',
    'llm.temperature': 'Параметр креативности ответов (0.0-1.0)',
    'llm.max_tokens': 'Максимальная длина ответа в токенах',
    'embeddings.provider': 'Провайдер для векторизации текста: sentence-transformers или openai',
    'embeddings.model_name': 'Название модели для создания векторных представлений текста',
    'embeddings.device': 'Устройство для вычислений: cpu, cuda (GPU) или mps (Apple Silicon)',
    'qdrant.url': 'URL сервера векторной базы данных Qdrant',
    'qdrant.collection_name': 'Имя коллекции для хранения векторов документов',
    'prompts.system_prompt': 'Системная инструкция для модели, определяющая её роль и поведение',
    'prompts.context_template': 'Шаблон для форматирования контекста из найденных фрагментов',
    'prompts.query_template': 'Шаблон для форматирования финального запроса к модели'
  },
  indexing: {
    'chunk_size': 'Размер фрагмента текста в символах при индексации документа',
    'chunk_overlap': 'Количество символов перекрытия между фрагментами',
    'collection_name': 'Название коллекции в Qdrant для хранения индексированных документов',
    'embeddings.provider': 'Провайдер для векторизации: sentence-transformers или openai',
    'embeddings.model_name': 'Модель для создания векторных представлений текста',
    'embeddings.device': 'Устройство для вычислений: cpu, cuda или mps',
    'qdrant.url': 'URL сервера Qdrant для хранения векторов',
    'qdrant.collection_name': 'Коллекция для индексированных документов'
  }
};

// Компонент настроек системы
function Settings() {
  const [activeService, setActiveService] = useState('query');
  const [config, setConfig] = useState(null);
  const [originalConfig, setOriginalConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  const loadConfig = useCallback(async () => {
    setLoading(true);
    setMessage(null);
    try {
      const data = await apiService.getConfig(activeService);
      setConfig(data);
      setOriginalConfig(JSON.parse(JSON.stringify(data))); // Deep copy
    } catch (error) {
      setMessage({
        type: 'error',
        text: `Ошибка загрузки конфигурации: ${error.message}`
      });
    } finally {
      setLoading(false);
    }
  }, [activeService]);

  // Загрузка конфигурации при смене сервиса
  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  // Обработка изменения значения в конфигурации
  const handleChange = (path, value) => {
    const newConfig = { ...config };
    const keys = path.split('.');
    let current = newConfig;

    for (let i = 0; i < keys.length - 1; i++) {
      current = current[keys[i]];
    }

    // Конвертация типов
    const lastKey = keys[keys.length - 1];
    if (typeof originalConfig !== 'undefined') {
      let originalValue = originalConfig;
      keys.forEach(key => {
        originalValue = originalValue?.[key];
      });

      if (typeof originalValue === 'number') {
        current[lastKey] = Number(value);
      } else if (typeof originalValue === 'boolean') {
        current[lastKey] = value === 'true' || value === true;
      } else {
        current[lastKey] = value;
      }
    } else {
      current[lastKey] = value;
    }

    setConfig(newConfig);
  };

  // Сохранение конфигурации
  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      await apiService.updateConfig(activeService, config);
      await apiService.reloadService(activeService);
      setMessage({
        type: 'success',
        text: 'Конфигурация успешно сохранена и применена'
      });
      setOriginalConfig(JSON.parse(JSON.stringify(config)));
    } catch (error) {
      setMessage({
        type: 'error',
        text: `Ошибка сохранения: ${error.message}`
      });
    } finally {
      setSaving(false);
    }
  };

  // Сброс изменений
  const handleReset = () => {
    setConfig(JSON.parse(JSON.stringify(originalConfig)));
    setMessage(null);
  };

  // Проверка наличия изменений
  const hasChanges = JSON.stringify(config) !== JSON.stringify(originalConfig);

  // Получить описание для поля
  const getFieldDescription = (fullPath) => {
    const descriptions = CONFIG_DESCRIPTIONS[activeService];
    return descriptions?.[fullPath] || null;
  };

  // Рекурсивный рендеринг полей конфигурации
  const renderConfigField = (key, value, path = '') => {
    const fullPath = path ? `${path}.${key}` : key;

    if (value === null || value === undefined) {
      return null;
    }

    if (typeof value === 'object' && !Array.isArray(value)) {
      return (
        <div key={fullPath} className="config-section">
          <h4 className="config-section-title">{key}</h4>
          <div className="config-section-content">
            {Object.entries(value).map(([k, v]) => renderConfigField(k, v, fullPath))}
          </div>
        </div>
      );
    }

    // Определяем, нужен ли textarea (для длинных строк или строк с переносами)
    const isLongText = typeof value === 'string' && (value.length > 100 || value.includes('\n'));
    const description = getFieldDescription(fullPath);

    return (
      <div key={fullPath} className={`config-field ${isLongText ? 'config-field-long' : ''}`}>
        <label className="config-label">
          {key}
          {description && (
            <Tooltip text={description}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="info-icon">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
              </svg>
            </Tooltip>
          )}
        </label>
        {typeof value === 'boolean' ? (
          <select
            value={value.toString()}
            onChange={(e) => handleChange(fullPath, e.target.value)}
            className="config-input config-select"
          >
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        ) : typeof value === 'number' ? (
          <input
            type="number"
            value={value}
            onChange={(e) => handleChange(fullPath, e.target.value)}
            className="config-input"
          />
        ) : isLongText ? (
          <textarea
            value={value}
            onChange={(e) => handleChange(fullPath, e.target.value)}
            className="config-input config-textarea"
            rows={Math.min(Math.max(value.split('\n').length, 5), 20)}
          />
        ) : (
          <input
            type="text"
            value={value}
            onChange={(e) => handleChange(fullPath, e.target.value)}
            className="config-input"
          />
        )}
      </div>
    );
  };

  return (
    <div className="settings-container">
      <div className="settings-wrapper">
        <div className="settings-header">
          <h2>Настройки системы</h2>
          <p>Управление конфигурацией RAG системы</p>
        </div>

        <div className="service-tabs">
          <button
            className={`service-tab ${activeService === 'query' ? 'active' : ''}`}
            onClick={() => setActiveService('query')}
          >
            Query Service
          </button>
          <button
            className={`service-tab ${activeService === 'indexing' ? 'active' : ''}`}
            onClick={() => setActiveService('indexing')}
          >
            Indexing Service
          </button>
        </div>

        {loading ? (
          <div className="loading-state">
            <div className="spinner-large"></div>
            <p>Загрузка конфигурации...</p>
          </div>
        ) : config ? (
          <div className="config-content">
            <div className="config-form">
              {Object.entries(config).map(([key, value]) => renderConfigField(key, value))}
            </div>

            {message && (
              <div className={`message-box message-${message.type}`}>
                {message.text}
              </div>
            )}

            <div className="config-actions">
              <button
                onClick={handleReset}
                disabled={!hasChanges || saving}
                className="btn-secondary"
              >
                Сбросить
              </button>
              <button
                onClick={handleSave}
                disabled={!hasChanges || saving}
                className="btn-primary"
              >
                {saving ? 'Сохранение...' : 'Сохранить и применить'}
              </button>
            </div>
          </div>
        ) : (
          <div className="error-state">
            <p>Не удалось загрузить конфигурацию</p>
            <button onClick={loadConfig} className="btn-secondary">
              Попробовать снова
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default Settings;
