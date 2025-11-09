import React, { useState, useEffect } from 'react';
import Navbar from '../Common/Navbar';
import { getAPIKeys, deleteAPIKey, getAPIKeyUsage } from '../../services/api';
import CreateAPIKey from './CreateAPIKey';
import toast from 'react-hot-toast';

const APIKeys = () => {
  const [apiKeys, setApiKeys] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [usageStats, setUsageStats] = useState({});

  useEffect(() => {
    loadAPIKeys();
  }, []);

  const loadAPIKeys = async () => {
    try {
      const response = await getAPIKeys();
      setApiKeys(response.data.api_keys);
      
      // Load usage stats for each key
      const stats = {};
      for (const key of response.data.api_keys) {
        try {
          const usageResponse = await getAPIKeyUsage(key.key_id);
          stats[key.key_id] = usageResponse.data.usage;
        } catch (error) {
          console.error(`Error loading usage for key ${key.key_id}:`, error);
        }
      }
      setUsageStats(stats);
    } catch (error) {
      console.error('Error loading API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (keyId) => {
    if (!window.confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
      return;
    }

    try {
      await deleteAPIKey(keyId);
      toast.success('API key deleted successfully');
      loadAPIKeys();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to delete API key');
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
          <h1>API Keys</h1>
          <button
            onClick={() => setShowCreate(true)}
            className="btn btn-primary"
          >
            Create API Key
          </button>
        </div>

        <div className="card" style={{ marginBottom: '24px' }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
            API keys allow third-party applications to access your account. Keep them secure and never share them publicly.
          </p>
        </div>

        {apiKeys.length === 0 ? (
          <div className="card">
            <div style={{ textAlign: 'center', padding: '60px 20px' }}>
              <p style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>
                No API keys created yet
              </p>
              <button
                onClick={() => setShowCreate(true)}
                className="btn btn-primary"
              >
                Create Your First API Key
              </button>
            </div>
          </div>
        ) : (
          <div className="card">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Permissions</th>
                  <th>Status</th>
                  <th>Usage (24h)</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {apiKeys.map(key => (
                  <tr key={key.id}>
                    <td><strong>{key.name}</strong></td>
                    <td>
                      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        {key.can_read && <span className="badge badge-info">Read</span>}
                        {key.can_trade && <span className="badge badge-warning">Trade</span>}
                        {key.can_withdraw && <span className="badge badge-danger">Withdraw</span>}
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${key.is_active ? 'badge-success' : 'badge-secondary'}`}>
                        {key.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      {usageStats[key.key_id] ? usageStats[key.key_id].last_day : 0} requests
                    </td>
                    <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      {new Date(key.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <button
                        onClick={() => handleDelete(key.key_id)}
                        className="btn btn-danger"
                        style={{ padding: '4px 12px', fontSize: '12px' }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Create API Key Modal */}
        {showCreate && (
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
            <CreateAPIKey
              onClose={() => {
                setShowCreate(false);
                loadAPIKeys();
              }}
            />
          </div>
        )}
      </div>
    </>
  );
};

export default APIKeys;

