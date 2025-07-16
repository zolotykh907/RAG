import React from 'react';

const Settings = ({ autoScroll, onToggleAutoScroll }) => {
  const [settings, setSettings] = React.useState({
    showSources: true,
  });

  const handleChange = (e) => {
    const { id, checked } = e.target;
    if (id === 'autoScroll') {
      onToggleAutoScroll();
    } else {
      setSettings((prev) => ({ ...prev, [id]: checked }));
    }
  };

  return (
    <div className="sidebar-section">
      <h3><i className="fas fa-cog"></i> Настройки</h3>
      <div className="settings">
        <label className="setting-item">
          <input type="checkbox" id="autoScroll" checked={autoScroll} onChange={handleChange} />
          <span>Автопрокрутка</span>
        </label>
      </div>
    </div>
  );
};

export default Settings;