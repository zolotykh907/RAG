// Базовый URL для API
// В микросервисной архитектуре все запросы идут через Gateway
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

class ApiService {
  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  async sendQuery(question, sessionId = null) {
    try {
      const response = await fetch(`${this.baseUrl}/query/ask`, {
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

  async uploadFile(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${this.baseUrl}/indexing/upload`, {
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

  async uploadTempFile(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${this.baseUrl}/query/upload-temp`, {
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

  async clearTempSession(sessionId) {
    try {
      const response = await fetch(`${this.baseUrl}/query/sessions/${sessionId}`, {
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

  async getConfig(service) {
    try {
      const response = await fetch(`${this.baseUrl}/indexing/config?service=${service}`);

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

  async updateConfig(service, config) {
    try {
      const response = await fetch(`${this.baseUrl}/indexing/config?service=${service}`, {
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

  async reloadService(service) {
    try {
      const response = await fetch(`${this.baseUrl}/indexing/reload?service=${service}`, {
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

  async clearIndex() {
    try {
      const response = await fetch(`${this.baseUrl}/indexing/clear-index`, {
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

  async getDocuments() {
    try {
      const response = await fetch(`${this.baseUrl}/indexing/documents`);

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

  async getDocumentContent(filename, sessionId = null) {
    try {
      const url = sessionId
        ? `${this.baseUrl}/indexing/documents/${encodeURIComponent(filename)}?session_id=${sessionId}`
        : `${this.baseUrl}/indexing/documents/${encodeURIComponent(filename)}`;

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

  async deleteDocument(filename) {
    try {
      const response = await fetch(`${this.baseUrl}/indexing/documents/${encodeURIComponent(filename)}`, {
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

  async searchDocuments(query) {
    try {
      const response = await fetch(`${this.baseUrl}/indexing/search-documents?query=${encodeURIComponent(query)}`);

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

  async getTempFilesInfo(sessionId) {
    try {
      if (!sessionId) {
        return { temp_files: [], total_files: 0 };
      }

      const response = await fetch(`${this.baseUrl}/query/sessions/${sessionId}/files`);

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

  async deleteTempFile(sessionId, filename) {
    try {
      const response = await fetch(`${this.baseUrl}/query/sessions/${sessionId}/files/${encodeURIComponent(filename)}`, {
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

  // Статьи
  async getArticles() {
    try {
      const response = await fetch(`${this.baseUrl}/indexing/articles`);

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

  async addArticle(article) {
    try {
      const response = await fetch(`${this.baseUrl}/indexing/articles`, {
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

  async deleteArticle(articleId) {
    try {
      const response = await fetch(`${this.baseUrl}/indexing/articles/${articleId}`, {
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

  async updateArticle(articleId, article) {
    try {
      const response = await fetch(`${this.baseUrl}/indexing/articles/${articleId}`, {
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

const apiService = new ApiService();
export default apiService;
