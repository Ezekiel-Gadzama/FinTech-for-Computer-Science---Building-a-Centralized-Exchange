import axios from 'axios';

// Use the nginx proxy URL (port 80)
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const register = (data) => api.post('/auth/register', data);
export const login = (data) => api.post('/auth/login', data);
export const getCurrentUser = () => api.get('/auth/me');

// Trading - UPDATED to use query parameters
export const placeOrder = (data) => api.post('/trading/order', data);
export const getOrders = (params) => api.get('/trading/orders', { params });
export const cancelOrder = (orderId) => api.delete(`/trading/order/${orderId}`);
export const getOrderBook = (pair, depth = 20) =>
  api.get('/trading/orderbook', { params: { pair, depth } }); // Updated
export const getRecentTrades = (pair, limit = 50) =>
  api.get('/trading/trades', { params: { pair, limit } }); // Updated

// Wallet
export const getBalances = () => api.get('/wallet/balances');
export const deposit = (data) => api.post('/wallet/deposit', data);
export const withdraw = (data) => api.post('/wallet/withdraw', data);
export const getTransactions = (params) => api.get('/wallet/transactions', { params });

// Market - UPDATED to use query parameters
export const getPrices = () => api.get('/market/prices');
export const getTicker = (pair) => api.get('/market/ticker', { params: { pair } }); // Updated
export const getTradingPairs = () => api.get('/market/pairs');
export const getExchangeStats = () => api.get('/market/stats');

// KYC
export const submitKYC = (data) => api.post('/auth/kyc', data);
export const getKYCStatus = () => api.get('/auth/kyc/status');
export const uploadKYCDocument = (formData) => api.post('/kyc/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
export const getKYCDocuments = () => api.get('/kyc/documents');

// API Keys
export const createAPIKey = (data) => api.post('/api-keys', data);
export const getAPIKeys = () => api.get('/api-keys');
export const getAPIKey = (keyId) => api.get(`/api-keys/${keyId}`);
export const updateAPIKey = (keyId, data) => api.put(`/api-keys/${keyId}`, data);
export const deleteAPIKey = (keyId) => api.delete(`/api-keys/${keyId}`);
export const getAPIKeyUsage = (keyId) => api.get(`/api-keys/${keyId}/usage`);

// Security / 2FA
export const setup2FA = () => api.post('/security/2fa/setup');
export const verify2FA = (data) => api.post('/security/2fa/verify', data);
export const disable2FA = (data) => api.post('/security/2fa/disable', data);
export const get2FAStatus = () => api.get('/security/2fa/status');

// Admin - KYC Management
export const getPendingKYC = () => api.get('/kyc/pending');
export const verifyKYC = (userId, data) => api.post(`/kyc/verify/${userId}`, data);
export const rejectKYC = (userId, data) => api.post(`/kyc/reject/${userId}`, data);
export const getUserDocuments = (userId) => api.get(`/kyc/documents/${userId}`);

// Admin - Create Admin User (development only)
export const createAdmin = (data) => api.post('/auth/create-admin', data);

export default api;