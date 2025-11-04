import React, { useState, useEffect } from 'react';
import { placeOrder } from '../../services/api';
import { getBalances } from '../../services/api';
import toast from 'react-hot-toast';

const OrderForm = ({ pair, onOrderPlaced }) => {
  const [side, setSide] = useState('buy');
  const [orderType, setOrderType] = useState('limit');
  const [price, setPrice] = useState('');
  const [quantity, setQuantity] = useState('');
  const [loading, setLoading] = useState(false);
  const [balances, setBalances] = useState({});

  const [baseCurrency, quoteCurrency] = pair.split('/');

  useEffect(() => {
    loadBalances();
  }, []);

  const loadBalances = async () => {
    try {
      const response = await getBalances();
      const balanceMap = {};
      response.data.balances.forEach(b => {
        balanceMap[b.currency] = b.available_balance;
      });
      setBalances(balanceMap);
    } catch (error) {
      console.error('Error loading balances:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (orderType === 'limit' && (!price || parseFloat(price) <= 0)) {
      toast.error('Please enter a valid price');
      return;
    }

    if (!quantity || parseFloat(quantity) <= 0) {
      toast.error('Please enter a valid quantity');
      return;
    }

    setLoading(true);

    try {
      const orderData = {
        trading_pair: pair,
        side,
        order_type: orderType,
        quantity: parseFloat(quantity)
      };

      if (orderType === 'limit') {
        orderData.price = parseFloat(price);
      }

      await placeOrder(orderData);

      toast.success('Order placed successfully!');
      setPrice('');
      setQuantity('');
      loadBalances();

      if (onOrderPlaced) {
        onOrderPlaced();
      }
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to place order');
    } finally {
      setLoading(false);
    }
  };

  const availableBalance = side === 'buy'
    ? (balances[quoteCurrency] || 0)
    : (balances[baseCurrency] || 0);

  const estimatedTotal = price && quantity ? parseFloat(price) * parseFloat(quantity) : 0;

  return (
    <div className="card">
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
        <button
          onClick={() => setSide('buy')}
          className={`btn ${side === 'buy' ? 'btn-success' : ''}`}
          style={{
            flex: 1,
            background: side === 'buy' ? 'var(--secondary)' : 'var(--dark-light)',
            color: 'white'
          }}
        >
          Buy
        </button>
        <button
          onClick={() => setSide('sell')}
          className={`btn ${side === 'sell' ? 'btn-danger' : ''}`}
          style={{
            flex: 1,
            background: side === 'sell' ? 'var(--danger)' : 'var(--dark-light)',
            color: 'white'
          }}
        >
          Sell
        </button>
      </div>

      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
        <button
          onClick={() => setOrderType('limit')}
          className="btn"
          style={{
            flex: 1,
            background: orderType === 'limit' ? 'var(--primary)' : 'var(--dark-light)',
            color: 'white'
          }}
        >
          Limit
        </button>
        <button
          onClick={() => setOrderType('market')}
          className="btn"
          style={{
            flex: 1,
            background: orderType === 'market' ? 'var(--primary)' : 'var(--dark-light)',
            color: 'white'
          }}
        >
          Market
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '20px' }}>
          <p style={{
            fontSize: '14px',
            color: 'var(--text-secondary)',
            marginBottom: '8px'
          }}>
            Available: {availableBalance.toFixed(4)} {side === 'buy' ? quoteCurrency : baseCurrency}
          </p>
        </div>

        {orderType === 'limit' && (
          <div className="form-group">
            <label className="form-label">Price ({quoteCurrency})</label>
            <input
              type="number"
              step="0.01"
              className="input"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="0.00"
              required
            />
          </div>
        )}

        <div className="form-group">
          <label className="form-label">Amount ({baseCurrency})</label>
          <input
            type="number"
            step="0.0001"
            className="input"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="0.0000"
            required
          />
        </div>

        {orderType === 'limit' && estimatedTotal > 0 && (
          <div style={{
            padding: '12px',
            background: 'var(--dark-light)',
            borderRadius: '8px',
            marginBottom: '20px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Total:</span>
              <span>{estimatedTotal.toFixed(2)} {quoteCurrency}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Fee (0.1%):</span>
              <span>{(estimatedTotal * 0.001).toFixed(2)} {quoteCurrency}</span>
            </div>
          </div>
        )}

        <button
          type="submit"
          className={`btn ${side === 'buy' ? 'btn-success' : 'btn-danger'}`}
          style={{
            width: '100%',
            background: side === 'buy' ? 'var(--secondary)' : 'var(--danger)'
          }}
          disabled={loading}
        >
          {loading ? 'Placing Order...' : `${side === 'buy' ? 'Buy' : 'Sell'} ${baseCurrency}`}
        </button>
      </form>
    </div>
  );
};

export default OrderForm;