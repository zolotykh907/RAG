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

// Иконки для секций
const SECTION_ICONS = {
  llm: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
    </svg>
  ),
  embeddings: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10"></circle>
      <line x1="2" y1="12" x2="22" y2="12"></line>
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
    </svg>
  ),
  qdrant: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
    </svg>
  ),
  prompts: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
      <polyline points="14 2 14 8 20 8"></polyline>
      <line x1="16" y1="13" x2="8" y2="13"></line>
      <line x1="16" y1="17" x2="8" y2="17"></line>
    </svg>
  )
};

// Компонент настроек системы
function Settings() {
  const [activeService, setActiveService] = useState('query');
  const [config, setConfig] = useState(null);
  const [originalConfig, setOriginalConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [collapsedSections, setCollapsedSections] = useState({});

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
    setCollapsedSections({});
  }, [loadConfig]);

  const toggleSection = (key) => {
    setCollapsedSections(prev => ({ ...prev, [key]: !prev[key] }));
  };

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

  // Сброс отдельного поля
  const handleResetField = (fullPath) => {
    const keys = fullPath.split('.');
    let originalValue = originalConfig;
    for (const key of keys) {
      originalValue = originalValue?.[key];
    }
    handleChange(fullPath, originalValue);
  };

  // Проверка наличия изменений
  const hasChanges = JSON.stringify(config) !== JSON.stringify(originalConfig);

  // Проверка, изменено ли конкретное поле
  const isFieldChanged = (fullPath) => {
    if (!config || !originalConfig) return false;
    const keys = fullPath.split('.');
    let current = config;
    let original = originalConfig;
    for (const key of keys) {
      current = current?.[key];
      original = original?.[key];
    }
    return JSON.stringify(current) !== JSON.stringify(original);
  };

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
      const isCollapsed = collapsedSections[fullPath];
      const icon = SECTION_ICONS[key] || null;

      return (
        <div key={fullPath} className={`config-section ${isCollapsed ? 'collapsed' : ''}`}>
          <button className="config-section-header" onClick={() => toggleSection(fullPath)}>
            <div className="section-header-left">
              {icon && <span className="section-icon">{icon}</span>}
              <h4 className="config-section-title">{key}</h4>
            </div>
            <svg className="section-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>
          <div className="config-section-body">
            <div className="config-section-content">
              {Object.entries(value).map(([k, v]) => renderConfigField(k, v, fullPath))}
            </div>
          </div>
        </div>
      );
    }

    // Определяем, нужен ли textarea (для длинных строк или строк с переносами)
    const isLongText = typeof value === 'string' && (value.length > 100 || value.includes('\n'));
    const description = getFieldDescription(fullPath);
    const changed = isFieldChanged(fullPath);

    return (
      <div key={fullPath} className={`config-field ${isLongText ? 'config-field-long' : ''} ${changed ? 'config-field-changed' : ''}`}>
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
        <div className="config-input-wrapper">
          {typeof value === 'boolean' ? (
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={value}
                onChange={(e) => handleChange(fullPath, e.target.checked)}
              />
              <span className="toggle-slider"></span>
              <span className="toggle-label">{value ? 'Вкл' : 'Выкл'}</span>
            </label>
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
          {changed && (
            <button
              className="field-reset-btn"
              onClick={() => handleResetField(fullPath)}
              title="Сбросить значение"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="1 4 1 10 7 10"></polyline>
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
              </svg>
            </button>
          )}
        </div>
      </div>
    );
  };

  // Разделяем top-level поля и секции (объекты)
  const renderConfigForm = () => {
    if (!config) return null;

    const topLevelFields = [];
    const sections = [];

    for (const [key, value] of Object.entries(config)) {
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        sections.push([key, value]);
      } else {
        topLevelFields.push([key, value]);
      }
    }

    return (
      <div className="config-form">
        {topLevelFields.length > 0 && (
          <div className="config-section config-section-general">
            <div className="config-section-header config-section-header-static">
              <div className="section-header-left">
                <span className="section-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                  </svg>
                </span>
                <h4 className="config-section-title">Основные</h4>
              </div>
            </div>
            <div className="config-section-body config-section-body-open">
              <div className="config-section-content">
                {topLevelFields.map(([key, value]) => renderConfigField(key, value))}
              </div>
            </div>
          </div>
        )}
        {sections.map(([key, value]) => renderConfigField(key, value))}
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
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.35-4.35"></path>
            </svg>
            <span>Query Service</span>
          </button>
          <button
            className={`service-tab ${activeService === 'indexing' ? 'active' : ''}`}
            onClick={() => setActiveService('indexing')}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
              <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
              <line x1="6" y1="6" x2="6.01" y2="6"></line>
              <line x1="6" y1="18" x2="6.01" y2="18"></line>
            </svg>
            <span>Indexing Service</span>
          </button>
        </div>

        {loading ? (
          <div className="loading-state">
            <div className="spinner-large"></div>
            <p>Загрузка конфигурации...</p>
          </div>
        ) : config ? (
          <div className="config-content">
            {renderConfigForm()}

            {message && (
              <div className={`message-box message-${message.type}`}>
                {message.type === 'success' ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                ) : (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                  </svg>
                )}
                {message.text}
              </div>
            )}
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

      {/* Floating action buttons */}
      {config && hasChanges && (
        <div className="floating-actions">
          <button
            onClick={handleSave}
            disabled={saving}
            className="floating-btn floating-btn-primary"
          >
            {saving ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="spinner">
                <circle cx="12" cy="12" r="10"></circle>
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            )}
            <span className="floating-label">{saving ? 'Сохранение' : 'Сохранить'}</span>
          </button>
          <button
            onClick={handleReset}
            disabled={saving}
            className="floating-btn floating-btn-secondary"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="1 4 1 10 7 10"></polyline>
              <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
            </svg>
            <span className="floating-label">Сбросить</span>
          </button>
        </div>
      )}
    </div>
  );
}

export default Settings;
