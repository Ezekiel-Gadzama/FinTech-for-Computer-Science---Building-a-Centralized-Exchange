import React, { useState, useEffect } from 'react';
import { getOrderBook } from '../../services/api';
import wsService from '../../services/websocket';

const OrderBook = ({ pair }) => {
  const [orderbook, setOrderbook] = useState({ bids: [], asks: [] });

  useEffect(() => {
    loadOrderBook();
    
    wsService.on('orderbook_update', handleOrderbookUpdate);
    
    return () => {
      wsService.off('orderbook_update', handleOrderbookUpdate);
    };
  }, [pair]);

  const loadOrderBook = async () => {
    try {
      const response = await getOrderBook(pair, 15);
      setOrderbook(response.data.orderbook);
    } catch (error) {
      console.error('Error loading orderbook:', error);
    }
  };

  const handleOrderbookUpdate = (data) => {
    if (data.pair === pair) {
      setOrderbook(data.data);
    }
  };

  return (
    <div className="card">
      <h3 style={{ marginBottom: '20px' }}>Order Book</h3>
      
      {/* Asks (Sell Orders) */}
      <div style={{ marginBottom: '20px' }}>
        <table className="table">
          <thead>
            <tr>
              <th>Price (USDT)</th>
              <th>Amount</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {orderbook.asks.slice().reverse().map((order, idx) => (
              <tr key={idx} style={{ background: 'rgba(239, 68, 68, 0.05)' }}>
                <td className="red">{order.price.toFixed(2)}</td>
                <td>{order.quantity.toFixed(4)}</td>
                <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {order.total.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Spread */}
      <div style={{ 
        textAlign: 'center', 
        padding: '12px', 
        background: 'var(--dark-light)', 
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
          Spread: {orderbook.asks[0] && orderbook.bids[0] ? 
            (orderbook.asks[0].price - orderbook.bids[0].price).toFixed(2) : 
            '-'}
        </span>
      </div>

      {/* Bids (Buy Orders) */}
      <div>
        <table className="table">
          <thead>
            <tr>
              <th>Price (USDT)</th>
              <th>Amount</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {orderbook.bids.map((order, idx) => (
              <tr key={idx} style={{ background: 'rgba(16, 185, 129, 0.05)' }}>
                <td className="green">{order.price.toFixed(2)}</td>
                <td>{order.quantity.toFixed(4)}</td>
                <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {order.total.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default OrderBook;