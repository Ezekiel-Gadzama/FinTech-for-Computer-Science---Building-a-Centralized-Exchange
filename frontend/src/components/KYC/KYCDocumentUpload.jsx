import React, { useState, useEffect } from 'react';
import { uploadKYCDocument, getKYCDocuments } from '../../services/api';
import toast from 'react-hot-toast';

const KYCDocumentUpload = () => {
  const [documents, setDocuments] = useState([]);
  const [selectedType, setSelectedType] = useState('passport');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const response = await getKYCDocuments();
      setDocuments(response.data.documents);
    } catch (error) {
      console.error('Error loading documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (selectedFile.size > 10 * 1024 * 1024) {
        toast.error('File size must be less than 10MB');
        return;
      }
      setFile(selectedFile);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      toast.error('Please select a file');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('document_type', selectedType);

      await uploadKYCDocument(formData);
      toast.success('Document uploaded successfully!');
      setFile(null);
      setSelectedType('passport');
      e.target.reset();
      loadDocuments();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      verified: 'badge-success',
      pending: 'badge-warning',
      rejected: 'badge-danger',
      expired: 'badge-secondary'
    };
    return badges[status] || 'badge-secondary';
  };

  if (loading) {
    return <div className="loading"><div className="spinner"></div></div>;
  }

  return (
    <div className="card">
      <h3 style={{ marginBottom: '20px' }}>Upload KYC Documents</h3>
      <p style={{ marginBottom: '24px', color: 'var(--text-secondary)' }}>
        Upload required documents for KYC verification. Supported formats: PDF, PNG, JPG (Max 10MB)
      </p>

      <form onSubmit={handleUpload} style={{ marginBottom: '32px' }}>
        <div className="form-group">
          <label className="form-label">Document Type</label>
          <select
            className="input"
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
          >
            <option value="passport">Passport</option>
            <option value="id_card">National ID Card</option>
            <option value="driver_license">Driver's License</option>
            <option value="proof_of_address">Proof of Address</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Document File</label>
          <input
            type="file"
            className="input"
            accept=".pdf,.png,.jpg,.jpeg,.gif"
            onChange={handleFileChange}
            required
          />
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={uploading || !file}
          style={{ width: '100%' }}
        >
          {uploading ? 'Uploading...' : 'Upload Document'}
        </button>
      </form>

      <div>
        <h4 style={{ marginBottom: '16px' }}>Uploaded Documents</h4>
        {documents.length === 0 ? (
          <p style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-secondary)' }}>
            No documents uploaded yet
          </p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Type</th>
                <th>File Name</th>
                <th>Status</th>
                <th>Uploaded</th>
              </tr>
            </thead>
            <tbody>
              {documents.map(doc => (
                <tr key={doc.id}>
                  <td>{doc.document_type.replace('_', ' ').toUpperCase()}</td>
                  <td>{doc.file_name}</td>
                  <td>
                    <span className={`badge ${getStatusBadge(doc.status)}`}>
                      {doc.status}
                    </span>
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    {new Date(doc.uploaded_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default KYCDocumentUpload;

