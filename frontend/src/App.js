import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import ChatPage from './pages/ChatPage';
import ConfigPage from './pages/ConfigPage';
import UploadPage from './pages/UploadPage';
import DocumentationPage from './pages/DocumentationPage';
import './styles.css';

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<ChatPage />} />
        <Route path="config" element={<ConfigPage />} />
        <Route path="upload" element={<UploadPage />} />
        <Route path="documentation" element={<DocumentationPage />} />
      </Route>
    </Routes>
  );
};

export default App;