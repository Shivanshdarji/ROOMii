// Advanced Analytics Dashboard for ROOMie
// Beautiful insights and visualizations
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, Line, AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const EMOTION_COLORS = {
    happy: '#10b981',
    sad: '#3b82f6',
    angry: '#ef4444',
    fear: '#8b5cf6',
    surprise: '#f59e0b',
    disgust: '#84cc16',
    neutral: '#6b7280',
    calm: '#06b6d4'
};

export default function AnalyticsDashboard({ socket, isOpen, onClose }) {
    const [analyticsData, setAnalyticsData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [selectedPeriod, setSelectedPeriod] = useState(7);

    useEffect(() => {
        if (isOpen && socket) {
            fetchAnalytics();

            // Listen for analytics data
            socket.on('analytics_data', (data) => {
                setAnalyticsData(data);
                setLoading(false);
            });

            return () => {
                socket.off('analytics_data');
            };
        }
    }, [isOpen, socket, selectedPeriod]);

    const fetchAnalytics = () => {
        setLoading(true);
        socket.emit('get_analytics', { days: selectedPeriod });
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                className="analytics-overlay"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={onClose}
            />
            <motion.div
                className="analytics-dashboard"
                initial={{ x: '100%' }}
                animate={{ x: 0 }}
                exit={{ x: '100%' }}
                transition={{ type: 'spring', damping: 25 }}
            >
                <div className="analytics-header">
                    <h2>Analytics Dashboard</h2>
                    <div className="header-controls">
                        <select
                            value={selectedPeriod}
                            onChange={(e) => setSelectedPeriod(Number(e.target.value))}
                            className="period-selector"
                        >
                            <option value={7}>Last 7 days</option>
                            <option value={14}>Last 14 days</option>
                            <option value={30}>Last 30 days</option>
                        </select>
                        <button className="close-btn" onClick={onClose}>✕</button>
                    </div>
                </div>

                <div className="analytics-content">
                    {loading ? (
                        <div className="loading-state">
                            <div className="spinner"></div>
                            <p>Loading analytics...</p>
                        </div>
                    ) : analyticsData ? (
                        <>
                            {/* Overview Cards */}
                            <div className="overview-cards">
                                <div className="stat-card">
                                    <div className="stat-icon" style={{ fontSize: '1.5rem', fontWeight: '300' }}>↑</div>
                                    <div className="stat-content">
                                        <div className="stat-label">Mood Score</div>
                                        <div className="stat-value">{analyticsData.summary?.mood_score || 0}/100</div>
                                    </div>
                                </div>

                                <div className="stat-card">
                                    <div className="stat-icon" style={{ fontSize: '1.2rem', fontWeight: '600' }}>
                                        {analyticsData.summary?.dominant_emotion &&
                                            getEmotionIcon(analyticsData.summary.dominant_emotion)}
                                    </div>
                                    <div className="stat-content">
                                        <div className="stat-label">Dominant Emotion</div>
                                        <div className="stat-value">
                                            {analyticsData.summary?.dominant_emotion || 'neutral'}
                                        </div>
                                    </div>
                                </div>

                                <div className="stat-card">
                                    <div className="stat-icon" style={{ fontSize: '1.5rem', fontWeight: '300' }}>∞</div>
                                    <div className="stat-content">
                                        <div className="stat-label">Total Records</div>
                                        <div className="stat-value">{analyticsData.summary?.total_records || 0}</div>
                                    </div>
                                </div>
                            </div>

                            {/* Insights */}
                            {analyticsData.insights && analyticsData.insights.length > 0 && (
                                <div className="insights-section">
                                    <h3>Insights</h3>
                                    <div className="insights-grid">
                                        {analyticsData.insights.map((insight, i) => (
                                            <motion.div
                                                key={i}
                                                className={`insight-card ${insight.severity}`}
                                                initial={{ opacity: 0, y: 20 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ delay: i * 0.1 }}
                                            >
                                                <div className="insight-icon">{insight.icon}</div>
                                                <div className="insight-content">
                                                    <div className="insight-title">{insight.title}</div>
                                                    <div className="insight-description">{insight.description}</div>
                                                </div>
                                            </motion.div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Emotion Distribution */}
                            {analyticsData.summary?.emotion_distribution && (
                                <div className="chart-section">
                                    <h3>Emotion Distribution</h3>
                                    <ResponsiveContainer width="100%" height={300}>
                                        <PieChart>
                                            <Pie
                                                data={Object.entries(analyticsData.summary.emotion_distribution).map(([emotion, count]) => ({
                                                    name: emotion,
                                                    value: count
                                                }))}
                                                cx="50%"
                                                cy="50%"
                                                labelLine={false}
                                                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                                outerRadius={100}
                                                fill="#8884d8"
                                                dataKey="value"
                                            >
                                                {Object.keys(analyticsData.summary.emotion_distribution).map((emotion, index) => (
                                                    <Cell key={`cell-${index}`} fill={EMOTION_COLORS[emotion] || '#6b7280'} />
                                                ))}
                                            </Pie>
                                            <Tooltip />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                            )}

                            {/* Mood Trends */}
                            {analyticsData.trends && analyticsData.trends.length > 0 && (
                                <div className="chart-section">
                                    <h3>Mood Trends</h3>
                                    <ResponsiveContainer width="100%" height={250}>
                                        <AreaChart data={analyticsData.trends}>
                                            <defs>
                                                <linearGradient id="moodGradient" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                                                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                                            <XAxis
                                                dataKey="timestamp"
                                                stroke="rgba(255,255,255,0.5)"
                                                tick={{ fontSize: 10 }}
                                            />
                                            <YAxis
                                                stroke="rgba(255,255,255,0.5)"
                                                tick={{ fontSize: 10 }}
                                            />
                                            <Tooltip
                                                contentStyle={{
                                                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                                    border: '1px solid rgba(255,255,255,0.2)',
                                                    borderRadius: '8px'
                                                }}
                                            />
                                            <Area
                                                type="monotone"
                                                dataKey="mood_score"
                                                stroke="#8b5cf6"
                                                fillOpacity={1}
                                                fill="url(#moodGradient)"
                                            />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>
                            )}

                            {/* Mood Calendar */}
                            {analyticsData.calendar && analyticsData.calendar.length > 0 && (
                                <div className="chart-section">
                                    <h3>Calendar</h3>
                                    <div className="calendar-grid">
                                        {analyticsData.calendar.slice(-30).map((day, i) => (
                                            <div
                                                key={i}
                                                className="calendar-day"
                                                style={{
                                                    backgroundColor: EMOTION_COLORS[day.dominant_emotion] || '#6b7280',
                                                    opacity: 0.3 + (day.intensity * 0.7)
                                                }}
                                                title={`${day.date}: ${day.dominant_emotion} (${day.count} records)`}
                                            >
                                                <div className="day-number">{new Date(day.date).getDate()}</div>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="calendar-legend">
                                        <span>Less activity</span>
                                        <div className="legend-gradient"></div>
                                        <span>More activity</span>
                                    </div>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="empty-state">
                            <p>No analytics data available yet. Start chatting with ROOMie!</p>
                        </div>
                    )}
                </div>
            </motion.div>
        </AnimatePresence>
    );
}

function getEmotionIcon(emotion) {
    const iconMap = {
        happy: 'H+',
        sad: 'S−',
        angry: 'A!',
        fear: 'F?',
        surprise: 'S*',
        disgust: 'D~',
        neutral: 'N=',
        calm: 'C·'
    };
    return iconMap[emotion] || 'N=';
}
