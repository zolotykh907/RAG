import './App.css';
import Sidebar from './components/Sidebar';
import MainPanel from './components/MainPanel';
import { BrowserRouter } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
        <Sidebar />
        <MainPanel />
    </BrowserRouter>
  );
}

export default App;