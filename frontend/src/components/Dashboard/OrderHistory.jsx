import React, { useState, useEffect } from 'react';
import { getOrders } from '../../services/api';

const OrderHistory = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const response = await getOrders({ limit: 10 });
      setOrders(response.data.orders);
    } catch (error) {
      console.error('Error loading orders:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="card">
        <h3>Recent Orders</h3>
        <div className="loading"><div className="spinner"></div></div>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 style={{ marginBottom: '20px' }}>Recent Orders</h3>

      {orders.length === 0 ? (
        <p style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-secondary)' }}>
          No orders yet
        </p>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table className="table">
            <thead>
              <tr>
                <th>Pair</th>
                <th>Type</th>
                <th>Side</th>
                <th>Price</th>
                <th>Amount</th>
                <th>Filled</th>
                <th>Status</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {orders.map(order => (
                <tr key={order.id}>
                  <td><strong>{order.trading_pair}</strong></td>
                  <td style={{ textTransform: 'capitalize' }}>{order.order_type}</td>
                  <td className={order.side === 'buy' ? 'green' : 'red'}>
                    {order.side.toUpperCase()}
                  </td>
                  <td>{order.price ? `$${parseFloat(order.price).toFixed(2)}` : 'Market'}</td>
                  <td>{parseFloat(order.quantity).toFixed(4)}</td>
                  <td>{order.fill_percentage.toFixed(1)}%</td>
                  <td>
                    <span className={`badge ${
                      order.status === 'filled' ? 'badge-success' :
                      order.status === 'cancelled' ? 'badge-danger' :
                      'badge-warning'
                    }`}>
                      {order.status}
                    </span>
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    {new Date(order.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default OrderHistory;