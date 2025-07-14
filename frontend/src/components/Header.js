import React from 'react';

const Header = () => {
  return (
    <header className="header">
      <div className="header-content">
        <h1><i className="fas fa-robot"></i> RAG Q&A Система</h1>
        <p>Задайте вопрос и получите ответ на основе ваших документов</p>
      </div>
    </header>
  );
};

export default Header;