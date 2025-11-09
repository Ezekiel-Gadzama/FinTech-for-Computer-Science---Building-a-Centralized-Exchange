import React, { useState, useEffect } from 'react';
import Navbar from '../Common/Navbar';
import { get2FAStatus, disable2FA } from '../../services/api';
import TwoFactorSetup from './TwoFactorSetup';
import toast from 'react-hot-toast';

const SecuritySettings = () => {
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [show2FASetup, setShow2FASetup] = useState(false);
  const [showDisable2FA, setShowDisable2FA] = useState(false);
  const [password, setPassword] = useState('');
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    load2FAStatus();
  }, []);

  const load2FAStatus = async () => {
    try {
      const response = await get2FAStatus();
      setTwoFactorEnabled(response.data.two_factor_enabled);
    } catch (error) {
      console.error('Error loading 2FA status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDisable2FA = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await disable2FA({ password, token });
      setTwoFactorEnabled(false);
      setShowDisable2FA(false);
      setPassword('');
      setToken('');
      toast.success('2FA disabled successfully');
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to disable 2FA');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="container">
        <h1 style={{ marginBottom: '32px' }}>Security Settings</h1>

        <div className="card" style={{ marginBottom: '24px' }}>
          <h3 style={{ marginBottom: '20px' }}>Two-Factor Authentication</h3>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <p style={{ marginBottom: '8px', fontWeight: '600' }}>
                {twoFactorEnabled ? '2FA is Enabled' : '2FA is Disabled'}
              </p>
              <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                {twoFactorEnabled
                  ? 'Your account is protected with two-factor authentication'
                  : 'Add an extra layer of security to your account'}
              </p>
            </div>
            <div>
              <span className={`badge ${twoFactorEnabled ? 'badge-success' : 'badge-warning'}`}>
                {twoFactorEnabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          </div>

          {!twoFactorEnabled ? (
            <button
              onClick={() => setShow2FASetup(true)}
              className="btn btn-primary"
            >
              Enable 2FA
            </button>
          ) : (
            <button
              onClick={() => setShowDisable2FA(true)}
              className="btn btn-danger"
            >
              Disable 2FA
            </button>
          )}
        </div>

        {/* 2FA Setup Modal */}
        {show2FASetup && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000,
            padding: '20px'
          }}>
            <div className="card" style={{ maxWidth: '500px', width: '100%', maxHeight: '90vh', overflowY: 'auto' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <h2>Setup 2FA</h2>
                <button
                  onClick={() => setShow2FASetup(false)}
                  style={{ background: 'none', border: 'none', fontSize: '24px', cursor: 'pointer', color: 'var(--text-secondary)' }}
                >
                  ×
                </button>
              </div>
              <TwoFactorSetup
                onComplete={() => {
                  setShow2FASetup(false);
                  load2FAStatus();
                }}
              />
            </div>
          </div>
        )}

        {/* Disable 2FA Modal */}
        {showDisable2FA && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000
          }}>
            <div className="card" style={{ maxWidth: '500px', width: '90%' }}>
              <h2 style={{ marginBottom: '24px' }}>Disable 2FA</h2>
              <p style={{ marginBottom: '24px', color: 'var(--text-secondary)' }}>
                To disable 2FA, please enter your password and a 2FA token.
              </p>
              <form onSubmit={handleDisable2FA}>
                <div className="form-group">
                  <label className="form-label">Password</label>
                  <input
                    type="password"
                    className="input"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">2FA Token</label>
                  <input
                    type="text"
                    className="input"
                    value={token}
                    onChange={(e) => setToken(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="000000"
                    maxLength="6"
                    required
                    style={{ textAlign: 'center', fontSize: '24px', letterSpacing: '8px' }}
                  />
                </div>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <button
                    type="button"
                    onClick={() => {
                      setShowDisable2FA(false);
                      setPassword('');
                      setToken('');
                    }}
                    className="btn"
                    style={{ flex: 1, background: 'var(--dark-light)' }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn btn-danger"
                    disabled={loading}
                    style={{ flex: 1 }}
                  >
                    {loading ? 'Disabling...' : 'Disable 2FA'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default SecuritySettings;

