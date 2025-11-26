# backend/tts_output.py
import os
import openai
from pathlib import Path
from tempfile import NamedTemporaryFile
import asyncio
from config import Config
from logger import setup_logger

logger = setup_logger("tts_output")

openai.api_key = Config.OPENAI_API_KEY

def speak(text: str, tone: str = "neutral") -> str:
    """Synchronous TTS generation"""
    try:
        # Standardize voice to "nova" but adjust speed based on tone
        voice = "nova"
        
        # Speed map based on emotion
        speed_map = {
            "sad": 0.85,
            "calm": 0.9,
            "neutral": 1.0,
            "happy": 1.1,
            "excited": 1.2,
            "angry": 1.15,
            "fear": 1.1
        }
        
        speed = speed_map.get(tone.lower(), 1.0)
        
        logger.info(f"Generating TTS with voice '{voice}' for tone '{tone}' (speed: {speed})")

        # Generate speech with correct model name
        response = openai.audio.speech.create(
            model=Config.TTS_MODEL,
            voice=voice,
            input=text,
            speed=speed
        )

        # Save temporary audio file
        audio_dir = Path(Config.AUDIO_DIR)
        audio_dir.mkdir(exist_ok=True)
        
        tmp_file = NamedTemporaryFile(
            delete=False, 
            suffix=".mp3",
            dir=audio_dir
        )
        tmp_file.write(response.read())
        tmp_file.close()

        logger.info(f"TTS audio saved: {tmp_file.name}")
        return f"audio/{Path(tmp_file.name).name}"
        
    except Exception as e:
        logger.error(f"TTS generation error: {e}")
        return None


async def speak_async(text: str, tone: str = "neutral") -> str:
    """Async TTS generation"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, speak, text, tone)


def cleanup_audio_file(file_path: str):
    """Delete audio file"""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up audio file: {file_path}")
    except Exception as e:
        logger.error(f"Audio cleanup error: {e}")

