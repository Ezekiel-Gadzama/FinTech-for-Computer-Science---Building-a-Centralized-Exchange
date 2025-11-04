import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../Common/Navbar';
import OrderBook from './OrderBook';
import OrderForm from './OrderForm';
import { getPrices, getTicker, getRecentTrades, getOrders } from '../../services/api';
import wsService from '../../services/websocket';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const TradingView = () => {
  const { pair } = useParams();
  const navigate = useNavigate();
  const [selectedPair, setSelectedPair] = useState(pair || 'BTC/USDT');
  const [ticker, setTicker] = useState(null);
  const [recentTrades, setRecentTrades] = useState([]);
  const [userOrders, setUserOrders] = useState([]);
  const [chartData, setChartData] = useState([]);

  const tradingPairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT'];

  useEffect(() => {
    loadTradingData();

    // Subscribe to WebSocket updates
    wsService.subscribe(selectedPair);
    wsService.on('trade', handleNewTrade);
    wsService.on('orderbook_update', handleOrderbookUpdate);

    return () => {
      wsService.unsubscribe(selectedPair);
      wsService.off('trade', handleNewTrade);
      wsService.off('orderbook_update', handleOrderbookUpdate);
    };
  }, [selectedPair]);

  const loadTradingData = async () => {
    try {
      await Promise.all([
        loadTicker(),
        loadRecentTrades(),
        loadUserOrders()
      ]);
    } catch (error) {
      console.error('Error loading trading data:', error);
    }
  };

  const loadTicker = async () => {
    try {
      const response = await getTicker(selectedPair);
      setTicker(response.data);
    } catch (error) {
      console.error('Error loading ticker:', error);
    }
  };

  const loadRecentTrades = async () => {
    try {
      const response = await getRecentTrades(selectedPair, 50);
      setRecentTrades(response.data.trades);

      // Generate chart data from recent trades
      if (response.data.trades.length > 0) {
        const data = response.data.trades.slice(0, 20).reverse().map((trade, idx) => ({
          time: idx,
          price: parseFloat(trade.price)
        }));
        setChartData(data);
      }
    } catch (error) {
      console.error('Error loading trades:', error);
    }
  };

  const loadUserOrders = async () => {
    try {
      const response = await getOrders({ pair: selectedPair, limit: 20 });
      setUserOrders(response.data.orders);
    } catch (error) {
      console.error('Error loading orders:', error);
    }
  };

  const handleNewTrade = (trade) => {
    if (trade.trading_pair === selectedPair) {
      setRecentTrades(prev => [trade, ...prev.slice(0, 49)]);
      setChartData(prev => [...prev.slice(-19), {
        time: prev.length,
        price: parseFloat(trade.price)
      }]);
    }
  };

  const handleOrderbookUpdate = () => {
    // Orderbook component will handle its own updates
  };

  const handlePairChange = (newPair) => {
    setSelectedPair(newPair);
    navigate(`/trade/${newPair.replace('/', '-')}`);
  };

  const handleOrderPlaced = () => {
    loadUserOrders();
  };

  return (
    <>
      <Navbar />
      <div className="container">
        {/* Pair Selector */}
        <div style={{ marginBottom: '24px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {tradingPairs.map(p => (
            <button
              key={p}
              onClick={() => handlePairChange(p)}
              className={`btn ${selectedPair === p ? 'btn-primary' : 'btn-secondary'}`}
              style={{
                background: selectedPair === p ? 'var(--primary)' : 'var(--dark-light)',
                color: 'white'
              }}
            >
              {p}
            </button>
          ))}
        </div>

        {/* Ticker */}
        {ticker && (
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="grid grid-4">
              <div>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>Last Price</p>
                <h2>{ticker.last ? `$${ticker.last.toLocaleString()}` : '-'}</h2>
              </div>
              <div>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>24h Change</p>
                <h2 className={ticker.change >= 0 ? 'green' : 'red'}>
                  {ticker.change ? `${ticker.change.toFixed(2)}%` : '-'}
                </h2>
              </div>
              <div>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>24h High</p>
                <h2>{ticker.high ? `$${ticker.high.toLocaleString()}` : '-'}</h2>
              </div>
              <div>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>24h Volume</p>
                <h2>{ticker.volume ? ticker.volume.toFixed(2) : '-'}</h2>
              </div>
            </div>
          </div>
        )}

        {/* Main Trading Area */}
        <div className="grid grid-3" style={{ marginBottom: '24px' }}>
          {/* Chart */}
          <div className="card" style={{ gridColumn: 'span 2' }}>
            <h3 style={{ marginBottom: '20px' }}>Price Chart</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="time" stroke="var(--text-secondary)" />
                <YAxis stroke="var(--text-secondary)" domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{
                    background: 'var(--dark-light)',
                    border: '1px solid var(--border)',
                    borderRadius: '8px'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="price"
                  stroke="var(--primary)"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Order Form */}
          <div>
            <OrderForm
              pair={selectedPair}
              onOrderPlaced={handleOrderPlaced}
            />
          </div>
        </div>

        <div className="grid grid-3">
          {/* Order Book */}
          <div>
            <OrderBook pair={selectedPair} />
          </div>

          {/* Recent Trades */}
          <div className="card">
            <h3 style={{ marginBottom: '20px' }}>Recent Trades</h3>
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Price</th>
                    <th>Amount</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {recentTrades.map((trade, idx) => (
                    <tr key={idx}>
                      <td className="green">${parseFloat(trade.price).toFixed(2)}</td>
                      <td>{parseFloat(trade.quantity).toFixed(4)}</td>
                      <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {new Date(trade.executed_at).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* User Orders */}
          <div className="card">
            <h3 style={{ marginBottom: '20px' }}>Your Orders</h3>
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {userOrders.length === 0 ? (
                <p style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-secondary)' }}>
                  No open orders
                </p>
              ) : (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Side</th>
                      <th>Price</th>
                      <th>Amount</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {userOrders.map(order => (
                      <tr key={order.id}>
                        <td className={order.side === 'buy' ? 'green' : 'red'}>
                          {order.side.toUpperCase()}
                        </td>
                        <td>${order.price ? parseFloat(order.price).toFixed(2) : 'Market'}</td>
                        <td>{parseFloat(order.quantity).toFixed(4)}</td>
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
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default TradingView;