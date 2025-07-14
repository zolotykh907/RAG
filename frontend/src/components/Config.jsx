import React, { useEffect, useState } from 'react';

function Config() {
  const [config, setConfig] = useState({});
  const [status, setStatus] = useState('');
  const [selectedService, setSelectedService] = useState('query');

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const endpoint = `http://localhost:8000/config?service=${selectedService}`;
        const res = await fetch(endpoint);
        if (!res.ok) throw new Error('Ошибка сети');
        const data = await res.json();
        setConfig(data || {});
      } catch (err) {
        console.error(`Ошибка загрузки конфигурации для ${selectedService}`, err);
        setStatus("Ошибка загрузки");
      }
    };
    fetchConfig();
  }, [selectedService]);

  const renderFields = (obj, path = []) => {
    return Object.entries(obj).map(([key, value]) => {
      const currentPath = [...path, key];
      const label = currentPath.join('.');

      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        return (
          <details key={label} className="field mb-4">
            <summary className="cursor-pointer text-lg font-semibold text-gray-700 bg-white p-2 rounded-lg mb-2">
              {key}
              <span className="tooltip ml-2">
                <span className="tooltip-icon">?</span>
                <span className="tooltip-text">Нажмите, чтобы раскрыть {key}</span>
              </span>
            </summary>
            <div className="ml-4">{renderFields(value, currentPath)}</div>
          </details>
        );
      } else {
        let inputElement;

        if (key === 'prompt_template') {
          inputElement = (
            <textarea
              className="w-full p-0.75rem border rounded-lg focus:border-indigo-600 transition-all duration-200"
              rows={6}
              value={value || ''}
              onChange={(e) => handleChange(currentPath, e.target.value)}
            />
          );
        } else {
          inputElement = (
            <input
              type="text"
              className="w-full p-0.75rem border rounded-lg focus:border-indigo-600 transition-all duration-200"
              value={Array.isArray(value) ? value.join(', ') : (value || '')}
              onChange={(e) => handleChange(currentPath, e.target.value)}
            />
          );
        }

        return (
          <div key={label} className="field mb-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {label}
              <span className="tooltip">
                <span className="tooltip-icon">?</span>
                <span className="tooltip-text">Введите значение для {label}</span>
              </span>
            </label>
            {inputElement}
          </div>
        );
      }
    });
  };

  const handleChange = (path, value) => {
    setConfig((prevConfig) => {
      const newConfig = structuredClone(prevConfig || {});
      let obj = newConfig;
      for (let i = 0; i < path.length - 1; i++) {
        obj = obj[path[i]] = obj[path[i]] || {};
      }
      const lastKey = path[path.length - 1];
      const original = obj[lastKey];

      if (Array.isArray(original)) {
        obj[lastKey] = value.split(',').map((v) => v.trim());
      } else {
        const numValue = Number(value);
        if (!isNaN(numValue) && value.trim() !== '') {
          obj[lastKey] = numValue;
        } else {
          obj[lastKey] = value;
        }
      }

      return newConfig;
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const endpoint = `http://localhost:8000/config?service=${selectedService}`;
    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
      .then((res) => {
        if (!res.ok) throw new Error('Ошибка сохранения');
        return res.json();
      })
      .then(() => setStatus('✅ Конфигурация сохранена!'))
      .catch(() => setStatus('❌ Ошибка сохранения'));
  };

  const handleReset = () => {
    setConfig({});
    setStatus('');
  };

  return (
    <div className="app">
      <nav className="config-nav">
        <a
          href="#"
          className={selectedService === 'query' ? 'active' : ''}
          onClick={() => setSelectedService('query')}
        >
          Query
        </a>
        <a
          href="#"
          className={selectedService === 'indexing' ? 'active' : ''}
          onClick={() => setSelectedService('indexing')}
        >
          Indexing
        </a>
      </nav>
      <main>
        <div className="config-page">
          <h2>⚙️ Настройки конфигурации - {selectedService}</h2>
          {status && <div className={`message ${status.includes('Ошибка') ? 'error' : 'success'}`}>{status}</div>}
          <form onSubmit={handleSubmit}>
            {renderFields(config)}
            <div className="flex gap-4">
              <button type="submit">Сохранить</button>
              <button type="button" className="reset-btn" onClick={handleReset}>
                Сбросить
              </button>
              <button
                onClick={async () => {
                  try {
                    const res = await fetch(`http://localhost:8000/reload?service=${selectedService}`, {
                      method: 'POST',
                    });
                    if (!res.ok) throw new Error("Ошибка перезагрузки");
                    alert("Сервис перезапущен");
                  } catch (e) {
                    alert("Ошибка при перезагрузке сервиса");
                    console.error(e);
                  }
                }}
              >
                🔁 Перезапустить сервис
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}

export default Config;