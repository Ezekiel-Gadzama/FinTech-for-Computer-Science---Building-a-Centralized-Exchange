import React from 'react';

const Footer = () => {
  return (
    <footer style={{
      background: 'var(--dark)',
      borderTop: '1px solid var(--border)',
      padding: '32px 0',
      marginTop: '64px'
    }}>
      <div className="container">
        <div className="grid grid-4">
          <div>
            <h3 style={{ marginBottom: '16px' }}>CryptoEx</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
              Professional cryptocurrency exchange platform
            </p>
          </div>

          <div>
            <h4 style={{ marginBottom: '16px' }}>Products</h4>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li style={{ marginBottom: '8px' }}>
                <a href="#" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>Spot Trading</a>
              </li>
              <li style={{ marginBottom: '8px' }}>
                <a href="#" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>Margin Trading</a>
              </li>
              <li style={{ marginBottom: '8px' }}>
                <a href="#" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>Staking</a>
              </li>
            </ul>
          </div>

          <div>
            <h4 style={{ marginBottom: '16px' }}>Support</h4>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li style={{ marginBottom: '8px' }}>
                <a href="#" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>Help Center</a>
              </li>
              <li style={{ marginBottom: '8px' }}>
                <a href="#" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>API Docs</a>
              </li>
              <li style={{ marginBottom: '8px' }}>
                <a href="#" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>Fees</a>
              </li>
            </ul>
          </div>

          <div>
            <h4 style={{ marginBottom: '16px' }}>Company</h4>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li style={{ marginBottom: '8px' }}>
                <a href="#" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>About Us</a>
              </li>
              <li style={{ marginBottom: '8px' }}>
                <a href="#" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>Careers</a>
              </li>
              <li style={{ marginBottom: '8px' }}>
                <a href="#" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>Terms</a>
              </li>
            </ul>
          </div>
        </div>

        <div style={{
          marginTop: '32px',
          paddingTop: '32px',
          borderTop: '1px solid var(--border)',
          textAlign: 'center',
          color: 'var(--text-secondary)',
          fontSize: '14px'
        }}>
          © 2024 CryptoEx. All rights reserved.
        </div>
      </div>
    </footer>
  );
};

export default Footer;