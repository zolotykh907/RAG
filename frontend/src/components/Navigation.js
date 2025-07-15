import React, { useState } from 'react';

const Navigation = ({ onTabChange }) => {
  const [activeTab, setActiveTab] = useState('chat');

  const handleTabClick = (tab) => {
    setActiveTab(tab);
    onTabChange(tab);
  };

  return (
    <nav className="config-nav">
      <a
        href="#"
        className={activeTab === 'chat' ? 'active' : ''}
        onClick={() => handleTabClick('chat')}
      >
        Чат
      </a>
      <a
        href="#"
        className={activeTab === 'config' ? 'active' : ''}
        onClick={() => handleTabClick('config')}
      >
        Конфигурация
      </a>
      <a
        href="#"
        className={activeTab === 'upload' ? 'active' : ''}
        onClick={() => handleTabClick('upload')}
      >
        Индексирование
      </a>
    </nav>
  );
};

export default Navigation;