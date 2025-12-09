import {Routes, Route, useLocation} from 'react-router-dom';
import Introduction from '../sections/Introduction';
import Description from '../sections/Description';
import Architecture from '../sections/Architecture';
import Technologies from '../sections/Technologies';
import Installation from '../sections/Installation';
import Usage from '../sections/Usage';
import Api from '../sections/Api';
import Testing from '../sections/Testing';
import Posts from '../sections/Posts';
import Flip from '../sections/Flip';
import Statistics from '../sections/Statistics';
import Login from '../pages/Login';
import Register from '../pages/Register';
import ProtectedRoute from './ProtectedRoute';
import UserProfile from './UserProfile';

const MainPanel = () => {
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';

  return (
    <main className={`main-content ${isAuthPage ? 'auth-page' : ''}`}>
      {!isAuthPage && <UserProfile />}
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route path="*" element={<ProtectedRoute><Introduction /></ProtectedRoute>} />
        <Route path="/introduction" element={<ProtectedRoute><Introduction /></ProtectedRoute>} />
        <Route path="/description" element={<ProtectedRoute><Description /></ProtectedRoute>} />
        <Route path="/architecture" element={<ProtectedRoute><Architecture /></ProtectedRoute>} />
        <Route path="/technologies" element={<ProtectedRoute><Technologies /></ProtectedRoute>} />
        <Route path="/installation" element={<ProtectedRoute><Installation /></ProtectedRoute>} />
        <Route path="/usage" element={<ProtectedRoute><Usage /></ProtectedRoute>} />
        <Route path="/api" element={<ProtectedRoute><Api /></ProtectedRoute>} />
        <Route path="/testing" element={<ProtectedRoute><Testing /></ProtectedRoute>} />
        <Route path="/posts" element={<ProtectedRoute><Posts /></ProtectedRoute>} />
        <Route path="/flip" element={<ProtectedRoute><Flip /></ProtectedRoute>} />
        <Route path="/statistics" element={<ProtectedRoute adminOnly><Statistics /></ProtectedRoute>} />
      </Routes>
    </main>
  );
};

export default MainPanel;

