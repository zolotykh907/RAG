import React, { useState, useEffect } from 'react';

const History = () => {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    setHistory(JSON.parse(localStorage.getItem('rag_history') || '[]'));
  }, []);

  const clearHistory = () => {
    if (confirm('Вы уверены, что хотите очистить историю?')) {
      localStorage.removeItem('rag_history');
      setHistory([]);
    }
  };

  return (
    <div className="sidebar-section">
      <h3><i className="fas fa-history"></i> История</h3>
      <div className="history-list" id="historyList">
        {history.length === 0 ? (
          <p className="empty-history">История пуста</p>
        ) : (
          history.map((item, index) => (
            <div key={index} className="history-item">
              {item.substring(0, 50) + (item.length > 50 ? '...' : '')}
            </div>
          ))
        )}
      </div>
      <button className="clear-history-btn" onClick={clearHistory}>
        <i className="fas fa-trash"></i> Очистить историю
      </button>
    </div>
  );
};

export default History;