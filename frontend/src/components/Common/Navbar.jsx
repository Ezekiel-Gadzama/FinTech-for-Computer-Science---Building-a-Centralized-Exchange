import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Navbar = () => {
  const { user, logoutUser } = useAuth();

  return (
    <nav className="navbar">
      <div className="navbar-content">
        <Link to="/" className="logo">CryptoEx</Link>

        <div className="nav-links">
          <Link to="/dashboard" className="nav-link">Dashboard</Link>
          <Link to="/trade" className="nav-link">Trade</Link>
          <Link to="/wallet" className="nav-link">Wallet</Link>

          {user && (
            <>
              <span style={{ color: 'var(--text-secondary)' }}>{user.username}</span>
              <button onClick={logoutUser} className="btn btn-primary">
                Logout
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;