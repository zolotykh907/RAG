import React from 'react';
import { NavLink } from 'react-router-dom';

const Navigation = () => {
  return (
    <nav className="config-nav">
      <NavLink
        to="/"
        className={({ isActive }) => (isActive ? 'active' : '')}
        end
      >
        Чат
      </NavLink>
      <NavLink
        to="/config"
        className={({ isActive }) => (isActive ? 'active' : '')}
      >
        Конфигурация
      </NavLink>
      <NavLink
        to="/upload"
        className={({ isActive }) => (isActive ? 'active' : '')}
      >
        Индексирование
      </NavLink>
      <NavLink
        to="/documentation"
        className={({ isActive }) => (isActive ? 'active' : '')}
      >
        Документация
      </NavLink>
    </nav>
  );
};

export default Navigation;