import { useEffect, useState } from 'react';
import apiService from '../services/api';
import './FileUpload.css';

const INDEXING_STARTING_MESSAGE = 'Сервис индексации запускается. Дождитесь завершения загрузки модели embeddings.';

// Компонент для загрузки файлов
function FileUpload({ onPermanentUpload }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [indexingReady, setIndexingReady] = useState(false);
  const [readinessMessage, setReadinessMessage] = useState('Проверяем готовность сервиса индексации...');
  const [checkingReadiness, setCheckingReadiness] = useState(true);

  useEffect(() => {
    let cancelled = false;
    let retryTimer = null;

    async function checkReadiness() {
      if (!cancelled) {
        setCheckingReadiness(true);
      }

      let ready = false;
      try {
        const readiness = await apiService.getIndexingReadiness();
        ready = readiness.status === 'ready';

        if (!cancelled) {
          setIndexingReady(ready);
          setReadinessMessage(ready ? null : readiness.message || INDEXING_STARTING_MESSAGE);
        }
      } catch (err) {
        if (!cancelled) {
          setIndexingReady(false);
          setReadinessMessage(err.message || INDEXING_STARTING_MESSAGE);
        }
      } finally {
        if (!cancelled) {
          setCheckingReadiness(false);
          if (!ready) {
            retryTimer = window.setTimeout(checkReadiness, 3000);
          }
        }
      }
    }

    checkReadiness();

    return () => {
      cancelled = true;
      if (retryTimer) {
        window.clearTimeout(retryTimer);
      }
    };
  }, []);

  // Обработка выбора файла
  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    setFile(selectedFile);
    setError(null);
    setSuccess(null);
  };

  // Обработка загрузки файла в базу
  const handlePermanentUpload = async () => {
    if (!file) {
      setError('Пожалуйста, выберите файл');
      return;
    }

    if (!indexingReady) {
      setError(readinessMessage || INDEXING_STARTING_MESSAGE);
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      await onPermanentUpload(file);
      setSuccess('Файл успешно загружен и проиндексирован в базе данных!');
      setFile(null);

      const fileInput = document.getElementById('file-input');
      if (fileInput) {
        fileInput.value = '';
      }
    } catch (err) {
      setError(`Ошибка при загрузке: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload-container">
      <div className="file-upload-card">
        <div className="file-input-wrapper">
          <input
            id="file-input"
            type="file"
            onChange={handleFileChange}
            accept=".txt,.pdf,.doc,.docx"
            disabled={uploading || !indexingReady}
          />
          <label
            htmlFor="file-input"
            className={`file-input-label${!indexingReady ? ' disabled' : ''}`}
          >
            {!indexingReady ? (
              <>
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <path d="M12 6v6l4 2"></path>
                </svg>
                <span className="file-label-text">Сервис индексации запускается</span>
                <span className="file-label-hint">
                  {checkingReadiness ? 'Проверяем готовность...' : readinessMessage}
                </span>
              </>
            ) : file ? (
              <>
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
                  <polyline points="13 2 13 9 20 9"></polyline>
                </svg>
                <span className="file-label-text">{file.name}</span>
                <span className="file-label-hint">Нажмите, чтобы выбрать другой файл</span>
              </>
            ) : (
              <>
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
                <span className="file-label-text">Нажмите для выбора файла</span>
                <span className="file-label-hint">или перетащите файл сюда</span>
              </>
            )}
          </label>
        </div>

        <div className="upload-buttons">
          <button
            onClick={handlePermanentUpload}
            disabled={!file || uploading || !indexingReady}
            className="upload-button upload-button-permanent"
          >
            {!indexingReady ? 'Сервис запускается' : uploading ? 'Загрузка...' : 'Загрузить в базу'}
          </button>
        </div>

        {!indexingReady && (
          <div className="upload-message pending-message">
            {checkingReadiness ? 'Проверяем готовность сервиса индексации...' : readinessMessage}
          </div>
        )}
        {error && <div className="upload-message error-message">{error}</div>}
        {success && <div className="upload-message success-message">{success}</div>}
      </div>
    </div>
  );
}

export default FileUpload;
