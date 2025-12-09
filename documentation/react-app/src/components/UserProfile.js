import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

function UserProfile() {
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  if (!user) return null;

  return (
    <div className="user-profile-container" ref={dropdownRef}>
      <button
        className="user-profile-btn"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="User menu"
      >
        <div className="user-profile-avatar">
          {user.email.charAt(0).toUpperCase()}
        </div>
      </button>

      {isOpen && (
        <div className="user-dropdown">
          <div className="user-dropdown-header">
            <div className="user-dropdown-avatar">
              {user.email.charAt(0).toUpperCase()}
            </div>
            <div className="user-dropdown-info">
              <p className="user-dropdown-email">{user.email}</p>
              <span className={`user-dropdown-role ${user.role.name === 'admin' ? 'role-admin' : 'role-user'}`}>
                {user.role.name === 'admin' ? '👑 Администратор' : '👤 Пользователь'}
              </span>
            </div>
          </div>

          <div className="user-dropdown-divider"></div>

          <button
            onClick={() => {
              logout();
              setIsOpen(false);
            }}
            className="user-dropdown-logout"
          >
            🚪 Выйти
          </button>
        </div>
      )}
    </div>
  );
}

export default UserProfile;
