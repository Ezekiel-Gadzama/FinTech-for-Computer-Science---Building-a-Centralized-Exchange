import React from 'react';
import Navbar from '../Common/Navbar';
import KYCForm from './KYCForm';
import KYCDocumentUpload from './KYCDocumentUpload';

const KYC = () => {
  return (
    <>
      <Navbar />
      <div className="container">
        <h1 style={{ marginBottom: '32px' }}>KYC Verification</h1>
        <KYCForm />
        <div style={{ marginTop: '24px' }}>
          <KYCDocumentUpload />
        </div>
      </div>
    </>
  );
};

export default KYC;

