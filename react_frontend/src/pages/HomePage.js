import { useState, useEffect, useCallback } from 'react';
import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import ChatHistory from '../components/ChatHistory';
import ChatPage from './ChatPage';
import DocumentsPage from './DocumentsPage';
import UploadPage from './UploadPage';
import SettingsPage from './SettingsPage';
import ArticlesPage from './ArticlesPage';
import apiService from '../services/api';
import './HomePage.css';

// Главная страница приложения
function HomePage() {
  const location = useLocation();
  const [sessionId, setSessionId] = useState(() => {
    return localStorage.getItem('currentSessionId') || null;
  });
  const [apiStatus, setApiStatus] = useState('checking');

  // Определяем активную вкладку по URL
  const getActiveTab = () => {
    const path = location.pathname;
    if (path === '/' || path === '/chat') return 'chat';
    if (path === '/documents') return 'documents';
    if (path === '/upload') return 'upload';
    if (path === '/articles') return 'articles';
    if (path === '/settings') return 'settings';
    return 'chat';
  };

  const activeTab = getActiveTab();

  // Проверка здоровья API при загрузке
  useEffect(() => {
    checkApiHealth();
  }, []);

  // Сохранение текущего sessionId в localStorage
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem('currentSessionId', sessionId);
    } else {
      localStorage.removeItem('currentSessionId');
    }
  }, [sessionId]);

  const checkApiHealth = async () => {
    try {
      await apiService.healthCheck();
      setApiStatus('healthy');
    } catch (error) {
      setApiStatus('unhealthy');
    }
  };

  // Выбор чата из истории
  const handleSelectChat = useCallback((chatId) => {
    setSessionId(chatId);
  }, []);

  // Создание нового чата
  const handleNewChat = useCallback(() => {
    setSessionId(null);
  }, []);

  // Очистка сообщений чата (документ остается)
  const handleClearSession = () => {
    if (sessionId) {
      try {
        localStorage.removeItem(`chat_${sessionId}`);
        window.dispatchEvent(new CustomEvent('clearChat', { detail: { sessionId } }));
      } catch (error) {
        console.error('Ошибка при очистке сообщений:', error);
      }
    }
  };

  return (
    <div className="home-page">
      {/* Боковая панель */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1 className="logo">RAG System</h1>
          <div className="status-indicator">
            <span className={`status-dot ${apiStatus}`}></span>
            <span className="status-text">
              {apiStatus === 'healthy' ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <Link
            to="/chat"
            className={`nav-item ${activeTab === 'chat' ? 'active' : ''}`}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span>Чат</span>
          </Link>

          <Link
            to="/documents"
            className={`nav-item ${activeTab === 'documents' ? 'active' : ''}`}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
              <polyline points="13 2 13 9 20 9"></polyline>
            </svg>
            <span>Документы</span>
          </Link>

          <Link
            to="/upload"
            className={`nav-item ${activeTab === 'upload' ? 'active' : ''}`}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <span>Загрузка файлов</span>
          </Link>

          <Link
            to="/articles"
            className={`nav-item ${activeTab === 'articles' ? 'active' : ''}`}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
            </svg>
            <span>Статьи</span>
          </Link>

          <Link
            to="/settings"
            className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M12 1v6m0 6v6"></path>
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14"></path>
            </svg>
            <span>Настройки</span>
          </Link>
        </nav>

        {activeTab === 'chat' && (
          <ChatHistory
            onSelectChat={handleSelectChat}
            currentSessionId={sessionId}
            onNewChat={handleNewChat}
            onClearSession={handleClearSession}
          />
        )}
      </aside>

      {/* Основной контент */}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/chat" replace />} />
          <Route path="/chat" element={<ChatPage sessionId={sessionId} setSessionId={setSessionId} />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/articles" element={<ArticlesPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default HomePage;
