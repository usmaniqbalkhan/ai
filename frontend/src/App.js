import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const YouTubeChannelAnalyzer = () => {
  const [channelUrl, setChannelUrl] = useState('');
  const [videoCount, setVideoCount] = useState(20);
  const [sortOrder, setSortOrder] = useState('newest');
  const [timezone, setTimezone] = useState(Intl.DateTimeFormat().resolvedOptions().timeZone);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const timezoneOptions = [
    'UTC',
    'America/New_York',
    'America/Los_Angeles',
    'America/Chicago',
    'Europe/London',
    'Europe/Paris',
    'Europe/Berlin',
    'Asia/Tokyo',
    'Asia/Shanghai',
    'Asia/Kolkata',
    'Australia/Sydney',
    'America/Sao_Paulo'
  ];

  // Helper function for timezone-aware formatting using built-in JS
  const formatTimeWithTimezone = (utcTimestamp, userTimezone) => {
    try {
      const utcDate = new Date(utcTimestamp);
      return utcDate.toLocaleString('en-US', {
        timeZone: userTimezone,
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      });
    } catch (e) {
      return utcTimestamp; // Fallback to original if formatting fails
    }
  };

  const handleAnalyze = async () => {
    if (!channelUrl.trim()) {
      setError('Please enter a YouTube channel URL');
      return;
    }

    setLoading(true);
    setError('');
    setAnalysis(null);

    try {
      const response = await axios.post(`${API}/analyze-channel`, {
        channel_url: channelUrl,
        video_count: videoCount,
        sort_order: sortOrder,
        timezone: timezone
      });

      setAnalysis(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze channel');
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = () => {
    if (!analysis) return;

    const headers = ['Title', 'Video ID', 'Category', 'Upload Date (UTC)', 'Upload Date (Local)', 'Duration', 'Views', 'Likes', 'Comments', 'Engagement Rate %', 'Time Gap'];
    
    const csvContent = [
      headers.join(','),
      ...analysis.videos.map(video => [
        `"${video.title.replace(/"/g, '""')}"`,
        video.id,
        `"${video.category}"`,
        `"${video.upload_date_utc}"`,
        `"${video.upload_date_local}"`,
        video.duration,
        video.views,
        video.likes,
        video.comments,
        video.engagement_rate,
        `"${video.time_gap_text}"`
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${analysis.channel_info.name}_analysis.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const exportToJSON = () => {
    if (!analysis) return;

    const blob = new Blob([JSON.stringify(analysis, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${analysis.channel_info.name}_analysis.json`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🎬 YouTube Channel Analyzer
          </h1>
          <p className="text-gray-600 text-lg">
            Professional-grade analytics with accurate timestamps and categories
          </p>
        </div>

        {/* Input Section */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                YouTube Channel URL
              </label>
              <input
                type="text"
                value={channelUrl}
                onChange={(e) => setChannelUrl(e.target.value)}
                placeholder="https://youtube.com/@channel or channel/user URL"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Video Count
              </label>
              <select
                value={videoCount}
                onChange={(e) => setVideoCount(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value={5}>First 5</option>
                <option value={10}>First 10</option>
                <option value={20}>First 20</option>
                <option value={50}>First 50</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sort Order
              </label>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <span className="flex items-center gap-2">
                  🕐 Timezone (for accurate timestamps)
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Enhanced</span>
                </span>
              </label>
              <select
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                {timezoneOptions.map(tz => (
                  <option key={tz} value={tz}>{tz}</option>
                ))}
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={handleAnalyze}
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2 px-4 rounded-lg transition duration-200"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Analyzing...
                  </span>
                ) : (
                  '🔍 Analyze Channel'
                )}
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              ❌ {error}
            </div>
          )}
        </div>

        {/* Analysis Results */}
        {analysis && (
          <div className="space-y-6">
            {/* Channel Overview */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
                📊 Channel Overview
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="text-center">
                  <h3 className="text-3xl font-bold text-blue-600">{analysis.channel_info.name}</h3>
                  <p className="text-gray-600">Channel Name</p>
                </div>
                
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-green-600">{analysis.channel_info.subscriber_count}</h3>
                  <p className="text-gray-600">Subscribers</p>
                </div>
                
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-purple-600">{analysis.channel_info.total_uploads.toLocaleString()}</h3>
                  <p className="text-gray-600">Total Videos</p>
                </div>
                
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-red-600">{analysis.channel_info.total_views.toLocaleString()}</h3>
                  <p className="text-gray-600">Total Views</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6 pt-6 border-t">
                <div className="text-center">
                  <h4 className="font-semibold text-gray-700">Created</h4>
                  <p className="text-gray-600">{analysis.channel_info.creation_date}</p>
                </div>
                
                <div className="text-center">
                  <h4 className="font-semibold text-gray-700">Primary Category</h4>
                  <div className="flex items-center justify-center gap-2">
                    <p className="text-gray-600 font-medium bg-gradient-to-r from-purple-100 to-blue-100 px-3 py-1 rounded-full inline-block">
                      🏷️ {analysis.channel_info.primary_category}
                    </p>
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Enhanced</span>
                  </div>
                </div>
                
                <div className="text-center">
                  <h4 className="font-semibold text-gray-700">Monetization</h4>
                  <p className="text-gray-600">{analysis.channel_info.monetization_status}</p>
                </div>
              </div>
            </div>

            {/* Analytics Summary */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
                📈 Analytics Summary
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-blue-600">{analysis.total_likes.toLocaleString()}</h3>
                  <p className="text-gray-600">Total Likes</p>
                </div>
                
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-green-600">{analysis.total_comments.toLocaleString()}</h3>
                  <p className="text-gray-600">Total Comments</p>
                </div>
                
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-purple-600">{analysis.avg_views_per_video.toLocaleString()}</h3>
                  <p className="text-gray-600">Avg Views/Video</p>
                </div>
                
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-red-600">{analysis.channel_info.recent_views_30_days.toLocaleString()}</h3>
                  <p className="text-gray-600">Recent Views (30d)</p>
                </div>
              </div>
            </div>

            {/* Export Options */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">📁 Export Data</h2>
              <div className="flex gap-4">
                <button
                  onClick={exportToCSV}
                  className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200"
                >
                  📄 Export CSV
                </button>
                <button
                  onClick={exportToJSON}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200"
                >
                  📋 Export JSON
                </button>
              </div>
            </div>

            {/* Video Analysis Table */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                🎥 Video Analysis ({analysis.videos.length} videos) 
                <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">Timezone: {timezone}</span>
                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Enhanced</span>
              </h2>
              
              <div className="overflow-x-auto">
                <table className="w-full table-auto">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Video</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                        <span className="flex items-center gap-1">
                          Category 
                          <span className="text-xs bg-purple-100 text-purple-800 px-1 rounded">New</span>
                        </span>
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                        <span className="flex items-center gap-1">
                          Upload Date 
                          <span className="text-xs bg-blue-100 text-blue-800 px-1 rounded">UTC Hover</span>
                        </span>
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Duration</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Views</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Likes</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Comments</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Engagement %</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Time Gap</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {analysis.videos.map((video, index) => (
                      <tr key={video.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div className="flex items-center">
                            <img
                              src={video.thumbnail_url}
                              alt={video.title}
                              className="w-16 h-12 object-cover rounded mr-3"
                              onError={(e) => {
                                e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYwIiBoZWlnaHQ9IjEyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjY2NjIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk5vIEltYWdlPC90ZXh0Pjwvc3ZnPg==';
                              }}
                            />
                            <div>
                              <div className="text-sm font-medium text-gray-900 max-w-xs truncate">
                                {video.title}
                              </div>
                              <div className="text-sm text-gray-500">ID: {video.id}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="inline-block bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full font-medium">
                            {video.category}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          <div 
                            className="cursor-help" 
                            title={`UTC: ${video.upload_date_utc || video.upload_date}`}
                          >
                            <div className="font-medium">{video.upload_date_local}</div>
                            <div className="text-xs text-blue-600">
                              Hover for UTC ↗️
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">{video.duration}</td>
                        <td className="px-4 py-3 text-sm text-gray-900">{video.views.toLocaleString()}</td>
                        <td className="px-4 py-3 text-sm text-gray-900">{video.likes.toLocaleString()}</td>
                        <td className="px-4 py-3 text-sm text-gray-900">{video.comments.toLocaleString()}</td>
                        <td className="px-4 py-3 text-sm text-gray-900">{video.engagement_rate}%</td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {index === analysis.videos.length - 1 ? '-' : video.time_gap_text}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default YouTubeChannelAnalyzer;