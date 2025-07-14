import React, { useState } from 'react';
import Header from './components/Header';
import FileUpload from './components/FileUpload';
import QueryInterface from './components/QueryInterface';
import SystemStatus from './components/SystemStatus';
import { Brain, Upload, Search, Activity } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('query');
  const [systemStatus, setSystemStatus] = useState(null);

  const tabs = [
    { id: 'query', name: 'Запросы', icon: Search },
    { id: 'upload', name: 'Загрузка файлов', icon: Upload },
    { id: 'status', name: 'Статус системы', icon: Activity },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {/* Навигация по вкладкам */}
        <div className="flex justify-center mb-8">
          <div className="flex space-x-1 bg-white rounded-lg p-1 shadow-sm">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all duration-200 ${
                    activeTab === tab.id
                      ? 'bg-primary-600 text-white shadow-sm'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <Icon size={18} />
                  <span className="font-medium">{tab.name}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Контент вкладок */}
        <div className="max-w-4xl mx-auto">
          {activeTab === 'query' && (
            <div className="animate-fade-in">
              <QueryInterface />
            </div>
          )}
          
          {activeTab === 'upload' && (
            <div className="animate-fade-in">
              <FileUpload />
            </div>
          )}
          
          {activeTab === 'status' && (
            <div className="animate-fade-in">
              <SystemStatus status={systemStatus} setStatus={setSystemStatus} />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App; 