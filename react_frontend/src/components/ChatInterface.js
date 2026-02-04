import { useState, useRef, useEffect } from 'react';
import apiService from '../services/api';
import './ChatInterface.css';

// Компонент чата для общения с RAG системой
function ChatInterface({ onSendMessage, sessionId = null, onFileUpload, onMessagesUpdate }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [tempFiles, setTempFiles] = useState([]);
  const [showTempFilesModal, setShowTempFilesModal] = useState(false);
  const [selectedTempFile, setSelectedTempFile] = useState(null);
  const [showTempFileContent, setShowTempFileContent] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Загрузка истории сообщений для текущей сессии
  useEffect(() => {
    if (sessionId) {
      loadMessages(sessionId);
      loadTempFilesInfo(sessionId);
    } else {
      setMessages([]);
      setTempFiles([]);
    }
  }, [sessionId]);

  // Загрузка информации о временных файлах
  const loadTempFilesInfo = async (sid) => {
    try {
      const info = await apiService.getTempFilesInfo(sid);
      if (info && info.temp_files) {
        setTempFiles(info.temp_files);
      } else {
        setTempFiles([]);
      }
    } catch (error) {
      console.error('Error loading temp files info:', error);
      setTempFiles([]);
    }
  };

  // Слушаем событие очистки чата
  useEffect(() => {
    const handleClearChat = (event) => {
      if (event.detail.sessionId === sessionId) {
        setMessages([]);
      }
    };

    window.addEventListener('clearChat', handleClearChat);
    return () => window.removeEventListener('clearChat', handleClearChat);
  }, [sessionId]);

  // Автоскролл к последнему сообщению
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Сохранение сообщений в localStorage
  useEffect(() => {
    if (sessionId && messages.length > 0) {
      saveMessages(sessionId, messages);

      // Обновляем последнее сообщение в истории чатов
      const lastMessage = messages[messages.length - 1];
      if (lastMessage && window.chatHistory) {
        const preview = lastMessage.text.length > 50
          ? lastMessage.text.substring(0, 50) + '...'
          : lastMessage.text;
        window.chatHistory.updateChatMessage(sessionId, preview);
      }

      // Уведомляем родителя об обновлении
      if (onMessagesUpdate) {
        onMessagesUpdate(messages);
      }
    }
  }, [messages, sessionId, onMessagesUpdate]);

  const loadMessages = (sid) => {
    try {
      const stored = localStorage.getItem(`chat_${sid}`);
      if (stored) {
        setMessages(JSON.parse(stored));
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const saveMessages = (sid, msgs) => {
    try {
      localStorage.setItem(`chat_${sid}`, JSON.stringify(msgs));
    } catch (error) {
      console.error('Error saving messages:', error);
    }
  };

  // Обработка отправки сообщения
  const handleSend = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage = {
      type: 'user',
      text: inputValue,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      // Отправляем запрос через callback функцию
      const response = await onSendMessage(inputValue);

      const botMessage = {
        type: 'bot',
        text: response.answer,
        sources: response.texts,
        timestamp: new Date().toLocaleTimeString()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        type: 'error',
        text: `Ошибка: ${error.message}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  // Обработка нажатия Enter
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Обработка загрузки файла
  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file || !onFileUpload) return;

    setUploadingFile(true);

    try {
      const result = await onFileUpload(file);

      const systemMessage = {
        type: 'system',
        text: `Файл "${file.name}" успешно загружен. Обработано ${result.chunks_count} фрагментов текста. Теперь вы можете задавать вопросы по этому документу.`,
        timestamp: new Date().toLocaleTimeString()
      };

      setMessages(prev => [...prev, systemMessage]);

      // Обновляем информацию о временных файлах
      if (result.session_id) {
        loadTempFilesInfo(result.session_id);
      }
    } catch (error) {
      const errorMessage = {
        type: 'error',
        text: `Ошибка при загрузке файла: ${error.message}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setUploadingFile(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  // Обработка клика по временному файлу
  const handleTempFileClick = async (filename) => {
    try {
      const content = await apiService.getDocumentContent(filename, sessionId);
      setSelectedTempFile(content);
      setShowTempFileContent(true);
      setShowTempFilesModal(false);
    } catch (error) {
      console.error('Error loading temp file content:', error);
      const errorMessage = {
        type: 'error',
        text: `Ошибка при загрузке файла: ${error.message}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  // Обработка удаления временного файла
  const handleDeleteTempFile = async (filename, event) => {
    event.stopPropagation();

    if (!window.confirm(`Вы уверены, что хотите удалить файл "${filename}"?`)) {
      return;
    }

    try {
      await apiService.deleteTempFile(sessionId, filename);

      // Обновляем список временных файлов
      await loadTempFilesInfo(sessionId);

      const systemMessage = {
        type: 'system',
        text: `Файл "${filename}" успешно удален из текущего чата.`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, systemMessage]);
    } catch (error) {
      console.error('Error deleting temp file:', error);
      const errorMessage = {
        type: 'error',
        text: `Ошибка при удалении файла: ${error.message}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Чат с документами</h2>
        {tempFiles.length > 0 && (
          <button
            className="session-badge clickable"
            onClick={() => setShowTempFilesModal(true)}
            title={`Загружено файлов: ${tempFiles.length}`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
              <polyline points="13 2 13 9 20 9"></polyline>
            </svg>
            Временных файлов: {tempFiles.length}
          </button>
        )}
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <h3>Начните разговор</h3>
            <p>Задайте вопрос о ваших документах или загрузите новый файл</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={`message message-${message.type}`}>
              <div className="message-avatar">
                {message.type === 'user' ? (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                  </svg>
                ) : message.type === 'error' ? (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                  </svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                  </svg>
                )}
              </div>
              <div className="message-body">
                <div className="message-text">{message.text}</div>

                {message.sources && message.sources.length > 0 && (
                  <div className="message-sources">
                    <details>
                      <summary>Источники ({message.sources.length})</summary>
                      <div className="sources-list">
                        {message.sources.map((source, idx) => (
                          <div key={idx} className="source-item">
                            <div className="source-number">#{idx + 1}</div>
                            <div className="source-text">{source}</div>
                          </div>
                        ))}
                      </div>
                    </details>
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {loading && (
          <div className="message message-bot loading">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".txt,.pdf,.doc,.docx"
          style={{ display: 'none' }}
        />

        <button
          className="attachment-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={loading || uploadingFile || !onFileUpload}
          title="Загрузить файл для текущей сессии"
        >
          {uploadingFile ? (
            <svg className="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
            </svg>
          )}
        </button>

        <textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Задайте вопрос о документе..."
          disabled={loading || uploadingFile}
          rows="1"
        />

        <button
          className="send-btn"
          onClick={handleSend}
          disabled={!inputValue.trim() || loading || uploadingFile}
        >
          {loading ? (
            <svg className="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          )}
        </button>
      </div>

      {/* Модальное окно с временными файлами */}
      {showTempFilesModal && (
        <div className="document-modal-overlay" onClick={() => setShowTempFilesModal(false)}>
          <div className="document-modal temp-files-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Временные файлы в этом чате</h3>
              <button className="modal-close-btn" onClick={() => setShowTempFilesModal(false)}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>

            <div className="modal-content">
              {tempFiles.length === 0 ? (
                <div className="temp-files-empty">
                  <p>Нет загруженных временных файлов</p>
                </div>
              ) : (
                <div className="temp-files-grid">
                  {tempFiles.map((file, index) => (
                    <div
                      key={index}
                      className="temp-file-card"
                      onClick={() => handleTempFileClick(file.filename)}
                      style={{ cursor: 'pointer' }}
                    >
                      <div className="document-card-header">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
                          <polyline points="13 2 13 9 20 9"></polyline>
                        </svg>
                        <button
                          className="delete-btn"
                          onClick={(e) => handleDeleteTempFile(file.filename, e)}
                          title="Удалить файл"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                          </svg>
                        </button>
                      </div>
                      <h4 className="document-title">{file.filename}</h4>
                      <div className="document-meta">
                        <div className="meta-item">
                          <span className="meta-label">Фрагментов:</span>
                          <span className="meta-value">{file.chunks_count}</span>
                        </div>
                        <div className="meta-item">
                          <span className="meta-label">Размер:</span>
                          <span className="meta-value">{formatBytes(file.total_chars)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно с содержимым временного файла */}
      {showTempFileContent && selectedTempFile && (
        <div className="document-modal-overlay" onClick={() => setShowTempFileContent(false)}>
          <div className="document-modal document-content-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3>{selectedTempFile.filename}</h3>
                <p className="modal-subtitle">
                  {selectedTempFile.total_chunks} фрагментов, {formatBytes(selectedTempFile.total_chars)}
                  {selectedTempFile.is_temporary && <span className="temp-badge"> (временный)</span>}
                </p>
              </div>
              <button className="modal-close-btn" onClick={() => setShowTempFileContent(false)}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>

            <div className="modal-content chunks-container">
              {selectedTempFile.chunks && selectedTempFile.chunks.length > 0 ? (
                selectedTempFile.chunks.map((chunk, index) => (
                  <div key={index} className="chunk-item">
                    <div className="chunk-header">
                      <span className="chunk-number">Фрагмент #{index + 1}</span>
                      {chunk.hash && (
                        <span className="chunk-hash" title={chunk.hash}>
                          {chunk.hash.substring(0, 8)}
                        </span>
                      )}
                    </div>
                    <div className="chunk-text">{chunk.text}</div>
                  </div>
                ))
              ) : (
                <div className="empty-state">
                  <p>Нет доступных фрагментов</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ChatInterface;
