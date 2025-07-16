import React from 'react';
import Navigation from './Navigation';

const Header = ({ onTabChange }) => {
  return (
    <header className="header">
      <div className="header-content flex-header">
        <div className="header-title">
          <h1><i className="fas fa-robot"></i> RAG Q&A Система</h1>
        </div>
        <div className="header-nav">
          <Navigation onTabChange={onTabChange} />
        </div>
      </div>
    </header>
  );
};

export default Header;