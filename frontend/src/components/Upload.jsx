import { useState } from 'react';
import axios from 'axios';

export default function Upload() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [messageType, setMessageType] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setMessage('');
    setMessageType('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(
        'http://localhost:8000/upload-files',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );
      setMessage(response.data.message);
      setMessageType('success');
      setFile(null);
      e.target.reset();
    } catch (error) {
      setMessage(error.response?.data?.error || 'Ошибка при загрузке файла');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setMessage('');
    setMessageType('');
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="config-container">
      <div className="chat-messages">
        <div className="message system" style={{ marginBottom: '2.2rem' }}>
          <div className="message-content">
            <h2 style={{ fontWeight: 700, fontSize: '1.45rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 10, justifyContent: 'center', width: '100%', textAlign: 'center' }}>
              <span style={{ fontSize: '1.7rem' }}>📁</span> Загрузка и индексация файлов
            </h2>
          </div>
        </div>
      </div>
      <form onSubmit={handleSubmit} style={{
        background: 'var(--surface-light)',
        borderRadius: 18,
        padding: '2.5rem 2.5rem 2rem 2.5rem',
        boxShadow: 'var(--shadow-lg)',
        border: '1.5px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '1.7rem',
        margin: '0 auto',
        maxWidth: 600,
        width: '100%'
      }}>
        <label htmlFor="file" style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '1.15rem', marginBottom: 10, alignSelf: 'flex-start' }}>
          Выберите файл для загрузки:
        </label>
        <input
          id="file"
          type="file"
          onChange={handleFileChange}
          accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
          required
          disabled={loading}
          style={{
            background: 'var(--surface)',
            color: 'var(--text-primary)',
            border: '2px solid var(--border)',
            borderRadius: 10,
            padding: '1.1rem 1.2rem',
            fontSize: '1.05rem',
            width: '100%',
            marginBottom: 0,
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        />
        {file && (
          <div style={{
            padding: '1.1rem 1.2rem',
            background: 'var(--surface)',
            borderRadius: '10px',
            border: '1.5px solid var(--border)',
            marginTop: '0.5rem',
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
          }}>
            <span style={{ fontSize: '1.3rem', color: 'var(--primary-color)' }}>📄</span>
            <div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>{file.name}</div>
              <div style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>
                {formatFileSize(file.size)} • {file.type || 'Неизвестный тип'}
              </div>
            </div>
          </div>
        )}
        <button
          type="submit"
          disabled={loading || !file}
          style={{
            background: 'linear-gradient(135deg, var(--primary-color), var(--secondary-color))',
            color: 'white',
            fontWeight: 700,
            fontSize: '1.15rem',
            border: 'none',
            borderRadius: 10,
            width: '100%',
            height: 48,
            marginTop: 10,
            boxShadow: 'var(--shadow)',
            transition: 'background 0.2s',
            cursor: loading || !file ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 14,
          }}
        >
          {loading ? (
            <div className="loading">
              <div className="spinner"></div>
              <span style={{ fontSize: '1.1rem' }}>Индексация файла...</span>
            </div>
          ) : (
            <>
              <span style={{ fontSize: '1.3rem' }}>📤</span> Загрузить и проиндексировать
            </>
          )}
        </button>
        {message && (
          <div className={`message ${messageType}`} style={{ width: '100%', marginTop: 14, textAlign: 'center', fontWeight: 600, fontSize: '1.08rem' }}>
            {messageType === 'success' ? '✅ ' : '❌ '}
            {message}
          </div>
        )}
        <div style={{
          marginTop: '2.2rem',
          padding: '1.3rem 1.7rem',
          background: 'var(--surface-light)',
          borderRadius: '12px',
          border: '1.5px solid var(--border)',
          width: '100%',
          color: 'var(--primary-color)',
          boxShadow: 'var(--shadow)',
        }}>
          <h4 style={{ color: 'var(--primary-color)', marginBottom: '0.7rem', fontWeight: 700, fontSize: '1.08rem' }}>ℹ️ Поддерживаемые форматы:</h4>
          <ul style={{ margin: 0, paddingLeft: '1.5rem', color: 'var(--text-secondary)', fontSize: '1.02rem' }}>
            <li><strong>PDF</strong> — Документы Adobe PDF</li>
            <li><strong>DOC/DOCX</strong> — Документы Microsoft Word</li>
            <li><strong>TXT</strong> — Текстовые файлы</li>
            <li><strong>JPG/PNG</strong> — Изображения (с OCR)</li>
          </ul>
        </div>
      </form>
    </div>
  );
} 