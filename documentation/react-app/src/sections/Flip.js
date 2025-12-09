import React, { useState } from 'react';
import axios from 'axios';
import './Flip.css';

const Flip = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const processFile = (selected) => {
    if (!selected) return;

    if (!selected.type.startsWith('image/')) {
      setError('Пожалуйста, выберите файл изображения (PNG, JPG, GIF и т.д.)');
      return;
    }

    setFile(selected);
    setError('');
    setResult('');

    const reader = new FileReader();
    reader.onload = (event) => setPreview(event.target.result);
    reader.readAsDataURL(selected);
  };

  const handleFileChange = (e) => {
    processFile(e.target.files[0]);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFlip = async () => {
    if (!file) {
      setError('Сначала выберите изображение');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const token = localStorage.getItem('token');
      const headers = { 'Content-Type': 'multipart/form-data' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await axios.post('http://localhost:8000/flip', formData, {
        headers,
        responseType: 'blob',
      });

      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      const imageUrl = URL.createObjectURL(blob);
      setResult(imageUrl);
    } catch (err) {
      setError('Ошибка при обработке изображения: ' + (err.response?.data?.message || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!result) return;

    const link = document.createElement('a');
    link.href = result;
    link.download = `flipped_${file.name}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleReset = () => {
    setFile(null);
    setPreview('');
    setResult('');
    setError('');
  };

  return (
    <section id='flip' className='fade-in flip-section'>
      <h2>Переворот изображения</h2>
      <p className="flip-description">
        Загрузите изображение и переверните его вертикально одним кликом
      </p>

      {!preview ? (
        <div
          className={`flip-upload-area ${dragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept="image/*"
            id="fileInput"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />

          <div className="flip-upload-icon">📁</div>
          <h3>Перетащите изображение сюда</h3>
          <p>или</p>
          <label htmlFor="fileInput" className="flip-upload-button">
            Выбрать файл
          </label>
          <p className="flip-upload-hint">Поддерживаются: PNG, JPG, GIF, WEBP</p>
        </div>
      ) : (
        <div className="flip-content">
          <div className="flip-controls">
            <button onClick={handleFlip} disabled={loading} className="flip-btn flip-btn-primary">
              {loading ? '⏳ Обработка...' : '🔄 Перевернуть изображение'}
            </button>
            {result && (
              <>
                <button onClick={handleDownload} className="flip-btn flip-btn-success">
                  💾 Скачать результат
                </button>
                <button onClick={handleReset} className="flip-btn flip-btn-secondary">
                  🔄 Загрузить другое
                </button>
              </>
            )}
            {!result && (
              <button onClick={handleReset} className="flip-btn flip-btn-secondary">
                ← Назад
              </button>
            )}
          </div>

          {error && (
            <div className="flip-error-box">
              <span className="flip-error-icon">⚠️</span>
              {error}
            </div>
          )}

          <div className="flip-images-container">
            <div className="flip-image-card">
              <div className="flip-image-header">
                <h3>Исходное изображение</h3>
                <span className="flip-badge">Оригинал</span>
              </div>
              <div className="flip-image-wrapper">
                <img src={preview} alt="original" className="flip-image" />
              </div>
              <div className="flip-image-footer">
                <span className="flip-filename">{file?.name}</span>
              </div>
            </div>

            {result && (
              <>
                <div className="flip-arrow">→</div>
                <div className="flip-image-card flip-card-result">
                  <div className="flip-image-header">
                    <h3>Результат</h3>
                    <span className="flip-badge flip-badge-success">Готово ✓</span>
                  </div>
                  <div className="flip-image-wrapper">
                    <img src={result} alt="flipped" className="flip-image flip-image-animated" />
                  </div>
                  <div className="flip-image-footer">
                    <span className="flip-filename">flipped_{file?.name}</span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </section>
  );
};

export default Flip;