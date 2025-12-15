import { useState, useEffect } from 'react';
import apiService from '../services/api';
import './Documents.css';

// Компонент для управления документами
function Documents({ searchQuery = '', searchMode = 'filename' }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [docContent, setDocContent] = useState(null);
  const [loadingContent, setLoadingContent] = useState(false);
  const [totalChunks, setTotalChunks] = useState(0);
  const [searchResults, setSearchResults] = useState(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  // Поиск по содержимому при изменении запроса
  useEffect(() => {
    const performSearch = async () => {
      if (searchMode === 'content' && searchQuery) {
        try {
          const results = await apiService.searchDocuments(searchQuery);
          setSearchResults(results);
        } catch (error) {
          console.error('Error searching documents:', error);
          setSearchResults({ results: [], total_results: 0 });
        }
      } else {
        setSearchResults(null);
      }
    };

    const debounceTimer = setTimeout(performSearch, 300);
    return () => clearTimeout(debounceTimer);
  }, [searchQuery, searchMode]);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const data = await apiService.getDocuments();
      setDocuments(data.documents || []);
      setTotalChunks(data.total_chunks || 0);
    } catch (error) {
      console.error('Error loading documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentClick = async (filename) => {
    setSelectedDoc(filename);
    setLoadingContent(true);
    try {
      const content = await apiService.getDocumentContent(filename);
      setDocContent(content);
    } catch (error) {
      console.error('Error loading document content:', error);
      setDocContent(null);
    } finally {
      setLoadingContent(false);
    }
  };

  const handleDeleteDocument = async (filename, e) => {
    e.stopPropagation();

    if (!window.confirm(`Вы уверены, что хотите удалить документ "${filename}"?`)) {
      return;
    }

    try {
      await apiService.deleteDocument(filename);
      await loadDocuments();
      if (selectedDoc === filename) {
        setSelectedDoc(null);
        setDocContent(null);
      }
      alert('Документ успешно удален');
    } catch (error) {
      alert(`Ошибка при удалении документа: ${error.message}`);
    }
  };

  const handleClosePreview = () => {
    setSelectedDoc(null);
    setDocContent(null);
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  // Фильтрация документов в зависимости от режима поиска
  const getDisplayDocuments = () => {
    if (searchMode === 'content' && searchResults) {
      // При поиске по содержимому показываем результаты с бэкенда
      return searchResults.results.map(result => {
        const doc = documents.find(d => d.filename === result.filename);
        return {
          ...doc,
          filename: result.filename,
          total_chunks: result.total_matches,
          matches: result.matches
        };
      });
    } else {
      // При поиске по названию фильтруем локально
      return documents.filter(doc =>
        doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
  };

  const filteredDocuments = getDisplayDocuments();

  return (
    <div className="documents-container">
      <div className="documents-header">
        <div>
          <h2>Документы</h2>
          <p>Управление индексированными документами</p>
        </div>
        <div className="documents-stats">
          <div className="stat-item">
            <span className="stat-label">Всего документов:</span>
            <span className="stat-value">{documents.length}</span>
          </div>
          {searchQuery && (
            <div className="stat-item">
              <span className="stat-label">Найдено:</span>
              <span className="stat-value">{filteredDocuments.length}</span>
            </div>
          )}
          <div className="stat-item">
            <span className="stat-label">Всего фрагментов:</span>
            <span className="stat-value">{totalChunks}</span>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="documents-loading">
          <div className="spinner-large"></div>
          <p>Загрузка документов...</p>
        </div>
      ) : documents.length === 0 ? (
        <div className="documents-empty">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
            <polyline points="13 2 13 9 20 9"></polyline>
          </svg>
          <h3>Нет индексированных документов</h3>
          <p>Загрузите документы на вкладке "Загрузка файлов"</p>
        </div>
      ) : filteredDocuments.length === 0 ? (
        <div className="documents-empty">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
          <h3>Документы не найдены</h3>
          <p>По запросу "{searchQuery}" ничего не найдено</p>
        </div>
      ) : (
        <div className="documents-grid">
          {filteredDocuments.map((doc) => (
            <div
              key={doc.filename}
              className="document-card"
              onClick={() => handleDocumentClick(doc.filename)}
            >
              <div className="document-card-header">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
                  <polyline points="13 2 13 9 20 9"></polyline>
                </svg>
                <button
                  className="delete-doc-btn"
                  onClick={(e) => handleDeleteDocument(doc.filename, e)}
                  title="Удалить документ"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                </button>
              </div>
              <h4 className="document-title">{doc.filename}</h4>
              {searchMode === 'content' && doc.matches && (
                <div className="search-matches">
                  <div className="match-count">Найдено совпадений: {doc.total_chunks}</div>
                  {doc.matches.slice(0, 2).map((match, idx) => (
                    <div key={idx} className="match-preview">
                      {match.text}
                    </div>
                  ))}
                </div>
              )}
              <div className="document-meta">
                <div className="meta-item">
                  <span className="meta-label">Фрагментов:</span>
                  <span className="meta-value">{doc.total_chunks}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Размер:</span>
                  <span className="meta-value">{formatBytes(doc.total_chars)}</span>
                </div>
                <div className="meta-item meta-date">
                  <span className="meta-label">Добавлен:</span>
                  <span className="meta-value">
                    {doc.first_added !== 'N/A'
                      ? new Date(doc.first_added).toLocaleDateString()
                      : 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Модальное окно предпросмотра */}
      {selectedDoc && (
        <div className="document-modal-overlay" onClick={handleClosePreview}>
          <div className="document-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selectedDoc}</h3>
              <button className="modal-close-btn" onClick={handleClosePreview}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>

            <div className="modal-content">
              {loadingContent ? (
                <div className="modal-loading">
                  <div className="spinner-large"></div>
                  <p>Загрузка содержимого...</p>
                </div>
              ) : docContent ? (
                <>
                  <div className="modal-stats">
                    <span>Всего фрагментов: {docContent.total_chunks}</span>
                    <span>Всего символов: {docContent.total_chars.toLocaleString()}</span>
                  </div>
                  <div className="chunks-list">
                    {docContent.chunks.map((chunk, index) => (
                      <div key={index} className="chunk-item">
                        <div className="chunk-header">
                          <span className="chunk-number">Фрагмент #{index + 1}</span>
                          <span className="chunk-length">{chunk.text.length} символов</span>
                        </div>
                        <div className="chunk-text">{chunk.text}</div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="modal-error">
                  <p>Не удалось загрузить содержимое документа</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Documents;
