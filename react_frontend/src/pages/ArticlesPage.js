import { useState, useEffect } from 'react';
import AddArticleModal from '../components/AddArticleModal';
import apiService from '../services/api';
import './ArticlesPage.css';

function ArticlesPage() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [error, setError] = useState(null);

  // Загрузка статей при монтировании компонента
  useEffect(() => {
    loadArticles();
  }, []);

  const loadArticles = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getArticles();
      setArticles(data);
    } catch (err) {
      console.error('Ошибка при загрузке статей:', err);
      setError('Не удалось загрузить статьи');
    } finally {
      setLoading(false);
    }
  };

  const handleAddArticle = async (newArticle) => {
    try {
      const addedArticle = await apiService.addArticle(newArticle);
      setArticles([...articles, addedArticle]);
      setIsModalOpen(false);
    } catch (err) {
      console.error('Ошибка при добавлении статьи:', err);
      alert('Не удалось добавить статью. Попробуйте еще раз.');
    }
  };

  const handleDeleteArticle = async (articleId) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту статью?')) {
      return;
    }

    try {
      await apiService.deleteArticle(articleId);
      setArticles(articles.filter(article => article.id !== articleId));
    } catch (err) {
      console.error('Ошибка при удалении статьи:', err);
      alert('Не удалось удалить статью. Попробуйте еще раз.');
    }
  };

  if (loading) {
    return (
      <div className="articles-page">
        <div className="loading-state">
          <p>Загрузка статей...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="articles-page">
        <div className="error-state">
          <p>{error}</p>
          <button onClick={loadArticles} className="retry-button">
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="articles-page">
      <div className="articles-header">
        <div>
          <h1>Статьи и материалы</h1>
          <p>Полезные ресурсы по RAG-системам, векторным базам данных и языковым моделям</p>
        </div>
        <button className="add-article-button" onClick={() => setIsModalOpen(true)}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          Добавить статью
        </button>
      </div>

      <div className="articles-grid">
        {articles.map(article => (
          <article key={article.id} className="article-card">
            <div className="article-card-header">
              <h3>{article.title}</h3>
              <button
                className="delete-article-button"
                onClick={() => handleDeleteArticle(article.id)}
                title="Удалить статью"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>

            <p className="article-description">{article.description}</p>

            <div className="article-tags">
              {article.tags && article.tags.map((tag, index) => (
                <span key={index} className="tag">{tag}</span>
              ))}
            </div>

            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="article-link"
            >
              Читать статью
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                <polyline points="15 3 21 3 21 9"></polyline>
                <line x1="10" y1="14" x2="21" y2="3"></line>
              </svg>
            </a>
          </article>
        ))}
      </div>

      {articles.length === 0 && (
        <div className="empty-state">
          <p>Статьи не найдены</p>
          <button className="add-article-button" onClick={() => setIsModalOpen(true)}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            Добавить первую статью
          </button>
        </div>
      )}

      <AddArticleModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onAdd={handleAddArticle}
      />
    </div>
  );
}

export default ArticlesPage;
