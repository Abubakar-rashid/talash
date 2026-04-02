import React, { useState } from 'react';

export default function CVUpload() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a PDF file first");
      return;
    }

    setLoading(true);
    setStatus('Uploading and parsing...');

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/cv/upload", {  // the port at which backend is running
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      
      if (response.ok) {
        setStatus(`Success! Document parsed. Extracted ${result.characters_extracted} characters.`);
      } else {
        setStatus(`Error: ${result.detail || 'Failed to upload'}`);
      }
    } catch (error) {
      setStatus(`Error connecting to server: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px', maxWidth: '400px', margin: '20px auto' }}>
      <h2>Upload CV</h2>
      <div style={{ marginBottom: '15px' }}>
        <input 
          type="file" 
          accept=".pdf" 
          onChange={handleFileChange} 
          disabled={loading}
        />
      </div>
      <button 
        onClick={handleUpload} 
        disabled={loading || !file}
        style={{ padding: '8px 16px', background: '#aa3bff', color: 'white', border: 'none', borderRadius: '4px', cursor: (loading || !file) ? 'not-allowed' : 'pointer' }}
      >
        {loading ? 'Processing...' : 'Upload and Parse'}
      </button>

      {status && (
        <div style={{ marginTop: '15px', color: status.startsWith('Error') ? 'red' : 'green' }}>
          {status}
        </div>
      )}
    </div>
  );
}
