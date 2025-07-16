import React, { useState, useEffect } from 'react';
import Stats from './Stats';
import Settings from './Settings';
import History from './History';

const Sidebar = ({ autoScroll, onToggleAutoScroll }) => {
  const [requestsToday, setRequestsToday] = useState(0);
  const [systemStatus, setSystemStatus] = useState('Онлайн');

  useEffect(() => {
    // Проверка статуса системы
    const checkStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: 'test' }),
        });
        setSystemStatus(response.ok ? 'Онлайн' : 'Офлайн');
      } catch {
        setSystemStatus('Офлайн');
      }
    };
    checkStatus();
  }, []);

  return (
    <div className="sidebar">
      <Stats requestsToday={requestsToday} systemStatus={systemStatus} />
      <Settings autoScroll={autoScroll} onToggleAutoScroll={onToggleAutoScroll} />
      <History />
    </div>
  );
};

export default Sidebar;