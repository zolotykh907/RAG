import React from 'react';

const ConfigButtons = ({
  onSubmit,
  onReset,
  onReload,
  isLoading,
  selectedService,
}) => {
  const handleReload = async () => {
    try {
      onReload(true);
      const res = await fetch(`http://localhost:8000/reload?service=${selectedService}`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Ошибка перезагрузки');
      alert('Сервис перезапущен');
    } catch (e) {
      alert('Ошибка при перезагрузке сервиса');
      console.error(e);
    } finally {
      onReload(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onLoadingChange(true); // Устанавливаем состояние загрузки
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
      .catch(() => setStatus('❌ Ошибка сохранения'))
      .finally(() => onLoadingChange(false)); // Снимаем состояние загрузки
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

  const handleReset = () => {
    setConfig({});
    setStatus('');
  };

  return (
    <div className='sidebar'>
        <div className="sidebar-section">
            <div className="config-buttons">
                    <button type="submit" className="bg-primary text-white p-0.75rem rounded-lg">
                    <div className="config-button">
                    Сохранить
                    </div>
                    </button>
                    <button
                    type="button"
                    className="reset-btn bg-surface-light text-text-primary p-0.75rem rounded-lg"
                    onClick={handleReset}
                    >
                    Сбросить
                    </button>
                    <button
                    type="button"
                    className="reload-btn bg-surface-light text-text-primary p-0.75rem rounded-lg"
                    onClick={async () => {
                        try {
                        onLoadingChange(true);
                        const res = await fetch(`http://localhost:8000/reload?service=${selectedService}`, {
                            method: 'POST',
                        });
                        if (!res.ok) throw new Error('Ошибка перезагрузки');
                        alert('Сервис перезапущен');
                        } catch (e) {
                        alert('Ошибка при перезагрузке сервиса');
                        console.error(e);
                        } finally {
                        onLoadingChange(false);
                        }
                    }}
                    >
                    Перезапустить сервис
                    </button>
                </div>
            </div>  
        </div>
  );
};

export default ConfigButtons;
