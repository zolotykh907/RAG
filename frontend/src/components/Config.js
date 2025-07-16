import React from 'react';

const Config = ({ config, setConfig, status, setStatus, isLoading, onChange, onSubmit, selectedService }) => {
  const renderFields = (obj, path = []) => {
    return Object.entries(obj).map(([key, value]) => {
      const currentPath = [...path, key];
      const label = currentPath.join('.');

      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        return (
          <details key={label} className="field mb-4">
            <summary className="cursor-pointer text-lg font-semibold text-primary bg-surface-light p-2 rounded-lg mb-2">
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
        const inputElement = key === 'prompt_template' ? (
          <textarea
            className="w-full p-1rem border border-border rounded-lg focus:border-primary transition-all duration-200"
            rows={6}
            value={value || ''}
            onChange={(e) => onChange(currentPath, e.target.value)}
          />
        ) : (
          <input
            type="text"
            className="w-full p-1rem border border-border rounded-lg focus:border-primary transition-all duration-200"
            value={Array.isArray(value) ? value.join(', ') : value || ''}
            onChange={(e) => onChange(currentPath, e.target.value)}
          />
        );

        return (
          <div key={label} className="field mb-2">
            <label className="block text-sm font-medium text-text-secondary mb-1">
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

  return (
    <div className="config-container">
      <div className="chat-messages">
        <div className="message system">
          <div className="message-content">
            <h2>⚙️ Настройки конфигурации - {selectedService}</h2>
          </div>
        </div>
        <form onSubmit={onSubmit} className="p-1.5rem">
          {renderFields(config)}
        </form>
      </div>
    </div>
  );
};

export default Config;