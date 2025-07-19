import React, { useState, useCallback } from 'react';
import Header from './components/Header';
import ChatContainer from './components/ChatContainer';
import Sidebar from './components/Sidebar';
import LoadingOverlay from './components/LoadingOverlay';
import Navigation from './components/Navigation';
import Config from './components/Config';
import Upload from './components/Upload';
import ConfigSidebar from './components/ConfigSidebar';
import Toast from './components/Toast';
import './styles.css';

const App = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const [selectedService, setSelectedService] = useState('query');
  const [config, setConfig] = useState({});
  const [initialConfig, setInitialConfig] = useState({}); // добавлено для хранения начального состояния
  const [status, setStatus] = useState('');
  const [toast, setToast] = useState({ visible: false, message: '', type: 'success' });
  const [autoScroll, setAutoScroll] = useState(true);
  const [messages, setMessages] = useState([]);
  const [showSources, setShowSources] = useState({});
  const [tempSessionId, setTempSessionId] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ visible: true, message, type });
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  // --- Конфиг обработчики ---
  const fetchConfig = useCallback(async (service) => {
    try {
      setIsLoading(true);
      const endpoint = `http://localhost:8000/config?service=${service}`;
      const res = await fetch(endpoint);
      if (!res.ok) throw new Error('Ошибка сети');
      const data = await res.json();
      setConfig(data || {});
      // Сохраняем initialConfig только если он ещё не был установлен
      setInitialConfig(prev => (Object.keys(prev).length === 0 ? (data || {}) : prev));
      setStatus('✅ Конфигурация загружена');
    } catch (err) {
      setStatus('❌ Ошибка загрузки');
      showToast('Ошибка загрузки конфигурации', 'error');
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (activeTab === 'config') {
      fetchConfig(selectedService);
    }
  }, [selectedService, activeTab, fetchConfig]);

  const handleChange = (path, value) => {
    setConfig((prevConfig) => {
      const newConfig = structuredClone(prevConfig || {});
      let obj = newConfig;
      for (let i = 0; i < path.length - 1; i++) {
        obj = obj[path[i]] = obj[path[i]] || {};
      }
      const lastKey = path[path.length - 1];
      const original = obj[lastKey];
      if (Array.isArray(original)) {
        obj[lastKey] = value.split(',').map((v) => v.trim());
      } else {
        const numValue = Number(value);
        obj[lastKey] = !isNaN(numValue) && value.trim() !== '' ? numValue : value;
      }
      return newConfig;
    });
  };

  const handleSubmit = (e) => {
    if (e && e.preventDefault) e.preventDefault();
    setIsLoading(true);
    const endpoint = `http://localhost:8000/config?service=${selectedService}`;
    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
      .then((res) => {
        if (!res.ok) throw new Error('Ошибка сохранения');
        return res.json();
      })
      .then(() => {
        setStatus('✅ Конфигурация сохранена!');
        showToast('✅ Конфигурация сохранена!', 'success');
      })
      .catch(() => {
        setStatus('❌ Ошибка сохранения');
        showToast('❌ Ошибка сохранения', 'error');
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  const handleReset = () => {
    setConfig(initialConfig); // сбрасываем к начальному состоянию
    setStatus('');
  };

  const handleReload = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/reload?service=${selectedService}`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Ошибка перезагрузки');
      setStatus('✅ Сервис перезапущен');
      showToast('✅ Сервис перезапущен', 'success');
    } catch (e) {
      setStatus('❌ Ошибка при перезапуске сервиса');
      showToast('❌ Ошибка при перезапуске сервиса', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleAutoScroll = () => setAutoScroll((v) => !v);

  // Добавление сообщения
  const addMessage = (content, type, sources = null) => {
    const msg = { content, type, sources, id: Date.now() };
    setMessages((prev) => [...prev, msg]);
    if (type === 'user') {
      const history = JSON.parse(localStorage.getItem('rag_history') || '[]');
      localStorage.setItem('rag_history', JSON.stringify([content, ...history].slice(0, 30)));
    }
  };

  // Переключение показа источников
  const handleToggleSources = (id) => setShowSources((prev) => ({ ...prev, [id]: !prev[id] }));

  // Временное индексирование файла для чата
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
      
      // Сохраняем session_id для использования в запросах
      setTempSessionId(data.session_id);
      
      addMessage(`✅ Файл "${file.name}" успешно прикреплен и готов к использованию в чате!`, 'assistant');
    } catch (error) {
      addMessage(`❌ Ошибка при прикреплении файла: ${error.message}`, 'assistant');
    } finally {
      setIsLoading(false);
    }
  };

  // Отправка вопроса
  const sendQuestion = async (question) => {
    if (!question) return;
    addMessage(question, 'user');
    setIsLoading(true);
    try {
      // Отправляем запрос на единый endpoint с session_id, если он есть
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
    } catch (error) {
      addMessage(`Ошибка: ${error.message}`, 'assistant');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <Header onTabChange={handleTabChange} />
      <main className="main-content">
        {activeTab === 'chat' && (
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
            <Sidebar autoScroll={autoScroll} onToggleAutoScroll={handleToggleAutoScroll} activeTab={activeTab} />
          </>
        )}
        {activeTab === 'config' && (
          <>
            <Config
              config={config}
              setConfig={setConfig}
              status={status}
              setStatus={setStatus}
              isLoading={isLoading}
              onChange={handleChange}
              onSubmit={handleSubmit}
              selectedService={selectedService}
            />
            <ConfigSidebar
              selectedService={selectedService}
              onSelectService={setSelectedService}
              onReset={handleReset}
              onReload={handleReload}
              isLoading={isLoading}
              onSave={handleSubmit}
            />
          </>
        )}
        {activeTab === 'upload' && (
          <Upload onLoadingChange={setIsLoading} />
        )}
      </main>
      {isLoading && <LoadingOverlay />}
      <Toast
        message={toast.message}
        type={toast.type}
        visible={toast.visible}
        onClose={() => setToast({ ...toast, visible: false })}
      />
    </div>
  );
};

export default App;