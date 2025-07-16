import React, { useEffect } from 'react';

const Toast = ({ message, type = 'success', visible, onClose }) => {
  useEffect(() => {
    if (visible) {
      const timer = setTimeout(() => {
        onClose();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [visible, onClose]);

  if (!visible) return null;

  return (
    <div className={`toast-notification toast-${type}`}>
      {message}
    </div>
  );
};

export default Toast; 