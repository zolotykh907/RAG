import React from 'react';

const Stats = ({ requestsToday, systemStatus }) => {
  return (
    <div className="sidebar-section">
      <h3><i className="fas fa-chart-bar"></i> Статистика</h3>
      <div className="stats">
        <div className="stat-item">
          <span className="stat-label">Запросов сегодня:</span>
          <span className="stat-value">{requestsToday}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Статус системы:</span>
          <span className={`stat-value ${systemStatus === 'Онлайн' ? 'status-online' : 'status-offline'}`}>
            {systemStatus}
          </span>
        </div>
      </div>
    </div>
  );
};

export default Stats;