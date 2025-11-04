import React, { useState, useEffect } from 'react';
import Navbar from '../Common/Navbar';
import { getBalances, deposit, withdraw, getTransactions } from '../../services/api';
import toast from 'react-hot-toast';

const Wallet = () => {
  const [balances, setBalances] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDeposit, setShowDeposit] = useState(false);
  const [showWithdraw, setShowWithdraw] = useState(false);
  const [selectedCurrency, setSelectedCurrency] = useState('USDT');
  const [depositAmount, setDepositAmount] = useState('');
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [withdrawAddress, setWithdrawAddress] = useState('');

  useEffect(() => {
    loadWalletData();
  }, []);

  const loadWalletData = async () => {
    try {
      await Promise.all([
        loadBalances(),
        loadTransactions()
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadBalances = async () => {
    try {
      const response = await getBalances();
      setBalances(response.data.balances);
    } catch (error) {
      console.error('Error loading balances:', error);
    }
  };

  const loadTransactions = async () => {
    try {
      const response = await getTransactions({ limit: 20 });
      setTransactions(response.data.transactions);
    } catch (error) {
      console.error('Error loading transactions:', error);
    }
  };

  const handleDeposit = async (e) => {
    e.preventDefault();

    try {
      await deposit({
        currency: selectedCurrency,
        amount: parseFloat(depositAmount)
      });

      toast.success('Deposit successful!');
      setDepositAmount('');
      setShowDeposit(false);
      loadWalletData();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Deposit failed');
    }
  };

  const handleWithdraw = async (e) => {
    e.preventDefault();

    try {
      await withdraw({
        currency: selectedCurrency,
        amount: parseFloat(withdrawAmount),
        address: withdrawAddress
      });

      toast.success('Withdrawal initiated!');
      setWithdrawAmount('');
      setWithdrawAddress('');
      setShowWithdraw(false);
      loadWalletData();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Withdrawal failed');
    }
  };

  const totalValue = balances.reduce((sum, balance) => {
    // Simplified: assuming 1:1 for USDT, would need real prices for others
    return sum + balance.balance;
  }, 0);

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
        <h1 style={{ marginBottom: '32px' }}>Wallet</h1>

        {/* Total Balance */}
        <div className="card" style={{ marginBottom: '24px' }}>
          <h3 style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>
            Estimated Total Balance
          </h3>
          <h1 style={{ fontSize: '48px' }}>${totalValue.toFixed(2)}</h1>
        </div>

        <div className="grid grid-2">
          {/* Balances */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3>Your Balances</h3>
              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  onClick={() => setShowDeposit(true)}
                  className="btn btn-primary"
                >
                  Deposit
                </button>
                <button
                  onClick={() => setShowWithdraw(true)}
                  className="btn btn-danger"
                >
                  Withdraw
                </button>
              </div>
            </div>

            <table className="table">
              <thead>
                <tr>
                  <th>Currency</th>
                  <th>Total</th>
                  <th>Available</th>
                  <th>In Orders</th>
                </tr>
              </thead>
              <tbody>
                {balances.map(balance => (
                  <tr key={balance.id}>
                    <td><strong>{balance.currency}</strong></td>
                    <td>{balance.balance.toFixed(8)}</td>
                    <td>{balance.available_balance.toFixed(8)}</td>
                    <td style={{ color: 'var(--warning)' }}>
                      {balance.locked_balance.toFixed(8)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Transaction History */}
          <div className="card">
            <h3 style={{ marginBottom: '20px' }}>Recent Transactions</h3>
            <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
              {transactions.length === 0 ? (
                <p style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-secondary)' }}>
                  No transactions yet
                </p>
              ) : (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Amount</th>
                      <th>Status</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map(tx => (
                      <tr key={tx.id}>
                        <td>
                          <span className={tx.transaction_type === 'deposit' ? 'green' : 'red'}>
                            {tx.transaction_type.toUpperCase()}
                          </span>
                        </td>
                        <td>
                          {tx.amount} {tx.currency}
                        </td>
                        <td>
                          <span className={`badge ${
                            tx.status === 'completed' ? 'badge-success' :
                            tx.status === 'failed' ? 'badge-danger' :
                            'badge-warning'
                          }`}>
                            {tx.status}
                          </span>
                        </td>
                        <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                          {new Date(tx.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>

        {/* Deposit Modal */}
        {showDeposit && (
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
            <div className="card" style={{ maxWidth: '500px', width: '90%' }}>
              <h2 style={{ marginBottom: '24px' }}>Deposit Funds</h2>
              <form onSubmit={handleDeposit}>
                <div className="form-group">
                  <label className="form-label">Currency</label>
                  <select
                    className="input"
                    value={selectedCurrency}
                    onChange={(e) => setSelectedCurrency(e.target.value)}
                  >
                    {balances.map(b => (
                      <option key={b.currency} value={b.currency}>{b.currency}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Amount</label>
                  <input
                    type="number"
                    step="0.01"
                    className="input"
                    value={depositAmount}
                    onChange={(e) => setDepositAmount(e.target.value)}
                    placeholder="0.00"
                    required
                  />
                </div>

                <div style={{ display: 'flex', gap: '12px' }}>
                  <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                    Deposit
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowDeposit(false)}
                    className="btn"
                    style={{ flex: 1, background: 'var(--dark-light)', color: 'white' }}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Withdraw Modal */}
        {showWithdraw && (
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
            <div className="card" style={{ maxWidth: '500px', width: '90%' }}>
              <h2 style={{ marginBottom: '24px' }}>Withdraw Funds</h2>
              <form onSubmit={handleWithdraw}>
                <div className="form-group">
                  <label className="form-label">Currency</label>
                  <select
                    className="input"
                    value={selectedCurrency}
                    onChange={(e) => setSelectedCurrency(e.target.value)}
                  >
                    {balances.map(b => (
                      <option key={b.currency} value={b.currency}>{b.currency}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Amount</label>
                  <input
                    type="number"
                    step="0.01"
                    className="input"
                    value={withdrawAmount}
                    onChange={(e) => setWithdrawAmount(e.target.value)}
                    placeholder="0.00"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Withdrawal Address</label>
                  <input
                    type="text"
                    className="input"
                    value={withdrawAddress}
                    onChange={(e) => setWithdrawAddress(e.target.value)}
                    placeholder="0x..."
                    required
                  />
                </div>

                <div style={{ display: 'flex', gap: '12px' }}>
                  <button type="submit" className="btn btn-danger" style={{ flex: 1 }}>
                    Withdraw
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowWithdraw(false)}
                    className="btn"
                    style={{ flex: 1, background: 'var(--dark-light)', color: 'white' }}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default Wallet;