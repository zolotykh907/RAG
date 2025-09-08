import { NavLink } from 'react-router-dom';

const navItems = [
  { to: '/introduction', label: 'Введение' },
  { to: '/description', label: 'Описание' },
  { to: '/architecture', label: 'Архитектура' },
  { to: '/technologies', label: 'Технологии' },
  { to: '/installation', label: 'Установка' },
  { to: '/usage', label: 'Использование' },
  { to: '/api', label: 'API' },
  { to: '/testing', label: 'Тестирование' },
];

const Sidebar = () => (
  <nav className="sidebar">
    <h2>Навигация</h2>
    <ul className="nav-menu">
      {navItems.map((item) => (
        <li key={item.to}>
          <NavLink
            to={item.to}
            className={({ isActive }) => isActive ? 'active' : ''}
          >
            {item.label}
          </NavLink>
        </li>
      ))}
    </ul>
  </nav>
);

export default Sidebar;
