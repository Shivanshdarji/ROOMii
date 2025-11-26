// Settings panel component
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function SettingsPanel({ isOpen, onClose, settings, onSettingsChange }) {
    const [localSettings, setLocalSettings] = useState(settings || {
        voice: 'nova',
        detectionSensitivity: 0.55,
        autoListen: true,
        showEmotionHistory: true,
        theme: 'dark'
    });

    const handleSave = () => {
        onSettingsChange(localSettings);
        onClose();
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    <motion.div
                        className="settings-overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                    />
                    <motion.div
                        className="settings-panel"
                        initial={{ x: '100%' }}
                        animate={{ x: 0 }}
                        exit={{ x: '100%' }}
                        transition={{ type: 'spring', damping: 25 }}
                    >
                        <div className="settings-header">
                            <h2>⚙️ Settings</h2>
                            <button className="close-btn" onClick={onClose}>✕</button>
                        </div>

                        <div className="settings-content">
                            {/* Voice Selection */}
                            <div className="setting-group">
                                <label>Voice</label>
                                <select
                                    value={localSettings.voice}
                                    onChange={(e) => setLocalSettings({ ...localSettings, voice: e.target.value })}
                                >
                                    <option value="alloy">Alloy (Neutral)</option>
                                    <option value="echo">Echo (Calm)</option>
                                    <option value="fable">Fable (Expressive)</option>
                                    <option value="onyx">Onyx (Deep)</option>
                                    <option value="nova">Nova (Warm)</option>
                                    <option value="shimmer">Shimmer (Soft)</option>
                                </select>
                            </div>

                            {/* Detection Sensitivity */}
                            <div className="setting-group">
                                <label>
                                    Emotion Detection Sensitivity
                                    <span className="value">{(localSettings.detectionSensitivity * 100).toFixed(0)}%</span>
                                </label>
                                <input
                                    type="range"
                                    min="0.3"
                                    max="0.9"
                                    step="0.05"
                                    value={localSettings.detectionSensitivity}
                                    onChange={(e) => setLocalSettings({ ...localSettings, detectionSensitivity: parseFloat(e.target.value) })}
                                />
                            </div>

                            {/* Auto Listen */}
                            <div className="setting-group toggle">
                                <label>Auto-listen for speech</label>
                                <input
                                    type="checkbox"
                                    checked={localSettings.autoListen}
                                    onChange={(e) => setLocalSettings({ ...localSettings, autoListen: e.target.checked })}
                                />
                            </div>

                            {/* Show Emotion History */}
                            <div className="setting-group toggle">
                                <label>Show emotion history</label>
                                <input
                                    type="checkbox"
                                    checked={localSettings.showEmotionHistory}
                                    onChange={(e) => setLocalSettings({ ...localSettings, showEmotionHistory: e.target.checked })}
                                />
                            </div>

                            {/* Theme */}
                            <div className="setting-group">
                                <label>Theme</label>
                                <select
                                    value={localSettings.theme}
                                    onChange={(e) => setLocalSettings({ ...localSettings, theme: e.target.value })}
                                >
                                    <option value="dark">Dark</option>
                                    <option value="light">Light</option>
                                    <option value="auto">Auto</option>
                                </select>
                            </div>

                            {/* Calibrate Emotions */}
                            <div className="setting-group" style={{ marginTop: '2rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '1rem' }}>
                                <label>Personalization</label>
                                <button
                                    className="btn accent"
                                    style={{ width: '100%' }}
                                    onClick={() => {
                                        onSettingsChange({ ...localSettings, startCalibration: true });
                                    }}
                                >
                                    Calibrate Emotions
                                </button>
                                <p style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)', marginTop: '0.5rem' }}>
                                    Teach ROOMie your unique facial expressions for better accuracy
                                </p>
                            </div>

                            {/* Clear Chat */}
                            <div className="setting-group" style={{ marginTop: '2rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '1rem' }}>
                                <label style={{ color: '#ff4444' }}>Danger Zone</label>
                                <button
                                    className="btn ghost"
                                    style={{ width: '100%', color: '#ff4444', borderColor: '#ff4444' }}
                                    onClick={() => {
                                        if (window.confirm("Are you sure you want to delete all chat history? This cannot be undone.")) {
                                            onSettingsChange({ ...localSettings, clearChat: true });
                                        }
                                    }}
                                >
                                    🗑️ Clear All Chat History
                                </button>
                            </div>
                        </div>

                        <div className="settings-footer">
                            <button className="btn ghost" onClick={onClose}>Cancel</button>
                            <button className="btn accent" onClick={handleSave}>Save Changes</button>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
