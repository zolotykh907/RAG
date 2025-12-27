import { useState } from 'react';
import './InfoPopup.css';

function InfoPopup({ title, children }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="info-popup-container">
      <button
        className="info-popup-trigger"
        onClick={() => setIsOpen(!isOpen)}
        title={title || "Справка"}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="16" x2="12" y2="12"></line>
          <line x1="12" y1="8" x2="12.01" y2="8"></line>
        </svg>
      </button>

      {isOpen && (
        <>
          <div className="info-popup-overlay" onClick={() => setIsOpen(false)} />
          <div className="info-popup-content">
            <div className="info-popup-header">
              <h3>{title || "Информация"}</h3>
              <button
                className="info-popup-close"
                onClick={() => setIsOpen(false)}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            <div className="info-popup-body">
              {children}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default InfoPopup;
