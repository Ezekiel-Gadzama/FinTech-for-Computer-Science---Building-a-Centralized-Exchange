import React, { useState } from 'react';
import Navbar from '../Common/Navbar';
import toast from 'react-hot-toast';
import { placeOrder } from '../../services/api';

const StressTest = () => {
  const [numOrders, setNumOrders] = useState(100);
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState(null);

  const runStressTest = async () => {
    setRunning(true);
    setResults(null);

    const startTime = Date.now();
    let successful = 0;
    let failed = 0;

    try {
      const promises = [];

      for (let i = 0; i < numOrders; i++) {
        const order = {
          trading_pair: 'BTC/USDT',
          side: i % 2 === 0 ? 'buy' : 'sell',
          order_type: 'limit',
          price: i % 2 === 0 ? 44000 : 46000,
          quantity: 0.001
        };

        promises.push(
          placeOrder(order)
            .then(() => successful++)
            .catch(() => failed++)
        );
      }

      await Promise.all(promises);

      const endTime = Date.now();
      const duration = (endTime - startTime) / 1000;

      setResults({
        total: numOrders,
        successful,
        failed,
        duration,
        ordersPerSecond: (numOrders / duration).toFixed(2)
      });

      toast.success('Stress test completed!');
    } catch (error) {
      toast.error('Stress test failed');
    } finally {
      setRunning(false);
    }
  };

  return (
    <>
      <Navbar />
      <div className="container" style={{ maxWidth: '800px', paddingTop: '64px' }}>
        <div className="card">
          <h2 style={{ marginBottom: '24px' }}>Stress Test</h2>

          <div className="form-group">
            <label className="form-label">Number of Orders</label>
            <input
              type="number"
              className="input"
              value={numOrders}
              onChange={(e) => setNumOrders(parseInt(e.target.value))}
              min="10"
              max="1000"
              disabled={running}
            />
          </div>

          <button
            onClick={runStressTest}
            className="btn btn-primary"
            style={{ width: '100%' }}
            disabled={running}
          >
            {running ? 'Running Test...' : 'Run Stress Test'}
          </button>

          {results && (
            <div style={{ marginTop: '32px' }}>
              <h3 style={{ marginBottom: '16px' }}>Results</h3>
              <div className="grid grid-2">
                <div className="card">
                  <p style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>Total Orders</p>
                  <h2>{results.total}</h2>
                </div>
                <div className="card">
                  <p style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>Successful</p>
                  <h2 className="green">{results.successful}</h2>
                </div>
                <div className="card">
                  <p style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>Failed</p>
                  <h2 className="red">{results.failed}</h2>
                </div>
                <div className="card">
                  <p style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>Duration</p>
                  <h2>{results.duration}s</h2>
                </div>
                <div className="card" style={{ gridColumn: 'span 2' }}>
                  <p style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>Orders per Second</p>
                  <h2>{results.ordersPerSecond}</h2>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default StressTest;