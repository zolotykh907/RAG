import React, { useState } from 'react';

const ChatInput = ({ onSend, disabled }) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (question.trim()) {
      onSend(question);
      setQuestion('');
    }
  };

  return (
    <div className="chat-input-container">
      <form className="question-form" onSubmit={handleSubmit}>
        <div className="input-group">
          <input
            type="text"
            id="questionInput"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Введите ваш вопрос..."
            disabled={disabled}
          />
          <button type="submit" id="sendButton" disabled={disabled}>
            <i className="fas fa-paper-plane"></i>
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInput;