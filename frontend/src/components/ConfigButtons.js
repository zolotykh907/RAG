import React from 'react';

const ConfigButtons = ({
  onReset,
  onReload,
  isLoading,
  selectedService,
  onSave
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

  return (
    <div className="sidebar-section">
      <div className="config-buttons mt-4 flex gap-2">
        <button
          type="button"
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition"
          disabled={isLoading}
          onClick={onSave}
        >
          💾 Сохранить
        </button>

        <button
          type="button"
          className="bg-gray-300 text-black px-4 py-2 rounded-lg hover:bg-gray-400"
          onClick={onReset}
          disabled={isLoading}
        >
          Сбросить
        </button>

        <button
          type="button"
          className="bg-yellow-400 text-black px-4 py-2 rounded-lg hover:bg-yellow-500"
          onClick={handleReload}
          disabled={isLoading}
        >
          🔄 Перезапустить
        </button>
      </div>
    </div>
  );
};

export default ConfigButtons;