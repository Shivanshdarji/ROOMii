// Emotion Calibration Wizard Component
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const EMOTIONS = [
    { name: 'happy', instruction: 'Show your biggest smile! 😊', icon: 'H+' },
    { name: 'neutral', instruction: 'Relax your face, no expression', icon: 'N=' },
    { name: 'sad', instruction: 'Show a sad face', icon: 'S−' },
    { name: 'angry', instruction: 'Show an angry expression', icon: 'A!' },
    { name: 'surprised', instruction: 'Show surprise!', icon: 'S*' },
];

export default function EmotionCalibration({ socket, isOpen, onClose }) {
    const [currentStep, setCurrentStep] = useState(0);
    const [samplesCollected, setSamplesCollected] = useState(0);
    const [isCapturing, setIsCapturing] = useState(false);
    const [calibrationComplete, setCalibrationComplete] = useState(false);
    const videoRef = useRef(null);
    const streamRef = useRef(null);

    const SAMPLES_PER_EMOTION = 3;

    useEffect(() => {
        if (isOpen) {
            startCamera();

            // Listen for calibration events
            socket.on('calibration_sample_saved', handleSampleSaved);

            return () => {
                stopCamera();
                socket.off('calibration_sample_saved');
            };
        }
    }, [isOpen]);

    const startCamera = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                streamRef.current = stream;
            }
        } catch (error) {
            console.error('Error accessing camera:', error);
            alert('Please allow camera access for calibration');
        }
    };

    const stopCamera = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
        }
    };

    const captureFrame = () => {
        if (!videoRef.current) return null;

        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoRef.current, 0, 0);

        return canvas.toDataURL('image/jpeg', 0.8);
    };

    const handleCapture = () => {
        setIsCapturing(true);

        const frameData = captureFrame();
        if (!frameData) {
            setIsCapturing(false);
            return;
        }

        // Remove data:image/jpeg;base64, prefix
        const base64Data = frameData.split(',')[1];

        const currentEmotion = EMOTIONS[currentStep].name;

        socket.emit('save_calibration_sample', {
            emotion: currentEmotion,
            frame_data: base64Data
        });
    };

    const handleSampleSaved = () => {
        setIsCapturing(false);

        setSamplesCollected(prev => {
            const newCount = prev + 1;

            // Check if we've collected enough samples for this emotion
            if (newCount >= SAMPLES_PER_EMOTION) {
                // Move to next emotion
                if (currentStep < EMOTIONS.length - 1) {
                    setTimeout(() => {
                        setCurrentStep(s => s + 1);
                        setSamplesCollected(0);
                    }, 500);
                } else {
                    // Calibration complete!
                    setTimeout(() => {
                        setCalibrationComplete(true);
                    }, 500);
                }
            }

            return newCount;
        });
    };

    const handleClose = () => {
        stopCamera();
        onClose();
        // Reset state
        setCurrentStep(0);
        setSamplesCollected(0);
        setCalibrationComplete(false);
    };

    const currentEmotion = EMOTIONS[currentStep];
    const progress = ((currentStep * SAMPLES_PER_EMOTION + samplesCollected) / (EMOTIONS.length * SAMPLES_PER_EMOTION)) * 100;

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    <motion.div
                        key="overlay"
                        className="calibration-overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={handleClose}
                    />
                    <motion.div
                        key="modal"
                        className="calibration-modal"
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.9, opacity: 0 }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        {!calibrationComplete ? (
                            <>
                                <div className="calibration-header">
                                    <h2>Emotion Calibration</h2>
                                    <button className="close-btn" onClick={handleClose}>✕</button>
                                </div>

                                <div className="calibration-progress">
                                    <div className="progress-bar">
                                        <div className="progress-fill" style={{ width: `${progress}%` }} />
                                    </div>
                                    <div className="progress-text">
                                        {currentStep + 1} / {EMOTIONS.length} emotions
                                    </div>
                                </div>

                                <div className="calibration-content">
                                    <div className="emotion-icon" style={{ fontSize: '3rem', marginBottom: '1rem' }}>
                                        {currentEmotion.icon}
                                    </div>
                                    <h3>{currentEmotion.name.toUpperCase()}</h3>
                                    <p className="instruction">{currentEmotion.instruction}</p>

                                    <div className="video-container">
                                        <video
                                            ref={videoRef}
                                            autoPlay
                                            playsInline
                                            muted
                                            style={{
                                                width: '100%',
                                                maxWidth: '400px',
                                                borderRadius: '12px',
                                                transform: 'scaleX(-1)' // Mirror effect
                                            }}
                                        />
                                    </div>

                                    <div className="samples-indicator">
                                        {Array.from({ length: SAMPLES_PER_EMOTION }).map((_, i) => (
                                            <div
                                                key={i}
                                                className={`sample-dot ${i < samplesCollected ? 'collected' : ''}`}
                                            />
                                        ))}
                                    </div>

                                    <button
                                        className="btn accent large"
                                        onClick={handleCapture}
                                        disabled={isCapturing}
                                        style={{ marginTop: '1rem', minWidth: '200px' }}
                                    >
                                        {isCapturing ? 'Capturing...' : `Capture (${samplesCollected}/${SAMPLES_PER_EMOTION})`}
                                    </button>
                                </div>
                            </>
                        ) : (
                            <div className="calibration-complete">
                                <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>✓</div>
                                <h2>Calibration Complete!</h2>
                                <p>ROOMie has learned your unique facial expressions.</p>
                                <p>Emotion detection will now be personalized to you.</p>
                                <button className="btn accent large" onClick={handleClose} style={{ marginTop: '2rem' }}>
                                    Done
                                </button>
                            </div>
                        )}
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
