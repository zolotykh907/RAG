
import './App.css';
import Sidebar from './Sidebar';
import MainPanel from './MainPanel';
import { BrowserRouter } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <div className="container">
        <Sidebar />
        <MainPanel />
      </div>
    </BrowserRouter>
  );
}

export default App;
