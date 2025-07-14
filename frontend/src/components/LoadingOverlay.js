import React from 'react';

const LoadingOverlay = () => {
  return (
    <div className="loading-overlay" id="loadingOverlay">
      <div className="loading-spinner">
        <i className="fas fa-spinner fa-spin"></i>
        <p>Обрабатываю ваш вопрос...</p>
      </div>
    </div>
  );
};

export default LoadingOverlay;