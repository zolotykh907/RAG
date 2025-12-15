// Базовый URL для API
const API_BASE_URL = 'http://localhost:8000';

// Класс для работы с API
class ApiService {
  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  // Отправка запроса к RAG системе
  async sendQuery(question, sessionId = null) {
    try {
      const response = await fetch(`${this.baseUrl}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question,
          session_id: sessionId
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error sending query:', error);
      throw error;
    }
  }

  // Загрузка файла для постоянной индексации
  async uploadFile(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${this.baseUrl}/upload-files`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error uploading file:', error);
      throw error;
    }
  }

  // Загрузка файла для временной сессии
  async uploadTempFile(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${this.baseUrl}/upload-temp`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error uploading temp file:', error);
      throw error;
    }
  }

  // Очистка временной сессии
  async clearTempSession(sessionId) {
    try {
      const response = await fetch(`${this.baseUrl}/clear-temp/${sessionId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error clearing temp session:', error);
      throw error;
    }
  }

  // Проверка здоровья API
  async healthCheck() {
    try {
      const response = await fetch(`${this.baseUrl}/health`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error checking health:', error);
      throw error;
    }
  }

  // Получение конфигурации сервиса
  async getConfig(service) {
    try {
      const response = await fetch(`${this.baseUrl}/config?service=${service}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting config:', error);
      throw error;
    }
  }

  // Обновление конфигурации сервиса
  async updateConfig(service, config) {
    try {
      const response = await fetch(`${this.baseUrl}/config?service=${service}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error updating config:', error);
      throw error;
    }
  }

  // Перезагрузка сервиса с новой конфигурацией
  async reloadService(service) {
    try {
      const response = await fetch(`${this.baseUrl}/reload?service=${service}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error reloading service:', error);
      throw error;
    }
  }

  // Очистка всех индексированных данных
  async clearIndex() {
    try {
      const response = await fetch(`${this.baseUrl}/clear-index`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error clearing index:', error);
      throw error;
    }
  }

  // Получение списка документов
  async getDocuments() {
    try {
      const response = await fetch(`${this.baseUrl}/documents`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting documents:', error);
      throw error;
    }
  }

  // Получение содержимого документа (постоянного или временного)
  async getDocumentContent(filename, sessionId = null) {
    try {
      const url = sessionId
        ? `${this.baseUrl}/documents/${encodeURIComponent(filename)}?session_id=${sessionId}`
        : `${this.baseUrl}/documents/${encodeURIComponent(filename)}`;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting document content:', error);
      throw error;
    }
  }

  // Удаление документа
  async deleteDocument(filename) {
    try {
      const response = await fetch(`${this.baseUrl}/documents/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error deleting document:', error);
      throw error;
    }
  }

  // Поиск документов по содержимому
  async searchDocuments(query) {
    try {
      const response = await fetch(`${this.baseUrl}/search-documents?query=${encodeURIComponent(query)}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error searching documents:', error);
      throw error;
    }
  }

  // Получение информации о временных файлах для сессии
  async getTempFilesInfo(sessionId) {
    try {
      if (!sessionId) {
        return { temp_files: [], total_files: 0 };
      }

      const response = await fetch(`${this.baseUrl}/temp-files/${sessionId}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting temp files info:', error);
      throw error;
    }
  }

  // Удаление временного файла
  async deleteTempFile(sessionId, filename) {
    try {
      const response = await fetch(`${this.baseUrl}/temp-files/${sessionId}/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error deleting temp file:', error);
      throw error;
    }
  }

  // Получение всех статей
  async getArticles() {
    try {
      const response = await fetch(`${this.baseUrl}/articles`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting articles:', error);
      throw error;
    }
  }

  // Добавление новой статьи
  async addArticle(article) {
    try {
      const response = await fetch(`${this.baseUrl}/articles`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(article),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error adding article:', error);
      throw error;
    }
  }

  // Удаление статьи
  async deleteArticle(articleId) {
    try {
      const response = await fetch(`${this.baseUrl}/articles/${articleId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error deleting article:', error);
      throw error;
    }
  }

  // Обновление статьи
  async updateArticle(articleId, article) {
    try {
      const response = await fetch(`${this.baseUrl}/articles/${articleId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(article),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error updating article:', error);
      throw error;
    }
  }
}

// Экспортируем единственный экземпляр сервиса
const apiService = new ApiService();
export default apiService;
