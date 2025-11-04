import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../Common/Navbar';
import { getBalances, getPrices, getOrders } from '../../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Dashboard = () => {
  const navigate = useNavigate();
  const [balances, setBalances] = useState([]);
  const [prices, setPrices] = useState({});
  const [recentOrders, setRecentOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalValue, setTotalValue] = useState(0);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(() => {
      loadPrices();
    }, 30000); // Update prices every 30s

    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      await Promise.all([
        loadBalances(),
        loadPrices(),
        loadRecentOrders()
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadBalances = async () => {
    try {
      const response = await getBalances();
      setBalances(response.data.balances.filter(b => b.balance > 0));
    } catch (error) {
      console.error('Error loading balances:', error);
    }
  };

  const loadPrices = async () => {
    try {
      const response = await getPrices();
      setPrices(response.data.prices);
    } catch (error) {
      console.error('Error loading prices:', error);
    }
  };

  const loadRecentOrders = async () => {
    try {
      const response = await getOrders({ limit: 5 });
      setRecentOrders(response.data.orders);
    } catch (error) {
      console.error('Error loading orders:', error);
    }
  };

  useEffect(() => {
    if (balances.length > 0 && Object.keys(prices).length > 0) {
      calculateTotalValue();
    }
  }, [balances, prices]);

  const calculateTotalValue = () => {
    let total = 0;
    balances.forEach(balance => {
      if (balance.currency === 'USDT') {
        total += balance.balance;
      } else {
        const pair = `${balance.currency}/USDT`;
        if (prices[pair]) {
          total += balance.balance * prices[pair].price;
        }
      }
    });
    setTotalValue(total);
  };

  const getPriceData = () => {
    const pairs = Object.keys(prices);
    return pairs.map(pair => ({
      name: pair.split('/')[0],
      price: prices[pair].price,
      change: prices[pair].change_24h
    }));
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
        <h1 style={{ marginBottom: '32px' }}>Dashboard</h1>

        {/* Portfolio Value */}
        <div className="card" style={{ marginBottom: '24px' }}>
          <h3 style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>Total Portfolio Value</h3>
          <h1 style={{ fontSize: '48px', marginBottom: '8px' }}>
            ${totalValue.toFixed(2)}
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>USDT equivalent</p>
        </div>

        <div className="grid grid-2" style={{ marginBottom: '24px' }}>
          {/* Balances */}
          <div className="card">
            <h3 style={{ marginBottom: '20px' }}>Your Balances</h3>
            <table className="table">
              <thead>
                <tr>
                  <th>Currency</th>
                  <th>Balance</th>
                  <th>Value (USDT)</th>
                </tr>
              </thead>
              <tbody>
                {balances.map(balance => {
                  const pair = `${balance.currency}/USDT`;
                  const value = balance.currency === 'USDT'
                    ? balance.balance
                    : (prices[pair] ? balance.balance * prices[pair].price : 0);

                  return (
                    <tr key={balance.id}>
                      <td><strong>{balance.currency}</strong></td>
                      <td>{balance.balance.toFixed(8)}</td>
                      <td>${value.toFixed(2)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <button
              onClick={() => navigate('/wallet')}
              className="btn btn-primary"
              style={{ marginTop: '16px', width: '100%' }}
            >
              Manage Wallet
            </button>
          </div>

          {/* Recent Orders */}
          <div className="card">
            <h3 style={{ marginBottom: '20px' }}>Recent Orders</h3>
            {recentOrders.length === 0 ? (
              <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '40px 0' }}>
                No orders yet. Start trading!
              </p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Pair</th>
                    <th>Type</th>
                    <th>Amount</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recentOrders.map(order => (
                    <tr key={order.id}>
                      <td>{order.trading_pair}</td>
                      <td>
                        <span className={order.side === 'buy' ? 'green' : 'red'}>
                          {order.side.toUpperCase()}
                        </span>
                      </td>
                      <td>{order.quantity}</td>
                      <td>
                        <span className={`badge ${
                          order.status === 'filled' ? 'badge-success' :
                          order.status === 'cancelled' ? 'badge-danger' :
                          'badge-warning'
                        }`}>
                          {order.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <button
              onClick={() => navigate('/trade')}
              className="btn btn-primary"
              style={{ marginTop: '16px', width: '100%' }}
            >
              Start Trading
            </button>
          </div>
        </div>

        {/* Market Overview */}
        <div className="card">
          <h3 style={{ marginBottom: '20px' }}>Market Overview</h3>
          <div className="grid grid-3">
            {getPriceData().map(item => (
              <div
                key={item.name}
                className="card"
                style={{ cursor: 'pointer' }}
                onClick={() => navigate(`/trade/${item.name}/USDT`)}
              >
                <h4 style={{ marginBottom: '12px' }}>{item.name}/USDT</h4>
                <p style={{ fontSize: '24px', fontWeight: '600', marginBottom: '8px' }}>
                  ${item.price.toLocaleString()}
                </p>
                <p className={item.change >= 0 ? 'green' : 'red'}>
                  {item.change >= 0 ? '▲' : '▼'} {Math.abs(item.change).toFixed(2)}%
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
};

export default Dashboard;