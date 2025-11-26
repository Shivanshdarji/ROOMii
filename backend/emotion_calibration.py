"""
Personalized Emotion Calibration System
Allows users to calibrate emotion detection to their specific facial expressions
"""
import cv2
import numpy as np
from deepface import DeepFace
import json
import aiosqlite
from typing import List, Dict, Optional, Tuple
from logger import setup_logger
from config import Config

logger = setup_logger("emotion_calibration")

class EmotionCalibrator:
    """Manages personalized emotion calibration for users"""
    
    def __init__(self, db_path: str = "roomie_data.db"):
        self.db_path = db_path
    
    async def save_calibration_sample(self, user_id: int, emotion: str, frame_data: bytes) -> bool:
        """Save a calibration sample for a user"""
        try:
            # Decode frame
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Extract facial embedding using DeepFace
            embedding = DeepFace.represent(
                frame,
                model_name='Facenet',
                enforce_detection=False,
                detector_backend=Config.EMOTION_DETECTOR_BACKEND
            )
            
            if not embedding:
                logger.warning("No face detected in calibration sample")
                return False
            
            # Get the embedding vector
            embedding_vector = embedding[0]['embedding']
            embedding_json = json.dumps(embedding_vector)
            
            # Save to database
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO emotion_calibration (user_id, emotion, embedding) VALUES (?, ?, ?)",
                    (user_id, emotion, embedding_json)
                )
                await db.commit()
            
            logger.info(f"Saved calibration sample for user {user_id}, emotion: {emotion}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving calibration sample: {e}")
            return False
    
    async def get_user_calibration(self, user_id: int) -> Dict[str, List[List[float]]]:
        """Get all calibration data for a user"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT emotion, embedding FROM emotion_calibration WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    
                    calibration_data = {}
                    for row in rows:
                        emotion = row['emotion']
                        embedding = json.loads(row['embedding'])
                        
                        if emotion not in calibration_data:
                            calibration_data[emotion] = []
                        calibration_data[emotion].append(embedding)
                    
                    return calibration_data
        except Exception as e:
            logger.error(f"Error getting calibration data: {e}")
            return {}
    
    async def has_calibration(self, user_id: int) -> bool:
        """Check if user has calibration data"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT COUNT(*) FROM emotion_calibration WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return row[0] > 0
        except Exception as e:
            logger.error(f"Error checking calibration: {e}")
            return False
    
    async def clear_calibration(self, user_id: int):
        """Clear all calibration data for a user"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "DELETE FROM emotion_calibration WHERE user_id = ?",
                    (user_id,)
                )
                await db.commit()
            logger.info(f"Cleared calibration for user {user_id}")
        except Exception as e:
            logger.error(f"Error clearing calibration: {e}")
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    async def match_emotion(self, user_id: int, frame: np.ndarray) -> Tuple[Optional[str], float]:
        """Match current frame against user's calibrated emotions"""
        try:
            # Get user's calibration data
            calibration_data = await self.get_user_calibration(user_id)
            
            if not calibration_data:
                return None, 0.0
            
            # Extract embedding from current frame
            current_embedding = DeepFace.represent(
                frame,
                model_name='Facenet',
                enforce_detection=False,
                detector_backend=Config.EMOTION_DETECTOR_BACKEND
            )
            
            if not current_embedding:
                return None, 0.0
            
            current_vector = current_embedding[0]['embedding']
            
            # Compare against all calibrated emotions
            best_match = None
            best_similarity = 0.0
            
            for emotion, embeddings in calibration_data.items():
                # Calculate average similarity to all samples of this emotion
                similarities = [
                    self.cosine_similarity(current_vector, emb)
                    for emb in embeddings
                ]
                avg_similarity = np.mean(similarities)
                
                if avg_similarity > best_similarity:
                    best_similarity = avg_similarity
                    best_match = emotion
            
            # Only return match if similarity is high enough (>0.7)
            if best_similarity > 0.7:
                logger.info(f"Matched emotion: {best_match} (similarity: {best_similarity:.2f})")
                return best_match, best_similarity
            else:
                return None, best_similarity
                
        except Exception as e:
            logger.error(f"Error matching emotion: {e}")
            return None, 0.0

# Global instance
calibrator = EmotionCalibrator()
