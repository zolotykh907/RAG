import { NavLink } from 'react-router-dom';

const pages = [
  { to: '/introduction', label: 'Введение' },
  { to: '/description', label: 'Описание' },
  { to: '/architecture', label: 'Архитектура' },
  { to: '/technologies', label: 'Технологии' },
  { to: '/installation', label: 'Установка' },
  { to: '/usage', label: 'Использование' },
  { to: '/api', label: 'API' },
  { to: '/testing', label: 'Тестирование' },
  { to: '/posts', label: 'Посты'},
];

function Sidebar() {
  function getActiveState({ isActive }) {
    if (isActive) {
      return 'nav-link active'
    }
    else {
      return 'nav-link'
    }
  }

  return (
    <nav className="sidebar">
      <h2>Навигация</h2>
      <ul className="nav-menu" style={{ padding: '0px 15px 0px 15px' }}>
        {pages.map(item => (
          <li key={item.to}>
            <NavLink to={item.to} className={getActiveState}>
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export default Sidebar;
