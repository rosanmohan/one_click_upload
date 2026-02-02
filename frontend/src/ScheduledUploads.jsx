import { useState, useEffect } from 'react';
import axios from 'axios';
import { Calendar, Clock, Trash2, RefreshCw, CheckCircle, XCircle, Loader2, Youtube, Facebook, Instagram } from 'lucide-react';

function ScheduledUploads({ baseUrl }) {
    const [uploads, setUploads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('pending'); // pending, completed, failed, all

    useEffect(() => {
        fetchScheduledUploads();
    }, [filter]);

    const fetchScheduledUploads = async () => {
        setLoading(true);
        try {
            const params = {};
            if (filter !== 'all') {
                params.status = filter;
            }

            const response = await axios.get(`${baseUrl}/api/scheduled/list`, { params });
            let fetchedUploads = response.data.uploads || [];

            // Sort by scheduled_time descending (latest first)
            fetchedUploads.sort((a, b) => new Date(b.scheduled_time) - new Date(a.scheduled_time));

            setUploads(fetchedUploads);
        } catch (error) {
            console.error('Failed to fetch scheduled uploads:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (uploadId) => {
        if (!confirm('Are you sure you want to cancel this scheduled upload?')) {
            return;
        }

        try {
            await axios.delete(`${baseUrl}/api/scheduled/${uploadId}`);
            setUploads(uploads.filter(u => u.id !== uploadId));
        } catch (error) {
            alert(`Failed to delete: ${error.response?.data?.detail || error.message}`);
        }
    };

    const formatDateTime = (isoString) => {
        const date = new Date(isoString);
        return new Intl.DateTimeFormat('en-US', {
            dateStyle: 'medium',
            timeStyle: 'short'
        }).format(date);
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'pending': return 'bg-blue-100 text-blue-800';
            case 'completed': return 'bg-green-100 text-green-800';
            case 'failed': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'pending': return <Clock className="w-4 h-4" />;
            case 'completed': return <CheckCircle className="w-4 h-4" />;
            case 'failed': return <XCircle className="w-4 h-4" />;
            default: return <Loader2 className="w-4 h-4 animate-spin" />;
        }
    };

    return (
        <div className="scheduled-uploads-container">
            <div className="scheduled-header">
                <h2>Scheduled Uploads</h2>
                <button onClick={fetchScheduledUploads} className="refresh-btn" title="Refresh">
                    <RefreshCw className="w-5 h-5" />
                </button>
            </div>

            <div className="filter-tabs">
                <button
                    className={`filter-tab ${filter === 'pending' ? 'active' : ''}`}
                    onClick={() => setFilter('pending')}
                >
                    Pending
                </button>
                <button
                    className={`filter-tab ${filter === 'completed' ? 'active' : ''}`}
                    onClick={() => setFilter('completed')}
                >
                    Completed
                </button>
                <button
                    className={`filter-tab ${filter === 'failed' ? 'active' : ''}`}
                    onClick={() => setFilter('failed')}
                >
                    Failed
                </button>
                <button
                    className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
                    onClick={() => setFilter('all')}
                >
                    All
                </button>
            </div>

            {loading ? (
                <div className="loading-state">
                    <Loader2 className="w-8 h-8 animate-spin" />
                    <p>Loading scheduled uploads...</p>
                </div>
            ) : uploads.length === 0 ? (
                <div className="empty-state">
                    <Calendar className="w-16 h-16 text-gray-300 mb-4" />
                    <p className="text-gray-500">No scheduled uploads found</p>
                </div>
            ) : (
                <div className="uploads-list">
                    {uploads.map((upload) => (
                        <div key={upload.id} className="upload-card">
                            <div className="upload-card-header">
                                <div className="upload-title">
                                    <h3>{upload.title}</h3>
                                    <span className={`status-badge ${getStatusColor(upload.status)}`}>
                                        {getStatusIcon(upload.status)}
                                        <span>{upload.status}</span>
                                    </span>
                                </div>
                                {upload.status === 'pending' && (
                                    <button
                                        onClick={() => handleDelete(upload.id)}
                                        className="delete-btn"
                                        title="Cancel upload"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                )}
                            </div>

                            <div className="upload-card-body">
                                <div className="upload-info">
                                    <div className="info-item">
                                        <Calendar className="w-4 h-4" />
                                        <span>Scheduled: {formatDateTime(upload.scheduled_time)}</span>
                                    </div>
                                    <div className="info-item">
                                        <span className="profile-badge">{upload.profile_id}</span>
                                    </div>
                                </div>

                                {upload.description && (
                                    <p className="upload-description">{upload.description}</p>
                                )}

                                <div className="platforms-row">
                                    {upload.upload_youtube === 1 && (
                                        <div className="platform-icon" title="YouTube">
                                            <Youtube className="w-5 h-5 text-red-600" />
                                            {upload.youtube_video_id && (
                                                <CheckCircle className="w-3 h-3 text-green-600" />
                                            )}
                                        </div>
                                    )}
                                    {upload.upload_facebook === 1 && (
                                        <div className="platform-icon" title="Facebook">
                                            <Facebook className="w-5 h-5 text-blue-600" />
                                            {upload.facebook_post_id && (
                                                <CheckCircle className="w-3 h-3 text-green-600" />
                                            )}
                                        </div>
                                    )}
                                    {upload.upload_instagram === 1 && (
                                        <div className="platform-icon" title="Instagram">
                                            <Instagram className="w-5 h-5 text-pink-600" />
                                            {upload.instagram_media_id && (
                                                <CheckCircle className="w-3 h-3 text-green-600" />
                                            )}
                                        </div>
                                    )}
                                </div>

                                {upload.error_message && (
                                    <div className="error-message">
                                        <XCircle className="w-4 h-4" />
                                        <span>{upload.error_message}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default ScheduledUploads;
