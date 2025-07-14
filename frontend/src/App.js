import React, { useState } from 'react';
import Header from './components/Header';
import ChatContainer from './components/ChatContainer';
import Sidebar from './components/Sidebar';
import LoadingOverlay from './components/LoadingOverlay';
import './styles.css';

const App = () => {
  const [isLoading, setIsLoading] = useState(false);

  return (
    <div className="container">
      <Header />
      <main className="main-content">
        <ChatContainer onLoadingChange={setIsLoading} />
        <Sidebar />
      </main>
      {isLoading && <LoadingOverlay />}
    </div>
  );
};

export default App;