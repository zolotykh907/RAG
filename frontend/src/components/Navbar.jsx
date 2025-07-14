import { Link, useLocation } from 'react-router-dom';

export default function Navbar() {
  const location = useLocation();
  
  return (
    <nav>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <h1 style={{ color: '#667eea', margin: 0 }}>🤖 RAG System</h1>
      </div>
      <div style={{ display: 'flex', gap: '2rem' }}>
        <Link 
          to="/" 
          className={location.pathname === '/' ? 'active' : ''}
        >
          🔍 Запросы
        </Link>
        <Link 
          to="/upload" 
          className={location.pathname === '/upload' ? 'active' : ''}
        >
          📁 Загрузка
        </Link>
      </div>
    </nav>
  );
}