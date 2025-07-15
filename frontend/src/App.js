import React, { useState } from 'react';
import Header from './components/Header';
import ChatContainer from './components/ChatContainer';
import Sidebar from './components/Sidebar';
import LoadingOverlay from './components/LoadingOverlay';
import Navigation from './components/Navigation';
import Config from './components/Config';
import Upload from './components/Upload';
import ConfigSidebar from './components/ConfigSidebar'
import ServiceSelector from './components/ServiceSelector'
import ConfigButtons from './components/ConfigButtons'
import './styles.css';



const App = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const [selectedService, setSelectedService] = useState('query');


  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  return (
    <div className="container">
      <Header />
      <Navigation onTabChange={handleTabChange} />
      <main className="main-content">
        {activeTab === 'chat' && (
          <>
            <ChatContainer onLoadingChange={setIsLoading} />
            <Sidebar />
          </>
        )}
        {activeTab === 'config' && (
          <>
            <Config
              onLoadingChange={setIsLoading}
              selectedService={selectedService}
            />
            <ConfigSidebar
              selectedService={selectedService}
              onSelectService={setSelectedService}
            />
          </>
        )}
        {activeTab === 'upload' && (
          <Upload onLoadingChange={setIsLoading} />
        )}
      </main>
      {isLoading && <LoadingOverlay />}
    </div>
  );
};

export default App;