from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from emotion_detector import get_cached_emotion, BackgroundEmotionMonitor
from main import get_roomie_response
from websocket_handler import init_socketio
from conversation_memory import memory
from config import Config
from logger import setup_logger
import os
import asyncio
import time
from pathlib import Path

logger = setup_logger("app")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize SocketIO
socketio = init_socketio(app)

# Initialize and start background emotion monitor immediately
emotion_monitor = BackgroundEmotionMonitor(interval=3.0)  # Check every 3 seconds
emotion_monitor.start()
logger.info("Background emotion monitor started")

# Initialize database and audio directory on startup
try:
    asyncio.run(memory.initialize())
    Path(Config.AUDIO_DIR).mkdir(exist_ok=True)
    logger.info("Database and audio directory initialized")
except Exception as e:
    logger.error(f"Initialization error: {e}")

@app.before_request
def before_first_request():
    """Mark app as initialized"""
    if not hasattr(app, 'initialized'):
        app.initialized = True
        logger.info("ROOMie backend ready")

@app.route("/")
def home():
    return jsonify({
        "message": "ROOMii backend v3.0 is running!",
        "version": "3.0",
        "features": [
            "WebSocket support",
            "Voice tone emotion detection",
            "Particle effects",
            "Analytics dashboard",
            "Voice commands"
        ]
    })

# REST API endpoints (fallbacks)
@app.route('/detect_emotion', methods=['GET'])
def detect_emotion():
    """Get current cached emotion"""
    try:
        emotion, confidence = get_cached_emotion()
        return jsonify({
            'emotion': emotion,
            'confidence': float(confidence)
        })
    except Exception as e:
        logger.error(f"Emotion detection error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_response', methods=['POST'])
def get_response():
    """Get AI response (REST fallback)"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        response = get_roomie_response(user_message)
        return jsonify(response)
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    """Serve audio files"""
    try:
        audio_dir = Path(Config.AUDIO_DIR)
        file_path = audio_dir / filename
        
        if not file_path.is_relative_to(audio_dir):
            return jsonify({'error': 'Invalid file path'}), 403
        
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, mimetype='audio/mpeg')
    except Exception as e:
        logger.error(f"Audio serving error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'emotion_monitor': emotion_monitor.is_alive() if emotion_monitor else False,
        'timestamp': time.time()
    })

if __name__ == '__main__':
    logger.info("ROOMie Backend v3.0 starting...")
    logger.info(f"Server: http://{Config.HOST}:{Config.PORT}")
    logger.info(f"WebSocket: ws://{Config.HOST}:{Config.PORT}")
    socketio.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        allow_unsafe_werkzeug=True
    )
