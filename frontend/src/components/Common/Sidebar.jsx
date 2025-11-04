import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FaHome, FaChartLine, FaWallet, FaCog, FaHistory } from 'react-icons/fa';

const Sidebar = () => {
  const location = useLocation();

  const menuItems = [
    { path: '/dashboard', icon: <FaHome />, label: 'Dashboard' },
    { path: '/trade', icon: <FaChartLine />, label: 'Trade' },
    { path: '/wallet', icon: <FaWallet />, label: 'Wallet' },
    { path: '/history', icon: <FaHistory />, label: 'History' },
    { path: '/settings', icon: <FaCog />, label: 'Settings' }
  ];

  return (
    <div style={{
      width: '250px',
      background: 'var(--dark)',
      height: '100vh',
      borderRight: '1px solid var(--border)',
      padding: '20px 0',
      position: 'fixed',
      left: 0,
      top: 0
    }}>
      {menuItems.map(item => (
        <Link
          key={item.path}
          to={item.path}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '16px 24px',
            color: location.pathname === item.path ? 'var(--primary)' : 'var(--text)',
            background: location.pathname === item.path ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
            textDecoration: 'none',
            transition: 'all 0.3s ease'
          }}
        >
          <span style={{ fontSize: '20px' }}>{item.icon}</span>
          <span>{item.label}</span>
        </Link>
      ))}
    </div>
  );
};

export default Sidebar;