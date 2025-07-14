import React, { forwardRef } from 'react';

const ChatMessages = forwardRef(({ messages }, ref) => {
  return (
    <div className="chat-messages" ref={ref}>
      {messages.map((msg) => (
        <div key={msg.id} className={`message ${msg.type}`}>
          <div className="message-content">
            {msg.type === 'system' && <i className="fas fa-info-circle"></i>}
            <p>{msg.content.replace(/\n/g, '<br>')}</p>
            {msg.sources && msg.sources.length > 0 && (
              <div className="sources">
                <h4><i className="fas fa-link"></i> Источники</h4>
                {msg.sources.map((source, index) => (
                  <div key={index} className="source-item">
                    <strong>Источник {index + 1}:</strong> {source.substring(0, 200) + (source.length > 200 ? '...' : '')}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
});

export default ChatMessages;