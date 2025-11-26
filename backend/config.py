"""
Configuration management for ROOMie backend
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Centralized configuration"""
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Server Settings
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # Emotion Detection
    EMOTION_CACHE_TTL = int(os.getenv("EMOTION_CACHE_TTL", 8))  # seconds
    EMOTION_DETECTOR_BACKEND = os.getenv("EMOTION_DETECTOR_BACKEND", "opencv")  # faster than retinaface
    EMOTION_CONFIDENCE_THRESHOLD = float(os.getenv("EMOTION_CONFIDENCE_THRESHOLD", 0.70))  # Increased for accuracy
    
    # AI Settings
    AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
    AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", 0.9))
    AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", 150))
    CONVERSATION_CONTEXT_LENGTH = int(os.getenv("CONVERSATION_CONTEXT_LENGTH", 50))
    
    # TTS Settings
    TTS_MODEL = os.getenv("TTS_MODEL", "tts-1")  # or "tts-1-hd" for higher quality
    TTS_SPEED = float(os.getenv("TTS_SPEED", 1.0))
    
    # Audio Settings
    AUDIO_CLEANUP_DELAY = int(os.getenv("AUDIO_CLEANUP_DELAY", 30))  # seconds
    AUDIO_DIR = os.getenv("AUDIO_DIR", "audio")
    
    # Database
    DB_PATH = os.getenv("DB_PATH", "roomie_data.db")
    
    # Performance
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", 5))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
    
    # Voice Map
    VOICE_MAP = {
        "happy": "alloy",
        "sad": "echo",
        "angry": "fable",
        "neutral": "nova",
        "calm": "shimmer",
        "cheerful": "alloy",
        "fear": "onyx",
        "surprise": "alloy"
    }
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required in .env file")
        return True

# Validate on import
Config.validate()
