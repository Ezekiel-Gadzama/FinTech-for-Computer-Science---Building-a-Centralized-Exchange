import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import Dashboard from './components/Dashboard/Dashboard';
import TradingView from './components/Trading/TradingView';
import Wallet from './components/Wallet/Wallet';
import SecuritySettings from './components/Security/SecuritySettings';
import APIKeys from './components/APIKeys/APIKeys';
import KYC from './components/KYC/KYC';
import AdminPanel from './components/Admin/AdminPanel';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import './styles/globals.css';

const PrivateRoute = ({ children }) => {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Toaster position="top-right" />
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/dashboard"
              element={
                <PrivateRoute>
                  <Dashboard />
                </PrivateRoute>
              }
            />
            <Route
              path="/trade/:pair?"
              element={
                <PrivateRoute>
                  <TradingView />
                </PrivateRoute>
              }
            />
            <Route
              path="/wallet"
              element={
                <PrivateRoute>
                  <Wallet />
                </PrivateRoute>
              }
            />
            <Route
              path="/security"
              element={
                <PrivateRoute>
                  <SecuritySettings />
                </PrivateRoute>
              }
            />
            <Route
              path="/api-keys"
              element={
                <PrivateRoute>
                  <APIKeys />
                </PrivateRoute>
              }
            />
            <Route
              path="/kyc"
              element={
                <PrivateRoute>
                  <KYC />
                </PrivateRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <PrivateRoute>
                  <AdminPanel />
                </PrivateRoute>
              }
            />
            <Route path="/" element={<Navigate to="/dashboard" />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;