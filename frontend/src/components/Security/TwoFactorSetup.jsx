import React, { useState } from 'react';
import { setup2FA, verify2FA } from '../../services/api';
import toast from 'react-hot-toast';

const TwoFactorSetup = ({ onComplete }) => {
  const [step, setStep] = useState(1); // 1: setup, 2: verify
  const [secret, setSecret] = useState('');
  const [qrCode, setQrCode] = useState('');
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSetup = async () => {
    setLoading(true);
    try {
      const response = await setup2FA();
      setSecret(response.data.secret);
      setQrCode(response.data.qr_code);
      setStep(2);
      toast.success('2FA setup initiated. Please verify with your authenticator app.');
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to setup 2FA');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await verify2FA({ token });
      toast.success('2FA enabled successfully!');
      if (onComplete) onComplete();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Invalid token');
    } finally {
      setLoading(false);
    }
  };

  if (step === 1) {
    return (
      <div className="card">
        <h3 style={{ marginBottom: '20px' }}>Setup Two-Factor Authentication</h3>
        <p style={{ marginBottom: '24px', color: 'var(--text-secondary)' }}>
          Two-factor authentication adds an extra layer of security to your account.
          You'll need an authenticator app like Google Authenticator or Authy.
        </p>
        <button
          onClick={handleSetup}
          className="btn btn-primary"
          disabled={loading}
          style={{ width: '100%' }}
        >
          {loading ? 'Setting up...' : 'Start Setup'}
        </button>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 style={{ marginBottom: '20px' }}>Verify 2FA Setup</h3>
      
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <img
          src={qrCode}
          alt="QR Code"
          style={{ maxWidth: '250px', border: '1px solid var(--border)', borderRadius: '8px' }}
        />
      </div>

      <div style={{ marginBottom: '24px', padding: '16px', background: 'var(--dark-light)', borderRadius: '8px' }}>
        <p style={{ marginBottom: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
          Manual Entry Key:
        </p>
        <code style={{ fontSize: '14px', wordBreak: 'break-all' }}>{secret}</code>
      </div>

      <p style={{ marginBottom: '24px', color: 'var(--text-secondary)', fontSize: '14px' }}>
        1. Scan the QR code with your authenticator app<br />
        2. Enter the 6-digit code from your app below
      </p>

      <form onSubmit={handleVerify}>
        <div className="form-group">
          <label className="form-label">Verification Code</label>
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
            onClick={() => setStep(1)}
            className="btn"
            style={{ flex: 1, background: 'var(--dark-light)' }}
          >
            Back
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || token.length !== 6}
            style={{ flex: 1 }}
          >
            {loading ? 'Verifying...' : 'Verify & Enable'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default TwoFactorSetup;

