import { useState, useRef } from 'react';
import axios from 'axios';
import { Upload, CheckCircle, XCircle, AlertCircle, FileVideo, Loader2, Power, X } from 'lucide-react';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [hashtags, setHashtags] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [serverStatus, setServerStatus] = useState('idle'); // idle, activating, active, error
  const [showModal, setShowModal] = useState(false);

  const [uploadProgress, setUploadProgress] = useState(0);
  const abortControllerRef = useRef(null);

  // Helper to get Base URL
  const getBaseUrl = () => import.meta.env.VITE_API_URL || 'http://192.168.1.3:8000';

  const activateServer = async () => {
    setServerStatus('activating');
    setError('');
    try {
      const baseUrl = getBaseUrl();
      console.log(`[DEBUG] Activating server at: ${baseUrl}`);
      await axios.get(`${baseUrl}/health`);
      setServerStatus('active');
    } catch (err) {
      console.error("[DEBUG] Activation failed:", err);
      setServerStatus('error');
      setError("Failed to wake up server. Please try again.");
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleCancelUpload = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setLoading(false);
    setShowModal(false);
    setUploadProgress(0);
    setResults(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a video file first.");
      return;
    }
    setError('');
    setLoading(true);
    setUploadProgress(0);
    setResults(null);
    setShowModal(true);

    // Create a new AbortController for this request
    abortControllerRef.current = new AbortController();

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('description', description);
    formData.append('hashtags', hashtags);

    try {
      const baseUrl = getBaseUrl();
      console.log(`[DEBUG] Starting upload request to: ${baseUrl}/api/upload`);

      const response = await axios.post(`${baseUrl}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        signal: abortControllerRef.current.signal,
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
          console.log(`[DEBUG] Upload Progress: ${percentCompleted}%`);
        }
      });
      console.log(`[DEBUG] Upload Success:`, response.data);
      setResults(response.data.results);
    } catch (err) {
      if (axios.isCancel(err)) {
        console.log('Upload cancelled by user');
        return; // Don't set error state if cancelled
      }
      console.error("[DEBUG] Upload Error Object:", err);
      if (err.response) {
        console.error("[DEBUG] Server responded with:", err.response.status, err.response.data);
      } else if (err.request) {
        console.error("[DEBUG] No response received. Request:", err.request);
      } else {
        console.error("[DEBUG] Error setting up request:", err.message);
      }
      // If modal is still open, show error there
      // Otherwise set global error
      if (showModal) {
        // We might want to keep the modal open to show the error
        // For now, let's keep it simple
      }
      setError("An error occurred during upload. " + err.message);
    } finally {
      if (abortControllerRef.current && !abortControllerRef.current.signal.aborted) {
        setLoading(false);
        setUploadProgress(0);
      }
    }
  };

  return (
    <div className="app-container">
      <div className="glass-card">
        <header className="header">
          <h1>Social Blast</h1>
          <p>Upload once, publish everywhere.</p>
        </header>

        {/* Server Activation Section */}
        {serverStatus !== 'active' && (
          <div className="server-status-section" style={{
            marginBottom: '1.5rem',
            padding: '1rem',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center'
          }}>
            {serverStatus === 'idle' || serverStatus === 'error' ? (
              <button
                onClick={activateServer}
                className="activate-btn"
                style={{
                  background: '#e11d48',
                  border: 'none',
                  padding: '0.75rem 2rem',
                  borderRadius: '8px',
                  color: 'white',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  fontSize: '1.1rem',
                  fontWeight: '600',
                  boxShadow: '0 4px 14px 0 rgba(225, 29, 72, 0.39)',
                  transition: 'transform 0.2s ease'
                }}
                onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.02)'}
                onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
              >
                <Power size={20} /> Activate Server
              </button>
            ) : (
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '0.5rem',
                color: '#fbbf24'
              }}>
                <Loader2 className="animate-spin" size={32} />
                <span style={{ fontSize: '0.9rem', fontWeight: '500' }}>Waking up server...</span>
              </div>
            )}
          </div>
        )}

        {serverStatus === 'active' && (
          <div style={{
            textAlign: 'center',
            marginBottom: '2rem',
            color: '#4ade80',
            background: 'rgba(74, 222, 128, 0.1)',
            padding: '0.75rem',
            borderRadius: '8px',
            border: '1px solid rgba(74, 222, 128, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem'
          }}>
            <CheckCircle size={20} />
            <span style={{ fontWeight: '500' }}>Server Connected</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ opacity: serverStatus === 'active' ? 1 : 0.5, pointerEvents: serverStatus === 'active' ? 'auto' : 'none', transition: 'opacity 0.3s' }}>
          {/* File Upload */}
          <div className="form-group">
            <label className="form-label">Video File</label>
            <div
              className="file-upload-zone"
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              onClick={() => document.getElementById('fileInput').click()}
            >
              <input
                type="file"
                id="fileInput"
                className="file-input"
                accept="video/*"
                onChange={handleFileChange}
              />
              {!file ? (
                <>
                  <Upload className="upload-icon" />
                  <p style={{ margin: 0, color: '#94a3b8' }}>Click or drag video here</p>
                </>
              ) : (
                <div className="file-info">
                  <FileVideo size={18} />
                  <span>{file.name}</span>
                </div>
              )}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Title (Optional)</label>
            <input
              type="text"
              className="form-input"
              placeholder="Amazing Video Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Description (Optional)</label>
            <textarea
              className="form-textarea"
              placeholder="What is this video about?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Select Hashtags (Optional)</label>
            <select
              className="form-input"
              value={hashtags}
              onChange={(e) => setHashtags(e.target.value)}
            >
              <option value="">-- Select Hashtags --</option>
              <option value="#viral #trending #reels">Viral & Trending (#viral #trending #reels)</option>
              <option value="#comedy #funny #lol">Comedy & Fun (#comedy #funny #lol)</option>
              <option value="#tech #innovation #gadgets">Technology (#tech #innovation)</option>
              <option value="#travel #wanderlust #adventure">Travel (#travel #wanderlust)</option>
              <option value="#food #foodie #delicious">Food & Cooking (#food #foodie)</option>
              <option value="#fitness #gym #workout">Fitness & Health (#fitness #gym)</option>
              <option value="#music #song #dance">Music & Dance (#music #song)</option>
              <option value="#motivation #inspiration #quotes">Motivation (#motivation #quotes)</option>
              <option value="#nature #beautiful #earth">Nature (#nature #beautiful)</option>
              <option value="#gaming #gamer #stream">Gaming (#gaming #gamer)</option>
            </select>
          </div>

          {error && <p style={{ color: '#f87171', fontSize: '0.9rem', marginBottom: '1rem' }}>{error}</p>}

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? 'Processing...' : 'Upload to All Platforms'}
          </button>
        </form>
      </div>

      {/* Modal for Upload Progress & Results */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <button className="close-btn" onClick={handleCancelUpload}>
              <X size={24} />
            </button>

            <h2 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', textAlign: 'center' }}>
              {loading ? 'Upload in Progress' : 'Upload Complete'}
            </h2>

            {/* Dynamic Status Message */}
            <p style={{ textAlign: 'center', marginBottom: '1rem', color: '#cbd5e1' }}>
              {loading ? (
                <>{file?.name} uploading...</>
              ) : (
                <>{file?.name} uploaded successfully</>
              )}
            </p>

            {loading && uploadProgress < 100 && (
              <div className="progress-container" style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#cbd5e1' }}>
                  <span>Uploading...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div style={{ height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', background: '#8b5cf6', width: `${uploadProgress}%`, transition: 'width 0.3s ease' }}></div>
                </div>
              </div>
            )}

            {loading && uploadProgress === 100 && (
              <div style={{ textAlign: 'center', marginBottom: '1rem', color: '#cbd5e1' }}>
                <Loader2 className="animate-spin" style={{ margin: '0 auto 0.5rem', display: 'block' }} />
                <p>Processing & Publishing to Platforms...</p>
                <p style={{ fontSize: '0.8rem', opacity: 0.7 }}>This might take a minute.</p>
              </div>
            )}

            {results && (
              <div className="results-section" style={{ marginTop: '1rem', maxHeight: '300px', overflowY: 'auto' }}>
                {results.map((res, idx) => (
                  <div key={idx} className="result-item">
                    <span className="result-platform">{res.platform}</span>
                    <div className="result-status">
                      {res.status === 'success' && (
                        <><CheckCircle size={18} className="status-success" /> Success</>
                      )}
                      {res.status === 'skipped' && (
                        <><AlertCircle size={18} className="status-skipped" /> Skipped</>
                      )}
                      {res.status === 'error' && (
                        <><XCircle size={18} className="status-error" /> Failed</>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
