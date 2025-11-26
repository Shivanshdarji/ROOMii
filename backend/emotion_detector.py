import cv2
import numpy as np
from deepface import DeepFace
from collections import deque
import time
import asyncio
from threading import Thread, Lock
from config import Config
from logger import setup_logger

logger = setup_logger("emotion_detector")

# Smoothed rolling results
recent_emotions = deque(maxlen=8)
CONFIDENCE_THRESHOLD = Config.EMOTION_CONFIDENCE_THRESHOLD
EMOTION_PRIORITY = ['happy', 'surprise', 'neutral', 'sad', 'angry', 'fear', 'disgust']

# Caching mechanism
_emotion_cache = {
    "emotion": "neutral",
    "confidence": 0.0,
    "timestamp": 0
}
_cache_lock = Lock()

def detect_emotion_sync(user_id=None, bypass_cache=False):
    """Synchronous emotion detection with caching and optional personalization"""
    global _emotion_cache
    
    # Check cache (unless bypassing)
    if not bypass_cache:
        with _cache_lock:
            now = time.time()
            if now - _emotion_cache["timestamp"] < Config.EMOTION_CACHE_TTL:
                logger.debug(f"Using cached emotion: {_emotion_cache['emotion']}")
                return _emotion_cache["emotion"], _emotion_cache["confidence"]
    
    # Capture frame
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        logger.warning("Failed to capture frame from camera")
        return "neutral", 0.0
    
    # Try personalized calibration first if user_id provided
    if user_id:
        try:
            from emotion_calibration import calibrator
            has_calibration = asyncio.run(calibrator.has_calibration(user_id))
            
            if has_calibration:
                emotion, confidence = asyncio.run(calibrator.match_emotion(user_id, frame))
                
                if emotion and confidence > 0.7:
                    logger.info(f"Personalized match: {emotion} (confidence: {confidence:.2f})")
                    
                    # Update cache
                    with _cache_lock:
                        _emotion_cache = {
                            "emotion": emotion,
                            "confidence": confidence,
                            "timestamp": time.time()
                        }
                    
                    return emotion, confidence
                else:
                    logger.debug(f"Personalized match too weak ({confidence:.2f}), falling back to default")
        except Exception as e:
            logger.error(f"Calibration matching error: {e}, falling back to default")
    
    # Fall back to default DeepFace detection
    try:
        # Use faster detector backend (opencv instead of retinaface)
        result = DeepFace.analyze(
            frame,
            actions=['emotion'],
            enforce_detection=False,
            detector_backend=Config.EMOTION_DETECTOR_BACKEND,
            silent=True
        )
        
        emotion = result[0]['dominant_emotion']
        confidence = float(result[0]['emotion'][emotion]) / 100.0  # Normalize to 0-1
        all_emotions = result[0]['emotion']
        
        # Bias correction: If detecting fear/sad with low-medium confidence, check if neutral is close
        if emotion in ['fear', 'sad'] and confidence < 0.80:
            neutral_score = float(all_emotions.get('neutral', 0)) / 100.0
            happy_score = float(all_emotions.get('happy', 0)) / 100.0
            
            # If neutral or happy is within 15% of fear/sad, prefer neutral/happy
            if neutral_score > (confidence - 0.15):
                emotion = 'neutral'
                confidence = neutral_score
                logger.info(f"Bias correction: Switched from fear/sad to neutral (neutral score: {neutral_score:.2f})")
            elif happy_score > (confidence - 0.15):
                emotion = 'happy'
                confidence = happy_score
                logger.info(f"Bias correction: Switched from fear/sad to happy (happy score: {happy_score:.2f})")
        
        logger.info(f"Detected emotion: {emotion} (confidence: {confidence:.2f})")
        
    except Exception as e:
        logger.error(f"Emotion detection error: {e}")
        return "neutral", 0.0

    # Add to smoothing queue
    recent_emotions.append((emotion, confidence))

    # Weighted smoothing: Pick emotion with highest average confidence in recent frames
    emotion_scores = {}
    for emo, conf in recent_emotions:
        if emo not in emotion_scores:
            emotion_scores[emo] = []
        emotion_scores[emo].append(conf)
    
    # Calculate average confidence for each emotion
    stable_emotion = max(emotion_scores.items(), key=lambda x: sum(x[1]) / len(x[1]))[0]
    avg_confidence = sum(emotion_scores[stable_emotion]) / len(emotion_scores[stable_emotion])

    # If confidence is low, neutralize
    if avg_confidence < CONFIDENCE_THRESHOLD:
        stable_emotion = "neutral"
        logger.debug(f"Low average confidence ({avg_confidence:.2f}), using neutral")

    # Update cache
    with _cache_lock:
        _emotion_cache = {
            "emotion": stable_emotion,
            "confidence": avg_confidence,
            "timestamp": time.time()
        }

    return stable_emotion, avg_confidence


async def detect_emotion():
    """Async wrapper for emotion detection"""
    loop = asyncio.get_event_loop()
    emotion, confidence = await loop.run_in_executor(None, detect_emotion_sync)
    return emotion, confidence


def get_cached_emotion():
    """Get current emotion from cache without triggering detection"""
    with _cache_lock:
        return _emotion_cache["emotion"], _emotion_cache["confidence"]


class BackgroundEmotionMonitor:
    """Background thread for continuous emotion monitoring"""
    
    def __init__(self, interval=5.0, user_id=None):
        self.interval = interval
        self.user_id = user_id
        self.running = False
        self.thread = None
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Detect emotion with user_id for personalization
                detect_emotion_sync(user_id=self.user_id, bypass_cache=True)
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Background monitoring error: {e}")
                time.sleep(self.interval)
    
    def start(self):
        """Start background monitoring"""
        if not self.running:
            self.running = True
            self.thread = Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            logger.info("Background emotion monitoring started")
    
    def stop(self):
        """Stop background monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("Background emotion monitoring stopped")



def live_emotion_detector():
    """Live demo with overlay + stabilized detection"""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not found.")
        return

    print("🎥 Live Emotion Detection started. Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        try:
            result = DeepFace.analyze(
                frame,
                actions=['emotion'],
                enforce_detection=False,
                detector_backend=Config.EMOTION_DETECTOR_BACKEND,
                silent=True
            )
            emotion = result[0]['dominant_emotion']
            confidence = result[0]['emotion'][emotion]

            recent_emotions.append(emotion)
            stable_emotion = max(set(recent_emotions), key=recent_emotions.count)

            if confidence < CONFIDENCE_THRESHOLD * 100:
                stable_emotion = "neutral"

            cv2.putText(frame, f"{stable_emotion.upper()} ({confidence:.2f})",
                        (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 255, 0), 2, cv2.LINE_AA)

        except Exception:
            cv2.putText(frame, "No face detected", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        cv2.imshow("ROOMii - Emotion Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    live_emotion_detector()
