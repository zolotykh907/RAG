import React, { useState } from 'react';

const Settings = () => {
  const [settings, setSettings] = useState({
    showSources: true,
    autoScroll: true,
  });

  const handleChange = (e) => {
    const { id, checked } = e.target;
    setSettings((prev) => ({ ...prev, [id]: checked }));
    // Сохраняйте в localStorage, если нужно
  };

  return (
    <div className="sidebar-section">
      <h3><i className="fas fa-cog"></i> Настройки</h3>
      <div className="settings">
        <label className="setting-item">
          <input type="checkbox" id="showSources" checked={settings.showSources} onChange={handleChange} />
          <span>Показывать источники</span>
        </label>
        <label className="setting-item">
          <input type="checkbox" id="autoScroll" checked={settings.autoScroll} onChange={handleChange} />
          <span>Автопрокрутка</span>
        </label>
      </div>
    </div>
  );
};

export default Settings;