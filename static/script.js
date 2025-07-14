class RAGInterface {
    constructor() {
        this.apiUrl = 'http://localhost:8000/query';
        this.requestsToday = 0;
        this.history = JSON.parse(localStorage.getItem('rag_history') || '[]');
        this.settings = JSON.parse(localStorage.getItem('rag_settings') || '{"showSources": true, "autoScroll": true}');
        
        this.initializeElements();
        this.bindEvents();
        this.loadHistory();
        this.applySettings();
        this.checkSystemStatus();
    }

    initializeElements() {
        this.elements = {
            questionForm: document.getElementById('questionForm'),
            questionInput: document.getElementById('questionInput'),
            sendButton: document.getElementById('sendButton'),
            chatMessages: document.getElementById('chatMessages'),
            loadingOverlay: document.getElementById('loadingOverlay'),
            requestsToday: document.getElementById('requestsToday'),
            systemStatus: document.getElementById('systemStatus'),
            historyList: document.getElementById('historyList'),
            clearHistory: document.getElementById('clearHistory'),
            showSources: document.getElementById('showSources'),
            autoScroll: document.getElementById('autoScroll')
        };
    }

    bindEvents() {
        // Form submission
        this.elements.questionForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendQuestion();
        });

        // Enter key in input
        this.elements.questionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendQuestion();
            }
        });

        // Clear history
        this.elements.clearHistory.addEventListener('click', () => {
            this.clearHistory();
        });

        // Settings changes
        this.elements.showSources.addEventListener('change', () => {
            this.settings.showSources = this.elements.showSources.checked;
            this.saveSettings();
        });

        this.elements.autoScroll.addEventListener('change', () => {
            this.settings.autoScroll = this.elements.autoScroll.checked;
            this.saveSettings();
        });

        // History item clicks
        this.elements.historyList.addEventListener('click', (e) => {
            if (e.target.classList.contains('history-item')) {
                this.elements.questionInput.value = e.target.textContent;
                this.elements.questionInput.focus();
            }
        });
    }

    async sendQuestion() {
        const question = this.elements.questionInput.value.trim();
        if (!question) return;

        // Disable input and button
        this.elements.questionInput.disabled = true;
        this.elements.sendButton.disabled = true;

        // Add user message
        this.addMessage(question, 'user');

        // Clear input
        this.elements.questionInput.value = '';

        // Show loading
        this.showLoading();

        try {
            const response = await this.makeApiRequest(question);
            this.handleResponse(response);
        } catch (error) {
            this.handleError(error);
        } finally {
            this.hideLoading();
            this.elements.questionInput.disabled = false;
            this.elements.sendButton.disabled = false;
            this.elements.questionInput.focus();
        }
    }

    async makeApiRequest(question) {
        const response = await fetch(this.apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    handleResponse(response) {
        const { answer, texts } = response;
        
        // Add assistant message
        this.addMessage(answer, 'assistant', texts);
        
        // Update stats
        this.requestsToday++;
        this.elements.requestsToday.textContent = this.requestsToday;
        
        // Add to history
        this.addToHistory(answer);
    }

    handleError(error) {
        console.error('Error:', error);
        const errorMessage = `Произошла ошибка при обработке запроса: ${error.message}`;
        this.addMessage(errorMessage, 'assistant');
    }

    addMessage(content, type, sources = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (type === 'system') {
            messageContent.innerHTML = `<i class="fas fa-info-circle"></i><p>${content}</p>`;
        } else if (type === 'user') {
            messageContent.textContent = content;
        } else if (type === 'assistant') {
            messageContent.innerHTML = `<p>${this.formatText(content)}</p>`;
            
            // Add sources if available and enabled
            if (sources && this.settings.showSources && sources.length > 0) {
                const sourcesDiv = document.createElement('div');
                sourcesDiv.className = 'sources';
                sourcesDiv.innerHTML = `
                    <h4><i class="fas fa-link"></i> Источники</h4>
                    ${sources.map((source, index) => `
                        <div class="source-item">
                            <strong>Источник ${index + 1}:</strong> ${this.truncateText(source, 200)}
                        </div>
                    `).join('')}
                `;
                messageContent.appendChild(sourcesDiv);
            }
        }
        
        messageDiv.appendChild(messageContent);
        this.elements.chatMessages.appendChild(messageDiv);
        
        // Auto scroll if enabled
        if (this.settings.autoScroll) {
            this.scrollToBottom();
        }
    }

    formatText(text) {
        // Convert line breaks to <br> tags
        return text.replace(/\n/g, '<br>');
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    scrollToBottom() {
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    showLoading() {
        this.elements.loadingOverlay.style.display = 'flex';
    }

    hideLoading() {
        this.elements.loadingOverlay.style.display = 'none';
    }

    addToHistory(question) {
        // Add to beginning of history
        this.history.unshift(question);
        
        // Keep only last 10 items
        if (this.history.length > 10) {
            this.history = this.history.slice(0, 10);
        }
        
        // Save to localStorage
        localStorage.setItem('rag_history', JSON.stringify(this.history));
        
        // Update UI
        this.loadHistory();
    }

    loadHistory() {
        const historyList = this.elements.historyList;
        
        if (this.history.length === 0) {
            historyList.innerHTML = '<p class="empty-history">История пуста</p>';
            return;
        }
        
        historyList.innerHTML = this.history.map(question => 
            `<div class="history-item">${this.truncateText(question, 50)}</div>`
        ).join('');
    }

    clearHistory() {
        if (confirm('Вы уверены, что хотите очистить историю?')) {
            this.history = [];
            localStorage.removeItem('rag_history');
            this.loadHistory();
        }
    }

    applySettings() {
        this.elements.showSources.checked = this.settings.showSources;
        this.elements.autoScroll.checked = this.settings.autoScroll;
    }

    saveSettings() {
        localStorage.setItem('rag_settings', JSON.stringify(this.settings));
    }

    async checkSystemStatus() {
        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: 'test' })
            });
            
            if (response.ok) {
                this.elements.systemStatus.textContent = 'Онлайн';
                this.elements.systemStatus.className = 'stat-value status-online';
            } else {
                throw new Error('API not responding');
            }
        } catch (error) {
            this.elements.systemStatus.textContent = 'Офлайн';
            this.elements.systemStatus.className = 'stat-value status-offline';
        }
    }

    // Utility method to add a system message
    addSystemMessage(message) {
        this.addMessage(message, 'system');
    }
}

// Initialize the interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const ragInterface = new RAGInterface();
    
    // Add welcome message
    setTimeout(() => {
        ragInterface.addSystemMessage('Система готова к работе! Задайте любой вопрос.');
    }, 1000);
    
    // Make interface globally available for debugging
    window.ragInterface = ragInterface;
});

// Add some utility functions
window.utils = {
    // Format timestamp
    formatTime: (date) => {
        return new Intl.DateTimeFormat('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    },
    
    // Debounce function
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Copy to clipboard
    copyToClipboard: async (text) => {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.error('Failed to copy: ', err);
            return false;
        }
    }
};