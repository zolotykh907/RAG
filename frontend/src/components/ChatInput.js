import React, { useState, useRef } from 'react';

const ChatInput = ({ onSend, disabled, uploadTempFile }) => {
  const [question, setQuestion] = useState('');
  const fileInputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (question.trim()) {
      onSend(question);
      setQuestion('');
    }
  };

  const handleFileAttach = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      uploadTempFile(file);
    }
    // Очищаем input, чтобы можно было выбрать тот же файл снова
    e.target.value = '';
  };

  return (
    <div className="chat-input-container">
      <form className="question-form" onSubmit={handleSubmit}>
        <div className="input-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button
            type="button"
            onClick={handleFileAttach}
            disabled={disabled}
            style={{
              background: 'var(--surface-light)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              padding: '0.7rem',
              cursor: disabled ? 'not-allowed' : 'pointer',
              color: 'var(--text-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '3rem',
              height: '3rem',
            }}
            title="Прикрепить файл для временного использования"
          >
            <i className="fas fa-paperclip" style={{ fontSize: '1.1rem' }}></i>
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
            style={{ display: 'none' }}
          />
          <input
            type="text"
            id="questionInput"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Введите ваш вопрос..."
            disabled={disabled}
            style={{ flex: 1 }}
          />
          <button type="submit" id="sendButton" disabled={disabled}>
            <i className="fas fa-paper-plane"> Отправить </i>
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInput;