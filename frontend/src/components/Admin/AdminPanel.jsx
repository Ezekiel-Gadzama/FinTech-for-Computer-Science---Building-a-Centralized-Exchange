import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { getPendingKYC, verifyKYC, rejectKYC, getUserDocuments } from '../../services/api';
import toast from 'react-hot-toast';
import { Navigate } from 'react-router-dom';
import Navbar from '../Common/Navbar';

const AdminPanel = () => {
  const { user } = useAuth();
  const [pendingKYC, setPendingKYC] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userDocuments, setUserDocuments] = useState([]);
  const [verificationNotes, setVerificationNotes] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [processingUserId, setProcessingUserId] = useState(null);

  useEffect(() => {
    // Only load KYC data if user is admin
    if (user && user.is_admin) {
      loadPendingKYC();
    }
  }, [user]);

  const loadPendingKYC = async () => {
    try {
      setLoading(true);
      const response = await getPendingKYC();
      setPendingKYC(response.data.pending_kyc || []);
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error('Admin access required');
      } else {
        toast.error(error.response?.data?.error || 'Failed to load pending KYC');
      }
    } finally {
      setLoading(false);
    }
  };

    // Redirect if not admin
  if (!user || !user.is_admin) {
    return <Navigate to="/dashboard" />;
  }

  const loadUserDocuments = async (userId) => {
    try {
      const response = await getUserDocuments(userId);
      setUserDocuments(response.data.documents || []);
    } catch (error) {
      console.error('Error loading documents:', error);
      toast.error('Failed to load user documents');
    }
  };

  const handleViewDetails = (kycRecord) => {
    setSelectedUser(kycRecord);
    setVerificationNotes('');
    setRejectionReason('');
    loadUserDocuments(kycRecord.user_id);
  };

  const handleApprove = async (userId) => {
    if (!window.confirm('Are you sure you want to approve this KYC verification?')) {
      return;
    }

    try {
      setProcessingUserId(userId);
      await verifyKYC(userId, {
        notes: verificationNotes || 'KYC approved by admin',
        aml_status: 'cleared',
        risk_score: 0
      });
      toast.success('KYC approved successfully');
      setSelectedUser(null);
      setVerificationNotes('');
      loadPendingKYC();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to approve KYC');
    } finally {
      setProcessingUserId(null);
    }
  };

  const handleReject = async (userId) => {
    if (!rejectionReason.trim()) {
      toast.error('Please provide a reason for rejection');
      return;
    }

    try {
      setProcessingUserId(userId);
      await rejectKYC(userId, {
        reason: rejectionReason
      });
      toast.success('KYC rejected');
      setSelectedUser(null);
      setRejectionReason('');
      setShowRejectModal(false);
      loadPendingKYC();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to reject KYC');
    } finally {
      setProcessingUserId(null);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <>
      <Navbar />
      <div className="container">
        <div style={{ marginBottom: '32px' }}>
          <h1 style={{ marginBottom: '8px' }}>Admin Panel - KYC Management</h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            Review and approve/reject KYC verification requests
          </p>
        </div>

      {selectedUser ? (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <h2>KYC Details - User ID: {selectedUser.user_id}</h2>
            <button
              className="btn btn-secondary"
              onClick={() => {
                setSelectedUser(null);
                setVerificationNotes('');
                setRejectionReason('');
              }}
            >
              ← Back to List
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
            <div>
              <h3 style={{ marginBottom: '16px' }}>Personal Information</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <strong>Full Name:</strong> {selectedUser.full_name || 'N/A'}
                </div>
                <div>
                  <strong>Date of Birth:</strong> {selectedUser.date_of_birth ? formatDate(selectedUser.date_of_birth) : 'N/A'}
                </div>
                <div>
                  <strong>Nationality:</strong> {selectedUser.nationality || 'N/A'}
                </div>
                <div>
                  <strong>Country:</strong> {selectedUser.country || 'N/A'}
                </div>
                <div>
                  <strong>Phone:</strong> {selectedUser.phone || 'N/A'}
                </div>
              </div>
            </div>

            <div>
              <h3 style={{ marginBottom: '16px' }}>Address Information</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <strong>Address:</strong> {selectedUser.address || 'N/A'}
                </div>
                <div>
                  <strong>City:</strong> {selectedUser.city || 'N/A'}
                </div>
                <div>
                  <strong>Postal Code:</strong> {selectedUser.postal_code || 'N/A'}
                </div>
              </div>
            </div>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ marginBottom: '16px' }}>Compliance Status</h3>
            <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
              <div>
                <strong>KYC Level:</strong> {selectedUser.kyc_level}
              </div>
              <div>
                <strong>AML Status:</strong> 
                <span className={`badge ${selectedUser.aml_status === 'cleared' ? 'badge-success' : 'badge-warning'}`}>
                  {selectedUser.aml_status}
                </span>
              </div>
              <div>
                <strong>PEP Status:</strong> {selectedUser.pep_status ? 'Yes' : 'No'}
              </div>
              <div>
                <strong>Sanctions Check:</strong> {selectedUser.sanctions_check ? 'Passed' : 'Pending'}
              </div>
              <div>
                <strong>Risk Score:</strong> {selectedUser.risk_score || 0}/100
              </div>
            </div>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ marginBottom: '16px' }}>Timestamps</h3>
            <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
              <div>
                <strong>Submitted:</strong> {formatDate(selectedUser.submitted_at)}
              </div>
            </div>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ marginBottom: '16px' }}>Uploaded Documents</h3>
            {userDocuments.length === 0 ? (
              <p style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                No documents uploaded yet
              </p>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>File Name</th>
                      <th>Size</th>
                      <th>Status</th>
                      <th>Uploaded</th>
                    </tr>
                  </thead>
                  <tbody>
                    {userDocuments.map((doc) => (
                      <tr key={doc.id}>
                        <td>{doc.document_type.replace('_', ' ').toUpperCase()}</td>
                        <td>{doc.file_name}</td>
                        <td>{(doc.file_size / 1024).toFixed(2)} KB</td>
                        <td>
                          <span className={`badge ${
                            doc.status === 'verified' ? 'badge-success' :
                            doc.status === 'rejected' ? 'badge-danger' :
                            'badge-warning'
                          }`}>
                            {doc.status}
                          </span>
                        </td>
                        <td>{formatDate(doc.uploaded_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label className="form-label">Verification Notes (optional)</label>
            <textarea
              className="input"
              rows="3"
              value={verificationNotes}
              onChange={(e) => setVerificationNotes(e.target.value)}
              placeholder="Add any notes about this verification..."
            />
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              className="btn btn-success"
              onClick={() => handleApprove(selectedUser.user_id)}
              disabled={processingUserId === selectedUser.user_id}
            >
              {processingUserId === selectedUser.user_id ? 'Processing...' : '✓ Approve KYC'}
            </button>
            <button
              className="btn btn-danger"
              onClick={() => setShowRejectModal(true)}
              disabled={processingUserId === selectedUser.user_id}
            >
              ✗ Reject KYC
            </button>
          </div>
        </div>
      ) : (
        <>
          {pendingKYC.length === 0 ? (
            <div className="card">
              <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>✓</div>
                <h3 style={{ marginBottom: '8px' }}>No Pending KYC</h3>
                <p style={{ color: 'var(--text-secondary)' }}>
                  All KYC verifications have been processed.
                </p>
              </div>
            </div>
          ) : (
            <div className="card">
              <h2 style={{ marginBottom: '24px' }}>Pending KYC Verifications ({pendingKYC.length})</h2>
              <div style={{ overflowX: 'auto' }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>User ID</th>
                      <th>Full Name</th>
                      <th>Country</th>
                      <th>KYC Level</th>
                      <th>AML Status</th>
                      <th>Submitted</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingKYC.map((kyc) => (
                      <tr key={kyc.id}>
                        <td>{kyc.user_id}</td>
                        <td>{kyc.full_name || 'N/A'}</td>
                        <td>{kyc.country || 'N/A'}</td>
                        <td>{kyc.kyc_level}</td>
                        <td>
                          <span className={`badge ${kyc.aml_status === 'cleared' ? 'badge-success' : 'badge-warning'}`}>
                            {kyc.aml_status}
                          </span>
                        </td>
                        <td>{formatDate(kyc.submitted_at)}</td>
                        <td>
                          <button
                            className="btn btn-primary"
                            onClick={() => handleViewDetails(kyc)}
                            style={{ fontSize: '14px', padding: '6px 12px' }}
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div className="card" style={{ maxWidth: '500px', width: '90%' }}>
            <h3 style={{ marginBottom: '16px' }}>Reject KYC Verification</h3>
            <p style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>
              Please provide a reason for rejecting this KYC verification. This will be visible to the user.
            </p>
            <div className="form-group">
              <label className="form-label">Rejection Reason *</label>
              <textarea
                className="input"
                rows="4"
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Enter the reason for rejection..."
                required
              />
            </div>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectionReason('');
                }}
              >
                Cancel
              </button>
              <button
                className="btn btn-danger"
                onClick={() => handleReject(selectedUser.user_id)}
                disabled={!rejectionReason.trim() || processingUserId === selectedUser.user_id}
              >
                {processingUserId === selectedUser.user_id ? 'Processing...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </>
  );
};

export default AdminPanel;

