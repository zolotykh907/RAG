import { useState } from 'react';
import './AddArticleModal.css';

function AddArticleModal({ isOpen, onClose, onAdd }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    url: '',
    tags: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Валидация
    if (!formData.title.trim() || !formData.description.trim() || !formData.url.trim()) {
      alert('Пожалуйста, заполните все обязательные поля');
      return;
    }

    // Преобразуем теги из строки в массив
    const tagsArray = formData.tags
      .split(',')
      .map(tag => tag.trim())
      .filter(tag => tag.length > 0);

    const newArticle = {
      title: formData.title.trim(),
      description: formData.description.trim(),
      url: formData.url.trim(),
      tags: tagsArray
    };

    onAdd(newArticle);

    // Очищаем форму
    setFormData({
      title: '',
      description: '',
      url: '',
      tags: ''
    });
  };

  const handleClose = () => {
    setFormData({
      title: '',
      description: '',
      url: '',
      tags: ''
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Добавить статью</h2>
          <button className="close-button" onClick={handleClose}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="article-form">
          <div className="form-group">
            <label htmlFor="title">
              Название статьи <span className="required">*</span>
            </label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              placeholder="Введите название статьи"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">
              Описание <span className="required">*</span>
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Краткое описание статьи"
              rows="4"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="url">
              Ссылка <span className="required">*</span>
            </label>
            <input
              type="url"
              id="url"
              name="url"
              value={formData.url}
              onChange={handleChange}
              placeholder="https://example.com/article"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="tags">
              Теги (через запятую)
            </label>
            <input
              type="text"
              id="tags"
              name="tags"
              value={formData.tags}
              onChange={handleChange}
              placeholder="RAG, AI, ML"
            />
            <span className="form-hint">Например: RAG, Векторные БД, Python</span>
          </div>

          <div className="form-actions">
            <button type="button" className="cancel-button" onClick={handleClose}>
              Отмена
            </button>
            <button type="submit" className="submit-button">
              Добавить статью
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default AddArticleModal;
