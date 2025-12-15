import { BrowserRouter as Router } from 'react-router-dom';
import HomePage from './pages/HomePage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <HomePage />
      </div>
    </Router>
  );
}

export default App;
