import React, { useState, useEffect } from 'react';
import { submitKYC, getKYCStatus } from '../../services/api';
import toast from 'react-hot-toast';

const KYCForm = () => {
  const [formData, setFormData] = useState({
    full_name: '',
    country: '',
    phone: '',
    address: '',
    city: '',
    postal_code: '',
    nationality: '',
    date_of_birth: ''
  });
  const [kycStatus, setKycStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    loadKYCStatus();
  }, []);

  const loadKYCStatus = async () => {
    try {
      const response = await getKYCStatus();
      setKycStatus(response.data);
      if (response.data.verified) {
        setSubmitted(true);
      }
    } catch (error) {
      console.error('Error loading KYC status:', error);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await submitKYC(formData);
      setSubmitted(true);
      toast.success('KYC information submitted successfully! Awaiting verification.');
      loadKYCStatus();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to submit KYC');
    } finally {
      setLoading(false);
    }
  };

  if (submitted && kycStatus?.verified) {
    return (
      <div className="card">
        <div style={{ textAlign: 'center', padding: '40px 20px' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>✓</div>
          <h3 style={{ marginBottom: '8px' }}>KYC Verified</h3>
          <p style={{ color: 'var(--text-secondary)' }}>
            Your KYC verification has been completed and approved.
          </p>
        </div>
      </div>
    );
  }

  if (submitted && !kycStatus?.verified) {
    return (
      <div className="card">
        <div style={{ textAlign: 'center', padding: '40px 20px' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
          <h3 style={{ marginBottom: '8px' }}>KYC Pending Verification</h3>
          <p style={{ color: 'var(--text-secondary)' }}>
            Your KYC information has been submitted and is awaiting admin verification.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 style={{ marginBottom: '20px' }}>KYC Verification</h3>
      <p style={{ marginBottom: '24px', color: 'var(--text-secondary)' }}>
        Complete your Know Your Customer (KYC) verification to unlock all features.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Full Name</label>
          <input
            type="text"
            name="full_name"
            className="input"
            value={formData.full_name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">Date of Birth</label>
          <input
            type="date"
            name="date_of_birth"
            className="input"
            value={formData.date_of_birth}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">Nationality</label>
          <input
            type="text"
            name="nationality"
            className="input"
            value={formData.nationality}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">Country</label>
          <input
            type="text"
            name="country"
            className="input"
            value={formData.country}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">Phone Number</label>
          <input
            type="tel"
            name="phone"
            className="input"
            value={formData.phone}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">Address</label>
          <input
            type="text"
            name="address"
            className="input"
            value={formData.address}
            onChange={handleChange}
            required
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div className="form-group">
            <label className="form-label">City</label>
            <input
              type="text"
              name="city"
              className="input"
              value={formData.city}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Postal Code</label>
            <input
              type="text"
              name="postal_code"
              className="input"
              value={formData.postal_code}
              onChange={handleChange}
              required
            />
          </div>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading}
          style={{ width: '100%', marginTop: '8px' }}
        >
          {loading ? 'Submitting...' : 'Submit KYC Information'}
        </button>
      </form>
    </div>
  );
};

export default KYCForm;

