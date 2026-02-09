import { useState, useCallback, useRef } from 'react';
import Documents from '../components/Documents';
import SearchBar from '../components/SearchBar';
import FileUpload from '../components/FileUpload';
import apiService from '../services/api';
import './DocumentsPage.css';

function DocumentsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchMode, setSearchMode] = useState('filename');
  const [searchVisible, setSearchVisible] = useState(false);
  const [uploadVisible, setUploadVisible] = useState(false);
  const documentsRef = useRef(null);

  const handleSearch = useCallback((query) => {
    setSearchQuery(query);
  }, []);

  const handleSearchModeChange = useCallback((mode) => {
    setSearchMode(mode);
  }, []);

  const handlePermanentUpload = async (file) => {
    const result = await apiService.uploadFile(file);
    if (documentsRef.current) {
      documentsRef.current.refresh();
    }
    return result;
  };

  const handleClearIndex = async () => {
    if (window.confirm('Вы уверены, что хотите удалить все индексированные документы? Это действие нельзя отменить.')) {
      try {
        await apiService.clearIndex();
        if (documentsRef.current) {
          documentsRef.current.refresh();
        }
      } catch (error) {
        alert(`Ошибка при удалении документов: ${error.message}`);
      }
    }
  };

  return (
    <div className="documents-page">
      <Documents ref={documentsRef} searchQuery={searchQuery} searchMode={searchMode} />

      {/* FAB-кнопки */}
      <div className="fab-group">
        <button
          className="fab-btn fab-upload"
          onClick={() => setUploadVisible(true)}
          title="Загрузить документ"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
        </button>
        <button
          className="fab-btn fab-search"
          onClick={() => setSearchVisible(true)}
          title="Поиск документов"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
        </button>
        <button
          className="fab-btn fab-clear"
          onClick={handleClearIndex}
          title="Очистить базу"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </div>

      {/* Модалка загрузки */}
      {uploadVisible && (
        <div className="modal-overlay" onClick={() => setUploadVisible(false)}>
          <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
            <div className="upload-modal-header">
              <h3>Загрузка документов</h3>
              <button className="modal-close-btn" onClick={() => setUploadVisible(false)}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            <div className="upload-modal-body">
              <p className="upload-modal-hint">
                Документ будет добавлен в постоянное хранилище и доступен во всех чатах
              </p>
              <FileUpload onPermanentUpload={handlePermanentUpload} />
            </div>
          </div>
        </div>
      )}

      {/* Модалка поиска */}
      {searchVisible && (
        <div className="modal-overlay" onClick={() => setSearchVisible(false)}>
          <div className="search-popup" onClick={(e) => e.stopPropagation()}>
            <div className="search-popup-header">
              <h3>Поиск документов</h3>
              <button className="modal-close-btn" onClick={() => setSearchVisible(false)}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            <SearchBar
              onSearch={handleSearch}
              placeholder="Поиск документов..."
              onModeChange={handleSearchModeChange}
              searchMode={searchMode}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default DocumentsPage;
