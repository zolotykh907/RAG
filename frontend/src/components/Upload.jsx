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
      // Очищаем input файла
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
    <div className="upload-container">
      <h2>📁 Загрузка и индексация файлов</h2>
      <p style={{ color: '#666', marginBottom: '1.5rem' }}>
        Загрузите документ для индексации в векторную базу данных. 
        Поддерживаются форматы: PDF, DOC, DOCX, TXT, JPG, PNG
      </p>
      
      <form onSubmit={handleSubmit}>
        <label htmlFor="file" style={{ fontWeight: '500', color: '#333' }}>
          Выберите файл:
        </label>
        <input 
          id="file"
          type="file" 
          onChange={handleFileChange}
          accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
          required 
          disabled={loading}
        />
        
        {/* Информация о выбранном файле */}
        {file && (
          <div style={{
            padding: '1rem',
            background: '#f8f9fa',
            borderRadius: '8px',
            border: '1px solid #e1e5e9',
            marginTop: '0.5rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '1.2rem' }}>📄</span>
              <div>
                <div style={{ fontWeight: '500' }}>{file.name}</div>
                <div style={{ fontSize: '0.9rem', color: '#666' }}>
                  {formatFileSize(file.size)} • {file.type || 'Неизвестный тип'}
                </div>
              </div>
            </div>
          </div>
        )}
        
        <button type="submit" disabled={loading || !file}>
          {loading ? (
            <div className="loading">
              <div className="spinner"></div>
              <span>Индексация файла...</span>
            </div>
          ) : (
            '📤 Загрузить и проиндексировать'
          )}
        </button>
      </form>

      {/* Сообщение о результате */}
      {message && (
        <div className={`message ${messageType}`}>
          {messageType === 'success' ? '✅ ' : '❌ '}
          {message}
        </div>
      )}

      {/* Информация о поддерживаемых форматах */}
      <div style={{
        marginTop: '2rem',
        padding: '1rem',
        background: '#e3f2fd',
        borderRadius: '8px',
        border: '1px solid #bbdefb'
      }}>
        <h4 style={{ color: '#1976d2', marginBottom: '0.5rem' }}>ℹ️ Поддерживаемые форматы:</h4>
        <ul style={{ margin: 0, paddingLeft: '1.5rem', color: '#1976d2' }}>
          <li><strong>PDF</strong> - Документы Adobe PDF</li>
          <li><strong>DOC/DOCX</strong> - Документы Microsoft Word</li>
          <li><strong>TXT</strong> - Текстовые файлы</li>
          <li><strong>JPG/PNG</strong> - Изображения (с OCR)</li>
        </ul>
      </div>
    </div>
  );
}