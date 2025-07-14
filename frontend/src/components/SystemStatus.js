import React, { useState, useEffect } from 'react';
import { Activity, RefreshCw, CheckCircle, AlertCircle, Server, Database, Cpu } from 'lucide-react';
import axios from 'axios';

const SystemStatus = ({ status, setStatus }) => {
  const [loading, setLoading] = useState(false);
  const [lastChecked, setLastChecked] = useState(null);

  const checkSystemStatus = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/health');
      setStatus({
        healthy: true,
        data: response.data,
        timestamp: new Date()
      });
    } catch (error) {
      setStatus({
        healthy: false,
        error: error.message,
        timestamp: new Date()
      });
    } finally {
      setLoading(false);
      setLastChecked(new Date());
    }
  };

  useEffect(() => {
    checkSystemStatus();
  }, []);

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    return timestamp.toLocaleString('ru-RU');
  };

  const getStatusIcon = (healthy) => {
    if (healthy) {
      return <CheckCircle className="h-5 w-5 text-green-600" />;
    }
    return <AlertCircle className="h-5 w-5 text-red-600" />;
  };

  const getStatusText = (healthy) => {
    if (healthy) {
      return 'Система работает';
    }
    return 'Ошибка системы';
  };

  const getStatusColor = (healthy) => {
    if (healthy) {
      return 'text-green-800 bg-green-50 border-green-200';
    }
    return 'text-red-800 bg-red-50 border-red-200';
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <Activity className="h-5 w-5 mr-2" />
            Статус системы
          </h2>
          <button
            onClick={checkSystemStatus}
            disabled={loading}
            className="btn-secondary flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Обновить</span>
          </button>
        </div>

        {/* Основной статус */}
        {status && (
          <div className={`p-4 rounded-lg border ${getStatusColor(status.healthy)}`}>
            <div className="flex items-center space-x-3">
              {getStatusIcon(status.healthy)}
              <div>
                <h3 className="font-medium">{getStatusText(status.healthy)}</h3>
                {status.data && (
                  <p className="text-sm opacity-80">{status.data.message}</p>
                )}
                {status.error && (
                  <p className="text-sm opacity-80">Ошибка: {status.error}</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Детальная информация */}
        {status?.data && (
          <div className="mt-6 space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Детальная информация</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* API статус */}
              <div className="p-4 bg-gray-50 rounded-lg border">
                <div className="flex items-center space-x-2 mb-2">
                  <Server className="h-4 w-4 text-gray-600" />
                  <span className="font-medium text-gray-900">API сервер</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${status.healthy ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <span className="text-sm text-gray-600">
                    {status.healthy ? 'Работает' : 'Недоступен'}
                  </span>
                </div>
              </div>

              {/* База данных */}
              <div className="p-4 bg-gray-50 rounded-lg border">
                <div className="flex items-center space-x-2 mb-2">
                  <Database className="h-4 w-4 text-gray-600" />
                  <span className="font-medium text-gray-900">Векторная БД</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${status.healthy ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <span className="text-sm text-gray-600">
                    {status.healthy ? 'Доступна' : 'Недоступна'}
                  </span>
                </div>
              </div>

              {/* LLM сервер */}
              <div className="p-4 bg-gray-50 rounded-lg border">
                <div className="flex items-center space-x-2 mb-2">
                  <Cpu className="h-4 w-4 text-gray-600" />
                  <span className="font-medium text-gray-900">LLM сервер</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${status.healthy ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <span className="text-sm text-gray-600">
                    {status.healthy ? 'Работает' : 'Недоступен'}
                  </span>
                </div>
              </div>

              {/* Время последней проверки */}
              <div className="p-4 bg-gray-50 rounded-lg border">
                <div className="flex items-center space-x-2 mb-2">
                  <Activity className="h-4 w-4 text-gray-600" />
                  <span className="font-medium text-gray-900">Последняя проверка</span>
                </div>
                <span className="text-sm text-gray-600">
                  {formatTimestamp(lastChecked)}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Информация о системе */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <h3 className="text-sm font-medium text-blue-900 mb-2">Информация о системе</h3>
          <div className="text-sm text-blue-800 space-y-1">
            <p>• RAG System API v1.0.0</p>
            <p>• Поддерживаемые форматы: PDF, DOC, DOCX, TXT, JPG, PNG</p>
            <p>• Модель эмбеддингов: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2</p>
            <p>• LLM: Llama3 (локально через Ollama)</p>
            <p>• Векторная БД: FAISS</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemStatus; 