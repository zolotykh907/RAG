import React, { useEffect, useState } from 'react';

function Config() {
  const [config, setConfig] = useState({});
  const [status, setStatus] = useState('');

  useEffect(() => {
    fetch('http://localhost:8000/config')
      .then((res) => res.json())
      .then((data) => setConfig(data))
      .catch((err) => {
        console.error("Ошибка загрузки конфигурации", err);
        setStatus("Ошибка загрузки");
      });
  }, []);

  const renderFields = (obj, path = []) => {
    return Object.entries(obj).map(([key, value]) => {
      const currentPath = [...path, key];
      const label = currentPath.join('.');

      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        return (
          <div key={label} className="border rounded-xl p-4 mb-4 bg-white shadow">
            <h3 className="text-lg font-semibold mb-2">{key}</h3>
            {renderFields(value, currentPath)}
          </div>
        );
      } else {
        let inputElement;

        if (key === 'prompt_template') {
          inputElement = (
            <textarea
              className="w-full p-2 border rounded-lg font-mono text-sm"
              rows={6}
              value={value}
              onChange={(e) => handleChange(currentPath, e.target.value)}
            />
          );
        } else {
          inputElement = (
            <input
              type="text"
              className="w-full p-2 border rounded-lg"
              value={Array.isArray(value) ? value.join(', ') : value}
              onChange={(e) => handleChange(currentPath, e.target.value)}
            />
          );
        }

        return (
          <div key={label} className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {label}
            </label>
            {inputElement}
          </div>
        );
      }
    });
  };

  const handleChange = (path, value) => {
    setConfig((prevConfig) => {
      const newConfig = structuredClone(prevConfig);
      let obj = newConfig;
      for (let i = 0; i < path.length - 1; i++) {
        obj = obj[path[i]];
      }
      const lastKey = path[path.length - 1];
      const original = obj[lastKey];

      if (Array.isArray(original)) {
        obj[lastKey] = value.split(',').map((v) => v.trim());
      } else {
        obj[lastKey] = value;
      }

      return newConfig;
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetch('http://localhost:8000/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    })
      .then((res) => res.json())
      .then(() => setStatus('✅ Конфигурация сохранена!'))
      .catch(() => setStatus('❌ Ошибка сохранения'));
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-bold mb-6">⚙️ Настройки конфигурации</h2>
      {status && <div className="mb-4 text-green-600 font-medium">{status}</div>}
      <form onSubmit={handleSubmit}>
        {renderFields(config)}
        <button
          type="submit"
          className="mt-4 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition"
        >
          💾 Сохранить
        </button>
      </form>
    </div>
  );
}

export default Config;
