import { useState, useEffect } from 'react';
import './ChatHistory.css';

// Компонент истории чатов
function ChatHistory({ onSelectChat, currentSessionId, onNewChat, onClearSession }) {
  const [chats, setChats] = useState([]);
  const [isExpanded, setIsExpanded] = useState(true);

  // Загрузка истории из localStorage при монтировании
  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = () => {
    try {
      const stored = localStorage.getItem('chatHistory');
      if (stored) {
        const history = JSON.parse(stored);
        setChats(history);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  // Сохранение нового чата в историю
  const saveChat = (sessionId, fileName) => {
    const newChat = {
      id: sessionId,
      fileName: fileName,
      timestamp: new Date().toISOString(),
      lastMessage: `Загружен файл: ${fileName}`
    };

    setChats(prevChats => {
      const updatedChats = [newChat, ...prevChats.filter(c => c.id !== sessionId)].slice(0, 10);
      localStorage.setItem('chatHistory', JSON.stringify(updatedChats));
      return updatedChats;
    });
  };

  // Обновление последнего сообщения чата
  const updateChatMessage = (sessionId, message) => {
    setChats(prevChats => {
      const updatedChats = prevChats.map(chat =>
        chat.id === sessionId
          ? { ...chat, lastMessage: message, timestamp: new Date().toISOString() }
          : chat
      );
      localStorage.setItem('chatHistory', JSON.stringify(updatedChats));
      return updatedChats;
    });
  };

  // Удаление чата из истории
  const deleteChat = (chatId, e) => {
    e.stopPropagation();
    setChats(prevChats => {
      const updatedChats = prevChats.filter(c => c.id !== chatId);
      localStorage.setItem('chatHistory', JSON.stringify(updatedChats));
      return updatedChats;
    });
  };

  // Форматирование времени
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'только что';
    if (diffMins < 60) return `${diffMins} мин назад`;
    if (diffHours < 24) return `${diffHours} ч назад`;
    if (diffDays < 7) return `${diffDays} д назад`;
    return date.toLocaleDateString();
  };

  // Экспорт функций для использования из родительского компонента
  useEffect(() => {
    window.chatHistory = { saveChat, updateChatMessage };
  }, []);

  // Слушаем событие очистки чата для обновления превью
  useEffect(() => {
    const handleClearChat = (event) => {
      const { sessionId } = event.detail;
      setChats(prevChats => {
        const chat = prevChats.find(c => c.id === sessionId);
        if (chat) {
          const updatedChats = prevChats.map(c =>
            c.id === sessionId
              ? { ...c, lastMessage: `Загружен файл: ${c.fileName}`, timestamp: new Date().toISOString() }
              : c
          );
          localStorage.setItem('chatHistory', JSON.stringify(updatedChats));
          return updatedChats;
        }
        return prevChats;
      });
    };

    window.addEventListener('clearChat', handleClearChat);
    return () => window.removeEventListener('clearChat', handleClearChat);
  }, []);

  return (
    <div className="chat-history">
      <div className="history-header">
        <button
          className="new-chat-btn"
          onClick={onNewChat}
          title="Новый чат"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span>Новый чат</span>
        </button>

        <button
          className="toggle-history-btn"
          onClick={() => setIsExpanded(!isExpanded)}
          title={isExpanded ? 'Скрыть историю' : 'Показать историю'}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            style={{ transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}
          >
            <polyline points="18 15 12 9 6 15"></polyline>
          </svg>
        </button>
      </div>

      {isExpanded && (
        <div className="history-list">
          {chats.length === 0 ? (
            <div className="history-empty">
              <p>История чатов пуста</p>
              <span>Загрузите файл для начала</span>
            </div>
          ) : (
            chats.map(chat => (
              <div
                key={chat.id}
                className={`history-item ${chat.id === currentSessionId ? 'active' : ''}`}
                onClick={() => onSelectChat(chat.id)}
              >
                <div className="history-item-content">
                  <div className="history-item-header">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
                      <polyline points="13 2 13 9 20 9"></polyline>
                    </svg>
                    <span className="history-item-title">{chat.fileName}</span>
                  </div>
                  <p className="history-item-message">{chat.lastMessage}</p>
                  <span className="history-item-time">{formatTime(chat.timestamp)}</span>

                  {chat.id === currentSessionId && onClearSession && (
                    <button
                      className="clear-session-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        onClearSession();
                      }}
                      title="Очистить историю сообщений (документ останется)"
                    >
                      Очистить сообщения
                    </button>
                  )}
                </div>

                <button
                  className="delete-chat-btn"
                  onClick={(e) => deleteChat(chat.id, e)}
                  title="Удалить из истории"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default ChatHistory;
