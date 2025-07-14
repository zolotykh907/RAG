import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Query from './components/Query';
import Upload from './components/Upload';
import Config from './components/Config';

function App() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<Query />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/config" element={<Config />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;