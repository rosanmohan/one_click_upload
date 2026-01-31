import { useState, useRef } from 'react';
import axios from 'axios';
import { Upload, CheckCircle, XCircle, AlertCircle, FileVideo, Loader2, Power, X, Trash2, ArrowUp, ArrowDown, User, Calendar } from 'lucide-react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import './App.css';
import ScheduledUploads from './ScheduledUploads';

function App() {
  const [files, setFiles] = useState([]);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [hashtags, setHashtags] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadQueue, setUploadQueue] = useState([]); // [{ file, status: 'pending'|'uploading'|'success'|'error', progress: 0, result: null }]
  const [error, setError] = useState('');
  const [serverStatus, setServerStatus] = useState('idle'); // idle, activating, active, error
  const [showModal, setShowModal] = useState(false);

  const [mergeVideos, setMergeVideos] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState('kids_fun'); // Default profile

  // Scheduling feature
  const [isScheduled, setIsScheduled] = useState(false);
  const [scheduledDateTime, setScheduledDateTime] = useState(null); // Changed to Date object for DatePicker
  const [currentView, setCurrentView] = useState('upload'); // 'upload' or 'scheduled'

  // currentFileIndex tracks which file is currently being processed in the loop
  const [currentFileIndex, setCurrentFileIndex] = useState(-1);
  const abortControllerRef = useRef(null);

  // Helper to get Base URL
  const getBaseUrl = () => import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files);
      setFiles(prev => [...prev, ...newFiles]);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files);
      setFiles(prev => [...prev, ...newFiles]);
    }
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const moveFile = (index, direction) => {
    setFiles(prev => {
      const newFiles = [...prev];
      const targetIndex = index + direction;
      // Safety check
      if (targetIndex < 0 || targetIndex >= newFiles.length) return prev;

      // Swap
      [newFiles[index], newFiles[targetIndex]] = [newFiles[targetIndex], newFiles[index]];
      return newFiles;
    });
  };

  const handleCancelUpload = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setLoading(false);
    setShowModal(false);
    setCurrentFileIndex(-1);
    setUploadQueue([]);
  };

  const handleScheduledUpload = async (e) => {
    e.preventDefault();

    // Validation
    if (files.length === 0) {
      setError("Please select at least one video file.");
      return;
    }
    if (!scheduledDateTime) {
      setError("Please select a date and time for the upload.");
      return;
    }

    setError('');
    setLoading(true);


    const baseUrl = getBaseUrl();
    const formData = new FormData();

    // Support multiple files (with optional merge) for scheduled uploads
    if (files.length === 1) {
      // Single file
      formData.append('file', files[0]);
      const uploadTitle = title.trim() || files[0].name.replace(/\.[^/.]+$/, '');
      formData.append('title', uploadTitle);
    } else {
      // Multiple files - attach all and set merge flag
      files.forEach((file) => {
        formData.append('files', file);
      });
      const uploadTitle = title.trim() || `${files.length} videos merged`;
      formData.append('title', uploadTitle);
      formData.append('merge_videos', mergeVideos ? 'true' : 'false');
    }

    formData.append('description', description);
    formData.append('hashtags', hashtags);

    // Convert local datetime to UTC ISO 8601 format
    const localDate = new Date(scheduledDateTime);
    const utcDateString = localDate.toISOString(); // Converts to UTC: "2026-01-29T17:10:00.000Z"
    formData.append('scheduled_time', utcDateString);

    formData.append('profile_id', selectedProfile);
    formData.append('upload_youtube', 'true');
    formData.append('upload_facebook', 'true');
    formData.append('upload_instagram', 'true');

    try {
      const response = await axios.post(
        `${baseUrl}/api/scheduled/upload`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      );

      if (response.data.success) {
        alert(`✅ Upload scheduled successfully for ${new Date(scheduledDateTime).toLocaleString()}!`);

        // Reset form
        setFiles([]);
        setTitle('');
        setDescription('');
        setHashtags('');
        setScheduledDateTime('');
        setIsScheduled(false);

        // Switch to scheduled view
        setCurrentView('scheduled');
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      setError(`Failed to schedule upload: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (files.length === 0) {
      setError("Please select at least one video file.");
      return;
    }
    setError('');
    setLoading(true);
    setShowModal(true);

    const baseUrl = getBaseUrl();

    // --- MERGE LOGIC ---
    if (mergeVideos && files.length > 1) {
      // 1. Setup Queue for Single Merged Item
      const mergedItem = {
        file: { name: `Merged Video (${files.length} clips)` },
        status: 'uploading',
        progress: 0,
        results: null,
        errorMsg: ''
      };
      setUploadQueue([mergedItem]);
      setCurrentFileIndex(0);

      abortControllerRef.current = new AbortController();
      const formData = new FormData();

      // Append all files to 'files' key (Backend expects List[UploadFile] at 'files')
      files.forEach(f => formData.append('files', f));

      formData.append('title', title);
      formData.append('description', description);
      formData.append('hashtags', hashtags);
      formData.append('merge', 'true');
      formData.append('profile_id', selectedProfile);

      try {
        console.log(`[DEBUG] Starting merged upload for ${files.length} files`);
        const response = await axios.post(`${baseUrl}/api/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          signal: abortControllerRef.current.signal,
          onUploadProgress: (progressEvent) => {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadQueue(prev => {
              const newQ = [...prev];
              if (newQ[0]) newQ[0].progress = percent;
              return newQ;
            });
          }
        });

        // Success
        setUploadQueue(prev => {
          const newQ = [...prev];
          if (newQ[0]) {
            newQ[0].status = 'success';
            newQ[0].results = response.data.results;
            newQ[0].progress = 100;
          }
          return newQ;
        });

      } catch (err) {
        if (axios.isCancel(err)) {
          console.log('Upload cancelled');
        } else {
          console.error(`[DEBUG] Error uploading merged video:`, err);
          setUploadQueue(prev => {
            const newQ = [...prev];
            if (newQ[0]) {
              newQ[0].status = 'error';
              newQ[0].errorMsg = err.response?.data?.detail || err.message;
            }
            return newQ;
          });
        }
      }

    } else {
      // --- EXISTING SEQUENTIAL LOGIC ---
      // Initialize Queue
      const initialQueue = files.map(f => ({
        file: f,
        status: 'pending',
        progress: 0,
        results: null,
        errorMsg: ''
      }));
      setUploadQueue(initialQueue);
      setCurrentFileIndex(0);

      // Iterate sequentially
      for (let i = 0; i < initialQueue.length; i++) {
        const queueItem = initialQueue[i];
        setCurrentFileIndex(i);

        // Update status to uploading
        setUploadQueue(prev => {
          const newQ = [...prev];
          newQ[i].status = 'uploading';
          return newQ;
        });

        abortControllerRef.current = new AbortController();

        const formData = new FormData();
        formData.append('file', queueItem.file); // Backend supports 'file' for single uploads too
        // Use global title if only 1 file, else let backend determine or use filename
        formData.append('title', files.length === 1 ? title : '');
        formData.append('description', description);
        formData.append('hashtags', hashtags);
        formData.append('profile_id', selectedProfile);
        // merge is false by default

        try {
          console.log(`[DEBUG] Starting upload for ${queueItem.file.name}`);
          const response = await axios.post(`${baseUrl}/api/upload`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            signal: abortControllerRef.current.signal,
            onUploadProgress: (progressEvent) => {
              const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              setUploadQueue(prev => {
                const newQ = [...prev];
                newQ[i].progress = percent;
                return newQ;
              });
            }
          });

          // Success
          setUploadQueue(prev => {
            const newQ = [...prev];
            newQ[i].status = 'success';
            newQ[i].results = response.data.results;
            newQ[i].progress = 100;
            return newQ;
          });

        } catch (err) {
          if (axios.isCancel(err)) {
            console.log('Upload cancelled');
            // If cancelled, stop loop
            break;
          }
          console.error(`[DEBUG] Error uploading ${queueItem.file.name}:`, err);
          setUploadQueue(prev => {
            const newQ = [...prev];
            newQ[i].status = 'error';
            newQ[i].errorMsg = err.response?.data?.detail || err.message;
            return newQ;
          });
          // Continue to next file even if one fails? Yes.
        }
      }
    }

    setLoading(false);
    // Keep modal open to show results
  };

  return (
    <div className="app-container">
      <div className="glass-card">
        <header className="header">
          <div>
            <h1>Social Blast</h1>
            <p>Upload once, publish everywhere.</p>
          </div>

          {/* View Toggle */}
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
            <button
              type="button"
              onClick={() => setCurrentView('upload')}
              className={`view-toggle-btn ${currentView === 'upload' ? 'active' : ''}`}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                border: 'none',
                background: currentView === 'upload' ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'rgba(255, 255, 255, 0.1)',
                color: 'white',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontWeight: '500',
                transition: 'all 0.3s'
              }}
            >
              <Upload size={16} />
              Upload
            </button>
            <button
              type="button"
              onClick={() => setCurrentView('scheduled')}
              className={`view-toggle-btn ${currentView === 'scheduled' ? 'active' : ''}`}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                border: 'none',
                background: currentView === 'scheduled' ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'rgba(255, 255, 255, 0.1)',
                color: 'white',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontWeight: '500',
                transition: 'all 0.3s'
              }}
            >
              <Calendar size={16} />
              Scheduled
            </button>
          </div>
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

        {/* Upload View */}
        {currentView === 'upload' && (
          <form onSubmit={handleSubmit} style={{ opacity: serverStatus === 'active' ? 1 : 0.5, pointerEvents: serverStatus === 'active' ? 'auto' : 'none', transition: 'opacity 0.3s' }}>

            {/* Profile Selection */}
            <div className="form-group">
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <User size={18} /> Select Profile
              </label>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <label style={{
                  display: 'flex', alignItems: 'center', gap: '8px',
                  padding: '0.75rem 1rem',
                  background: selectedProfile === 'kids_fun' ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                  border: selectedProfile === 'kids_fun' ? '1px solid #8b5cf6' : '1px solid transparent',
                  borderRadius: '8px', cursor: 'pointer', flex: 1, transition: 'all 0.2s'
                }}>
                  <input
                    type="radio"
                    name="profile"
                    value="kids_fun"
                    checked={selectedProfile === 'kids_fun'}
                    onChange={(e) => setSelectedProfile(e.target.value)}
                    style={{ accentColor: '#8b5cf6' }}
                  />
                  <span style={{ fontWeight: '500' }}>Kids Fun</span>
                </label>

                <label style={{
                  display: 'flex', alignItems: 'center', gap: '8px',
                  padding: '0.75rem 1rem',
                  background: selectedProfile === 'ayesha' ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                  border: selectedProfile === 'ayesha' ? '1px solid #8b5cf6' : '1px solid transparent',
                  borderRadius: '8px', cursor: 'pointer', flex: 1, transition: 'all 0.2s'
                }}>
                  <input
                    type="radio"
                    name="profile"
                    value="ayesha"
                    checked={selectedProfile === 'ayesha'}
                    onChange={(e) => setSelectedProfile(e.target.value)}
                    style={{ accentColor: '#8b5cf6' }}
                  />
                  <span style={{ fontWeight: '500' }}>Ayesha</span>
                </label>
              </div>
            </div>

            {/* File Upload */}
            <div className="form-group">
              <label className="form-label">Video Files</label>
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
                  multiple
                  onChange={handleFileChange}
                />
                <Upload className="upload-icon" />
                <p style={{ margin: 0, color: '#94a3b8' }}>
                  Click to add videos or drag them here
                </p>
              </div>

              {/* File List */}
              {files.length > 0 && (
                <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {files.map((f, i) => (
                    <div key={i} className="file-info" style={{ justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{
                          background: '#334155',
                          color: 'white',
                          width: '20px',
                          height: '20px',
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '0.75rem',
                          fontWeight: 'bold'
                        }}>
                          {i + 1}
                        </span>
                        <FileVideo size={18} />
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '200px' }}>
                          {f.name}
                        </span>
                      </div>

                      <div style={{ display: 'flex', gap: '4px' }}>
                        {/* Reordering Controls */}
                        {files.length > 1 && (
                          <>
                            <button
                              type="button"
                              onClick={() => moveFile(i, -1)}
                              disabled={i === 0}
                              style={{
                                background: 'none', border: 'none', cursor: i === 0 ? 'default' : 'pointer',
                                color: i === 0 ? '#475569' : '#94a3b8', padding: '4px'
                              }}
                              title="Move Up"
                            >
                              <ArrowUp size={16} />
                            </button>
                            <button
                              type="button"
                              onClick={() => moveFile(i, 1)}
                              disabled={i === files.length - 1}
                              style={{
                                background: 'none', border: 'none', cursor: i === files.length - 1 ? 'default' : 'pointer',
                                color: i === files.length - 1 ? '#475569' : '#94a3b8', padding: '4px'
                              }}
                              title="Move Down"
                            >
                              <ArrowDown size={16} />
                            </button>
                            <div style={{ width: '1px', background: '#334155', margin: '0 4px' }}></div>
                          </>
                        )}

                        <button
                          type="button"
                          onClick={() => removeFile(i)}
                          style={{ background: 'none', border: 'none', color: '#f87171', cursor: 'pointer', padding: '4px' }}
                          title="Remove"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}

                  {files.length > 1 && (
                    <div style={{ marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '8px', padding: '0.5rem', background: 'rgba(139, 92, 246, 0.1)', borderRadius: '6px' }}>
                      <input
                        type="checkbox"
                        id="mergeCheck"
                        checked={mergeVideos}
                        onChange={(e) => setMergeVideos(e.target.checked)}
                        style={{ width: '16px', height: '16px', accentColor: '#8b5cf6', cursor: 'pointer' }}
                      />
                      <label htmlFor="mergeCheck" style={{ color: 'white', fontSize: '0.9rem', cursor: 'pointer', fontWeight: '500' }}>
                        Merge these <strong>{files.length}</strong> videos into one?
                      </label>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">Title (Optional)</label>
              <input
                type="text"
                className="form-input"
                placeholder={files.length > 1 ? "Ignored for multiple files (filenames will be used)" : "Amazing Video Title"}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={files.length > 1}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Description (for all videos)</label>
              <textarea
                className="form-textarea"
                placeholder="What is this video about?"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Hashtags (for all videos)</label>
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

            {/* Scheduling Toggle */}
            <div className="form-group" style={{
              background: 'rgba(139, 92, 246, 0.1)',
              padding: '1rem',
              borderRadius: '8px',
              border: '1px solid rgba(139, 92, 246, 0.3)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: isScheduled ? '1rem' : 0 }}>
                <input
                  type="checkbox"
                  id="scheduleCheck"
                  checked={isScheduled}
                  onChange={(e) => {
                    setIsScheduled(e.target.checked);
                    if (!e.target.checked) setScheduledDateTime('');
                  }}
                  style={{ width: '18px', height: '18px', accentColor: '#8b5cf6', cursor: 'pointer' }}
                />
                <label htmlFor="scheduleCheck" style={{
                  color: 'white',
                  fontSize: '1rem',
                  cursor: 'pointer',
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <Calendar size={18} />
                  Schedule for later?
                </label>
              </div>

              {isScheduled && (
                <div>
                  <label className="form-label" style={{ marginBottom: '0.5rem', display: 'block' }}>
                    Select Date & Time
                  </label>
                  <div style={{ position: 'relative' }}>
                    <DatePicker
                      selected={scheduledDateTime}
                      onChange={(date) => setScheduledDateTime(date)}
                      showTimeSelect
                      timeFormat="HH:mm"
                      timeIntervals={30}
                      dateFormat="MMMM d, yyyy h:mm aa"
                      minDate={new Date()}
                      placeholderText="Click to select date and time"
                      required={isScheduled}
                      inline
                      className="form-input"
                      calendarClassName="custom-calendar"
                      wrapperClassName="datepicker-wrapper"
                    >
                      <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        padding: '12px',
                        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                        background: 'rgba(31, 41, 55, 0.98)'
                      }}>
                        <button
                          type="button"
                          onClick={() => {
                            if (scheduledDateTime) {
                              // Scroll to confirmation
                              setTimeout(() => {
                                document.querySelector('.schedule-confirmation')?.scrollIntoView({
                                  behavior: 'smooth',
                                  block: 'nearest'
                                });
                              }, 100);
                            }
                          }}
                          style={{
                            padding: '10px 32px',
                            background: scheduledDateTime
                              ? 'linear-gradient(135deg, #8b5cf6, #7c3aed)'
                              : 'rgba(139, 92, 246, 0.3)',
                            color: 'white',
                            border: 'none',
                            borderRadius: '8px',
                            fontWeight: '600',
                            cursor: scheduledDateTime ? 'pointer' : 'not-allowed',
                            transition: 'all 0.2s',
                            fontSize: '1rem',
                            boxShadow: scheduledDateTime ? '0 4px 12px rgba(139, 92, 246, 0.4)' : 'none'
                          }}
                          disabled={!scheduledDateTime}
                        >
                          ✓ Set Schedule
                        </button>
                      </div>
                    </DatePicker>
                  </div>

                  {/* Confirmation message */}
                  {scheduledDateTime && (
                    <div className="schedule-confirmation" style={{
                      marginTop: '1rem',
                      padding: '1rem',
                      background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(139, 92, 246, 0.05))',
                      border: '2px solid rgba(139, 92, 246, 0.4)',
                      borderRadius: '12px',
                      animation: 'pulse 2s ease-in-out infinite'
                    }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem',
                        color: '#a78bfa',
                        fontSize: '1rem',
                        fontWeight: '600'
                      }}>
                        <Calendar size={20} />
                        <div>
                          <div style={{ fontSize: '0.85rem', color: '#9ca3af', marginBottom: '0.25rem' }}>Scheduled for:</div>
                          {scheduledDateTime.toLocaleString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                      </div>
                    </div>
                  )}

                  <div style={{
                    fontSize: '0.8rem',
                    color: scheduledDateTime ? '#8b5cf6' : '#94a3b8',
                    marginTop: '0.5rem',
                    display: 'flex',
                    alignItems: 'start',
                    gap: '0.5rem'
                  }}>
                    <span>💡</span>
                    <div>
                      {scheduledDateTime ? (
                        <span>
                          <strong>Scheduled for:</strong> {new Date(scheduledDateTime).toLocaleString('en-US', {
                            dateStyle: 'medium',
                            timeStyle: 'short'
                          })}
                        </span>
                      ) : (
                        <span>Click the calendar field above, select date and time, then click outside the picker to confirm</span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            <button
              type="submit"
              className="submit-btn"
              disabled={loading || files.length === 0}
              onClick={isScheduled ? handleScheduledUpload : handleSubmit}
            >
              {loading ? 'Processing...' : isScheduled ? '📅 Schedule Upload' : `🚀 Upload Now (${files.length > 0 ? files.length : 0} video${files.length !== 1 ? 's' : ''})`}
            </button>
          </form>
        )}

        {/* Scheduled Uploads View */}
        {currentView === 'scheduled' && (
          <ScheduledUploads baseUrl={getBaseUrl()} />
        )}
      </div>

      {/* Modal for Upload Queue & Progress */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}>
            <button className="close-btn" onClick={handleCancelUpload}>
              <X size={24} />
            </button>

            <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', textAlign: 'center' }}>
              {loading ? 'Processing Uploads' : 'Queue Complete'}
            </h2>

            <div style={{ overflowY: 'auto', paddingRight: '0.5rem', flex: 1 }}>
              {uploadQueue.map((item, index) => (
                <div key={index} style={{
                  background: 'rgba(255,255,255,0.05)',
                  marginBottom: '1rem',
                  borderRadius: '8px',
                  padding: '1rem',
                  border: currentFileIndex === index ? '1px solid #8b5cf6' : '1px solid transparent'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: '500', fontSize: '0.9rem', color: 'white' }}>{item.file.name}</span>
                    <span style={{ fontSize: '0.8rem', opacity: 0.7, textTransform: 'capitalize' }}>
                      {item.status === 'uploading' && item.progress === 100 ? (
                        <span className="finishing-text">
                          Finishing
                          <span className="finishing-dots">
                            <span>.</span>
                            <span>.</span>
                            <span>.</span>
                          </span>
                          <span className="spinner"></span>
                        </span>
                      ) : item.status}
                    </span>
                  </div>

                  {/* Progress Bar for Pending/Uploading */}
                  {(item.status === 'pending' || item.status === 'uploading') && (
                    <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%',
                        background: item.status === 'pending' ? 'transparent' : '#8b5cf6',
                        width: `${item.progress}%`,
                        transition: 'width 0.3s ease'
                      }}></div>
                    </div>
                  )}

                  {/* Error Msg */}
                  {item.status === 'error' && (
                    <div style={{ color: '#f87171', fontSize: '0.85rem', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <XCircle size={14} /> {item.errorMsg || 'Upload failed'}
                    </div>
                  )}

                  {/* Success Results */}
                  {item.status === 'success' && item.results && (
                    <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      {item.results.map((res, ridx) => (
                        <div key={ridx} style={{ display: 'flex', flexDirection: 'column', marginBottom: res.status === 'error' ? '0.5rem' : '0', width: res.status === 'error' ? '100%' : 'auto' }}>
                          <div style={{
                            fontSize: '0.75rem',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            background: res.status === 'success' ? 'rgba(74, 222, 128, 0.2)' : 'rgba(255,255,255,0.1)',
                            color: res.status === 'success' ? '#4ade80' : '#cbd5e1',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            width: 'fit-content'
                          }}>
                            {res.status === 'success' ? <CheckCircle size={12} /> : (res.status === 'error' ? <XCircle size={12} /> : <AlertCircle size={12} />)}
                            {res.platform}
                          </div>
                          {res.status === 'error' && res.message && (
                            <div style={{ color: '#f87171', fontSize: '0.75rem', marginTop: '2px', paddingLeft: '4px', wordBreak: 'break-word' }}>
                              Error: {res.message}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {!loading && (
              <button onClick={handleCancelUpload} className="submit-btn" style={{ marginTop: '1rem' }}>
                Close
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
