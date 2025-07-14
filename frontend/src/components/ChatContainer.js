import React, { useState, useEffect, useRef } from 'react';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';

const ChatContainer = ({ onLoadingChange }) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const chatMessagesRef = useRef(null);

  const addMessage = (content, type, sources = null) => {
    setMessages((prev) => [
      ...prev,
      { content, type, sources, id: Date.now() },
    ]);
  };

  const sendQuestion = async (question) => {
    if (!question) return;

    addMessage(question, 'user');
    setLoading(true);
    onLoadingChange(true); // Уведомляем родителя о начале загрузки

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });
      if (!response.ok) throw new Error('API error');
      const data = await response.json();
      addMessage(data.answer, 'assistant', data.texts);
    } catch (error) {
      addMessage(`Ошибка: ${error.message}`, 'assistant');
    } finally {
      setLoading(false);
      onLoadingChange(false); // Уведомляем родителя об окончании загрузки
    }
  };

  useEffect(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    addMessage('Система готова к работе! Задайте любой вопрос.', 'system');
  }, []);

  return (
    <div className="chat-container">
      <ChatMessages messages={messages} ref={chatMessagesRef} />
      <ChatInput onSend={sendQuestion} disabled={loading} />
    </div>
  );
};

export default ChatContainer;