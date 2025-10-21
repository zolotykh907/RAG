import React, { useState, useCallback, useEffect } from 'react';
import ChatContainer from '../components/ChatContainer';
import Sidebar from '../components/Sidebar';
import LoadingOverlay from '../components/LoadingOverlay';
import Toast from '../components/Toast';

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showSources, setShowSources] = useState({});
  const [autoScroll, setAutoScroll] = useState(true);
  const [toast, setToast] = useState({ message: '', type: 'success', visible: false });
  const [tempSessionId, setTempSessionId] = useState(null);
  const [requestsToday, setRequestsToday] = useState(0);

  // Загружаем счетчик запросов из localStorage при инициализации
  useEffect(() => {
    const savedRequests = localStorage.getItem('requestsToday');
    if (savedRequests) {
      const { count, date } = JSON.parse(savedRequests);
      const today = new Date().toDateString();
      if (date === today) {
        setRequestsToday(count);
      } else {
        setRequestsToday(0);
        localStorage.setItem('requestsToday', JSON.stringify({ count: 0, date: today }));
      }
    } else {
      const today = new Date().toDateString();
      localStorage.setItem('requestsToday', JSON.stringify({ count: 0, date: today }));
    }
  }, []);

  const showToast = (message, type = 'success') => {
    setToast({ visible: true, message, type });
  };

  const incrementRequestsCount = () => {
    const today = new Date().toDateString();
    const newCount = requestsToday + 1;
    setRequestsToday(newCount);
    localStorage.setItem('requestsToday', JSON.stringify({ count: newCount, date: today }));
  };

  const addMessage = (content, type, sources = null) => {
    const msg = { content, type, sources, id: Date.now() };
    setMessages((prev) => [...prev, msg]);
    if (type === 'user') {
      const history = JSON.parse(localStorage.getItem('rag_history') || '[]');
      localStorage.setItem('rag_history', JSON.stringify([content, ...history].slice(0, 30)));
    }
  };

  const handleToggleSources = (id) => setShowSources((prev) => ({ ...prev, [id]: !prev[id] }));

  const uploadTempFile = async (file) => {
    if (!file) return;
    
    addMessage(`📎 Прикрепляю файл: ${file.name}`, 'user');
    setIsLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch('http://localhost:8000/upload-temp', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) throw new Error('Ошибка загрузки файла');
      const data = await response.json();
      
      setTempSessionId(data.session_id);
      addMessage(`✅ Файл "${file.name}" успешно прикреплен и готов к использованию в чате!`, 'assistant');
    } catch (error) {
      addMessage(`❌ Ошибка при прикреплении файла: ${error.message}`, 'assistant');
    } finally {
      setIsLoading(false);
    }
  };

  const sendQuestion = async (question) => {
    if (!question) return;
    addMessage(question, 'user');
    setIsLoading(true);
    try {
      const requestBody = tempSessionId 
        ? { question, session_id: tempSessionId }
        : { question };
      
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });
      if (!response.ok) throw new Error('API error');
      const data = await response.json();
      addMessage(data.answer, 'assistant', data.texts);
      incrementRequestsCount();
    } catch (error) {
      addMessage(`Ошибка: ${error.message}`, 'assistant');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleAutoScroll = () => setAutoScroll((v) => !v);

  return (
    <>
      <ChatContainer
        messages={messages}
        setMessages={setMessages}
        showSources={showSources}
        setShowSources={setShowSources}
        addMessage={addMessage}
        onToggleSources={handleToggleSources}
        sendQuestion={sendQuestion}
        onLoadingChange={setIsLoading}
        autoScroll={autoScroll}
        uploadTempFile={uploadTempFile}
      />
      <Sidebar 
        autoScroll={autoScroll} 
        onToggleAutoScroll={handleToggleAutoScroll} 
        activeTab="chat"
        requestsToday={requestsToday}
      />
      {isLoading && <LoadingOverlay />}
      <Toast
        message={toast.message}
        type={toast.type}
        visible={toast.visible}
        onClose={() => setToast({ ...toast, visible: false })}
      />
    </>
  );
};

export default ChatPage;
