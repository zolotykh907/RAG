import React, { useEffect, useRef } from 'react';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';

const ChatContainer = ({
  messages,
  setMessages,
  showSources,
  setShowSources,
  addMessage,
  onToggleSources,
  sendQuestion,
  onLoadingChange,
  autoScroll
}) => {
  const [loading, setLoading] = React.useState(false);
  const chatMessagesRef = useRef(null);

  useEffect(() => {
    if (autoScroll && chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  }, [messages, autoScroll]);

  // Приветствие только если сообщений нет
  useEffect(() => {
    if (messages.length === 0) {
      addMessage('Система готова к работе! Задайте любой вопрос.', 'system');
    }
    // eslint-disable-next-line
  }, []);

  return (
    <div className="chat-container">
      <ChatMessages
        messages={messages}
        ref={chatMessagesRef}
        showSources={showSources}
        onToggleSources={onToggleSources}
      />
      <ChatInput onSend={sendQuestion} disabled={loading} />
    </div>
  );
};

export default ChatContainer;