import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { login } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import toast from 'react-hot-toast';

const Login = () => {
  const navigate = useNavigate();
  const { loginUser } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    two_factor_token: ''
  });
  const [requires2FA, setRequires2FA] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await login(formData);
      const { user, access_token } = response.data;
      loginUser(user, access_token);
      toast.success('Login successful!');
      navigate('/dashboard');
    } catch (error) {
      if (error.response?.data?.requires_2fa) {
        setRequires2FA(true);
        toast.error('2FA token required');
      } else {
        toast.error(error.response?.data?.error || 'Login failed');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="auth-container">
      <div className="card auth-card">
        <h1 className="logo" style={{ textAlign: 'center', marginBottom: '32px' }}>
          CryptoEx
        </h1>
        <h2 style={{ marginBottom: '24px', textAlign: 'center' }}>Login</h2>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input
              type="text"
              name="username"
              className="input"
              value={formData.username}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              name="password"
              className="input"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>

          {requires2FA && (
            <div className="form-group">
              <label className="form-label">2FA Token</label>
              <input
                type="text"
                name="two_factor_token"
                className="input"
                value={formData.two_factor_token}
                onChange={handleChange}
                placeholder="000000"
                maxLength="6"
                required
                style={{ textAlign: 'center', fontSize: '20px', letterSpacing: '8px' }}
              />
              <small style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                Enter the 6-digit code from your authenticator app
              </small>
            </div>
          )}

          <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <p style={{ marginTop: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          Don't have an account? <Link to="/register" style={{ color: 'var(--primary)' }}>Register</Link>
        </p>
      </div>
    </div>
  );
};

export default Login;