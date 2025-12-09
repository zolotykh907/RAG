import './App.css';
import Sidebar from './components/Sidebar';
import MainPanel from './components/MainPanel';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Sidebar />
        <MainPanel />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;