import React, { useState } from 'react';
import { deposit } from '../../services/api';
import toast from 'react-hot-toast';

const Deposit = ({ currency, onSuccess, onClose }) => {
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!amount || parseFloat(amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    setLoading(true);

    try {
      await deposit({ currency, amount: parseFloat(amount) });
      toast.success(`Successfully deposited ${amount} ${currency}`);
      setAmount('');
      if (onSuccess) onSuccess();
      if (onClose) onClose();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Deposit failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h3 style={{ marginBottom: '24px' }}>Deposit {currency}</h3>

      <div style={{
        padding: '16px',
        background: 'rgba(59, 130, 246, 0.1)',
        borderRadius: '8px',
        marginBottom: '24px'
      }}>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          <strong>Note:</strong> This is a test environment. Deposits are simulated.
          In production, you would deposit to a blockchain address.
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Amount ({currency})</label>
          <input
            type="number"
            step="0.00000001"
            className="input"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder={`Enter ${currency} amount`}
            required
          />
        </div>

        <div style={{
          padding: '12px',
          background: 'var(--dark-light)',
          borderRadius: '8px',
          marginBottom: '20px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ color: 'var(--text-secondary)' }}>You will receive:</span>
            <strong>{amount || '0.00'} {currency}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Network fee:</span>
            <span>0.00 {currency}</span>
          </div>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          style={{ width: '100%' }}
          disabled={loading}
        >
          {loading ? 'Processing...' : `Deposit ${currency}`}
        </button>
      </form>
    </div>
  );
};

export default Deposit;