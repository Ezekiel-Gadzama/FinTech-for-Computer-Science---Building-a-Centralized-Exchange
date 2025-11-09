import React, { useState } from 'react';
import { createAPIKey } from '../../services/api';
import toast from 'react-hot-toast';

const CreateAPIKey = ({ onClose }) => {
  const [formData, setFormData] = useState({
    name: '',
    can_read: true,
    can_trade: false,
    can_withdraw: false,
    ip_whitelist: ''
  });
  const [createdKey, setCreatedKey] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await createAPIKey(formData);
      setCreatedKey(response.data.api_key);
      toast.success('API key created successfully!');
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to create API key');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  if (createdKey) {
    return (
      <div className="card" style={{ maxWidth: '600px', width: '90%' }}>
        <h2 style={{ marginBottom: '24px' }}>API Key Created</h2>
        <div style={{ 
          padding: '16px', 
          background: 'var(--warning)', 
          borderRadius: '8px',
          marginBottom: '24px',
          color: 'var(--dark)'
        }}>
          <strong>⚠️ Important:</strong> Save these credentials now. They will not be shown again!
        </div>

        <div className="form-group">
          <label className="form-label">API Key</label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              className="input"
              value={createdKey.api_key}
              readOnly
              style={{ fontFamily: 'monospace', fontSize: '12px' }}
            />
            <button
              type="button"
              onClick={() => copyToClipboard(createdKey.api_key)}
              className="btn"
              style={{ minWidth: '80px' }}
            >
              Copy
            </button>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">API Secret</label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              className="input"
              value={createdKey.api_secret}
              readOnly
              style={{ fontFamily: 'monospace', fontSize: '12px' }}
            />
            <button
              type="button"
              onClick={() => copyToClipboard(createdKey.api_secret)}
              className="btn"
              style={{ minWidth: '80px' }}
            >
              Copy
            </button>
          </div>
        </div>

        <button
          onClick={onClose}
          className="btn btn-primary"
          style={{ width: '100%' }}
        >
          I've Saved My Credentials
        </button>
      </div>
    );
  }

  return (
    <div className="card" style={{ maxWidth: '500px', width: '90%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2>Create API Key</h2>
        <button
          onClick={onClose}
          style={{ background: 'none', border: 'none', fontSize: '24px', cursor: 'pointer', color: 'var(--text-secondary)' }}
        >
          ×
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Name</label>
          <input
            type="text"
            name="name"
            className="input"
            value={formData.name}
            onChange={handleChange}
            placeholder="My Trading Bot"
            required
          />
        </div>

        <div className="form-group">
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              name="can_read"
              checked={formData.can_read}
              onChange={handleChange}
            />
            <span>Read (View balances, orders, trades)</span>
          </label>
        </div>

        <div className="form-group">
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              name="can_trade"
              checked={formData.can_trade}
              onChange={handleChange}
            />
            <span>Trade (Place and cancel orders)</span>
          </label>
        </div>

        <div className="form-group">
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              name="can_withdraw"
              checked={formData.can_withdraw}
              onChange={handleChange}
            />
            <span>Withdraw (Withdraw funds - use with caution)</span>
          </label>
        </div>

        <div className="form-group">
          <label className="form-label">IP Whitelist (Optional)</label>
          <input
            type="text"
            name="ip_whitelist"
            className="input"
            value={formData.ip_whitelist}
            onChange={handleChange}
            placeholder="192.168.1.1, 10.0.0.1"
          />
          <small style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
            Comma-separated list of allowed IP addresses. Leave empty to allow all IPs.
          </small>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            type="button"
            onClick={onClose}
            className="btn"
            style={{ flex: 1, background: 'var(--dark-light)' }}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ flex: 1 }}
          >
            {loading ? 'Creating...' : 'Create API Key'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateAPIKey;

