import React, { useState } from 'react';
import { withdraw } from '../../services/api';
import toast from 'react-hot-toast';

const Withdraw = ({ currency, availableBalance, onSuccess, onClose }) => {
  const [formData, setFormData] = useState({
    amount: '',
    address: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const amount = parseFloat(formData.amount);

    if (!amount || amount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    if (amount > availableBalance) {
      toast.error('Insufficient balance');
      return;
    }

    if (!formData.address) {
      toast.error('Please enter withdrawal address');
      return;
    }

    setLoading(true);

    try {
      await withdraw({
        currency,
        amount,
        address: formData.address
      });
      toast.success(`Withdrawal of ${amount} ${currency} initiated`);
      setFormData({ amount: '', address: '' });
      if (onSuccess) onSuccess();
      if (onClose) onClose();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Withdrawal failed');
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

  const handleMaxClick = () => {
    setFormData({
      ...formData,
      amount: availableBalance.toString()
    });
  };

  const withdrawFee = 0.0005; // Example fee
  const amountAfterFee = formData.amount ? parseFloat(formData.amount) - withdrawFee : 0;

  return (
    <div>
      <h3 style={{ marginBottom: '24px' }}>Withdraw {currency}</h3>

      <div style={{
        padding: '16px',
        background: 'rgba(239, 68, 68, 0.1)',
        borderRadius: '8px',
        marginBottom: '24px'
      }}>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          <strong>Warning:</strong> Make sure the withdrawal address is correct.
          Transactions cannot be reversed.
        </p>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
          Available Balance: <strong>{availableBalance.toFixed(8)} {currency}</strong>
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Withdrawal Address</label>
          <input
            type="text"
            name="address"
            className="input"
            value={formData.address}
            onChange={handleChange}
            placeholder="Enter wallet address"
            required
          />
        </div>

        <div className="form-group">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <label className="form-label">Amount ({currency})</label>
            <button
              type="button"
              onClick={handleMaxClick}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--primary)',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Max
            </button>
          </div>
          <input
            type="number"
            name="amount"
            step="0.00000001"
            className="input"
            value={formData.amount}
            onChange={handleChange}
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
            <span style={{ color: 'var(--text-secondary)' }}>Amount:</span>
            <span>{formData.amount || '0.00'} {currency}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Network fee:</span>
            <span>{withdrawFee} {currency}</span>
          </div>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            paddingTop: '8px',
            borderTop: '1px solid var(--border)'
          }}>
            <span style={{ color: 'var(--text-secondary)' }}>You will receive:</span>
            <strong>{amountAfterFee > 0 ? amountAfterFee.toFixed(8) : '0.00'} {currency}</strong>
          </div>
        </div>

        <button
          type="submit"
          className="btn btn-danger"
          style={{ width: '100%' }}
          disabled={loading}
        >
          {loading ? 'Processing...' : `Withdraw ${currency}`}
        </button>
      </form>
    </div>
  );
};

export default Withdraw;