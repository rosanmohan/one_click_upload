import { useState } from 'react';
import axios from 'axios';
import { Upload, CheckCircle, XCircle, AlertCircle, FileVideo, Loader2 } from 'lucide-react';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [hashtags, setHashtags] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a video file first.");
      return;
    }
    setError('');
    setLoading(true);
    setResults(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('description', description);
    formData.append('hashtags', hashtags);

    try {
      // Use environment variable if available, else fallback to local IP
      const baseUrl = import.meta.env.VITE_API_URL || 'http://192.168.1.3:8000';
      const response = await axios.post(`${baseUrl}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });
      setResults(response.data.results);
    } catch (err) {
      console.error(err);
      setError("An error occurred during upload. Please ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="glass-card">
        <header className="header">
          <h1>Social Blast</h1>
          <p>Upload once, publish everywhere.</p>
        </header>

        <form onSubmit={handleSubmit}>
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
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                Uploading...
              </>
            ) : (
              <>
                Upload to All Platforms
              </>
            )}
          </button>
        </form>

        {results && (
          <div className="results-section">
            <h3 style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>Upload Results</h3>
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
  );
}

export default App;
