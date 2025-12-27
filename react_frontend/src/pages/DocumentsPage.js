import { useState, useCallback } from 'react';
import Documents from '../components/Documents';
import SearchBar from '../components/SearchBar';
import './DocumentsPage.css';

function DocumentsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchMode, setSearchMode] = useState('filename');
  const [searchVisible, setSearchVisible] = useState(false);

  const handleSearch = useCallback((query) => {
    setSearchQuery(query);
  }, []);

  const handleSearchModeChange = useCallback((mode) => {
    setSearchMode(mode);
  }, []);

  return (
    <div className="documents-page">
      <button
        className="search-toggle-btn"
        onClick={() => setSearchVisible(!searchVisible)}
        title="Поиск документов"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
        </svg>
      </button>

      {searchVisible && (
        <div className="search-overlay" onClick={() => setSearchVisible(false)}>
          <div className="search-popup" onClick={(e) => e.stopPropagation()}>
            <div className="search-popup-header">
              <h3>Поиск документов</h3>
              <button
                className="search-close-btn"
                onClick={() => setSearchVisible(false)}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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

      <Documents searchQuery={searchQuery} searchMode={searchMode} />
    </div>
  );
}

export default DocumentsPage;
