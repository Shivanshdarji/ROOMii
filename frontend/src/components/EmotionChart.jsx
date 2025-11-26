// Emotion history chart component
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

const EMOTION_COLORS = {
    happy: '#10b981',
    sad: '#3b82f6',
    angry: '#ef4444',
    fear: '#8b5cf6',
    surprise: '#f59e0b',
    disgust: '#84cc16',
    neutral: '#6b7280'
};

export default function EmotionChart({ emotionHistory }) {
    if (!emotionHistory || emotionHistory.length === 0) {
        return (
            <div className="emotion-chart-empty">
                <p>No emotion data yet. Start talking to ROOMii!</p>
            </div>
        );
    }

    // Transform data for chart
    const chartData = emotionHistory.map((record, index) => ({
        time: index,
        emotion: record.emotion,
        confidence: (record.confidence * 100).toFixed(0),
        timestamp: new Date(record.timestamp).toLocaleTimeString()
    }));

    // Count emotions
    const emotionCounts = emotionHistory.reduce((acc, record) => {
        acc[record.emotion] = (acc[record.emotion] || 0) + 1;
        return acc;
    }, {});

    const dominantEmotion = Object.entries(emotionCounts)
        .sort(([, a], [, b]) => b - a)[0]?.[0] || 'neutral';

    return (
        <div className="emotion-chart-container">
            <div className="chart-header">
                <h4>Emotion Timeline</h4>
                <div className="dominant-emotion">
                    <span className="label">Dominant:</span>
                    <span className="emotion-badge" style={{ backgroundColor: EMOTION_COLORS[dominantEmotion] }}>
                        {dominantEmotion}
                    </span>
                </div>
            </div>

            <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={chartData}>
                    <defs>
                        <linearGradient id="emotionGradient" x1="0" y1="0" x2="0" y2="1">
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
                        dataKey="confidence"
                        stroke="#8b5cf6"
                        fillOpacity={1}
                        fill="url(#emotionGradient)"
                    />
                </AreaChart>
            </ResponsiveContainer>

            <div className="emotion-legend">
                {Object.entries(emotionCounts).map(([emotion, count]) => (
                    <div key={emotion} className="legend-item">
                        <span
                            className="legend-color"
                            style={{ backgroundColor: EMOTION_COLORS[emotion] }}
                        />
                        <span className="legend-text">{emotion}: {count}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
