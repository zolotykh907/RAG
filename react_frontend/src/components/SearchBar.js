import { useState, useEffect } from 'react';
import './SearchBar.css';

// Компонент для поиска по сайту
function SearchBar({ onSearch, placeholder = "Поиск...", onModeChange, searchMode = 'filename' }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      onSearch(searchQuery);
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchQuery, onSearch]);

  const handleClear = () => {
    setSearchQuery('');
    setIsExpanded(false);
  };

  const handleFocus = () => {
    setIsExpanded(true);
  };

  const handleBlur = () => {
    if (!searchQuery) {
      setIsExpanded(false);
    }
  };

  const toggleSearchMode = () => {
    if (onModeChange) {
      const newMode = searchMode === 'filename' ? 'content' : 'filename';
      onModeChange(newMode);
    }
  };

  return (
    <div className={`search-bar ${isExpanded ? 'expanded' : ''}`}>
      <div className="search-controls">
        <div className="search-input-wrapper">
          <svg
            className="search-icon"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>

          <input
            type="text"
            className="search-input"
            placeholder={placeholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={handleFocus}
            onBlur={handleBlur}
          />

          {searchQuery && (
            <button
              className="search-clear-btn"
              onClick={handleClear}
              type="button"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          )}
        </div>

        {onModeChange && (
          <button
            className="search-mode-btn"
            onClick={toggleSearchMode}
            type="button"
            title={searchMode === 'filename' ? 'Поиск по названию' : 'Поиск по содержимому'}
          >
            {searchMode === 'filename' ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
                <polyline points="13 2 13 9 20 9"></polyline>
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
            )}
            <span className="mode-label">
              {searchMode === 'filename' ? 'Название' : 'Содержимое'}
            </span>
          </button>
        )}
      </div>

      {searchQuery && (
        <div className="search-results-count">
          Поиск: "{searchQuery}"
        </div>
      )}
    </div>
  );
}

export default SearchBar;
