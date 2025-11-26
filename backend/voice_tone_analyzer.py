"""
Voice Tone Emotion Analyzer
Analyzes emotion from voice tone/audio features
"""
import numpy as np
from logger import setup_logger

logger = setup_logger("voice_tone")

def analyze_voice_tone(audio_data=None, text=""):
    """
    Analyze emotion from voice tone
    
    For now, uses text-based heuristics until we integrate audio analysis
    In future: use librosa for pitch, energy, tempo analysis
    """
    try:
        if not text:
            return "neutral", 0.3
        
        text_lower = text.lower()
        
        # Exclamation marks and caps indicate excitement/anger
        exclamation_count = text.count('!')
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        
        # Question marks indicate curiosity/confusion
        question_count = text.count('?')
        
        # Emotional keywords
        happy_words = ['happy', 'great', 'awesome', 'love', 'excited', 'wonderful', 'amazing', 'fantastic', 'yay', 'haha', 'lol']
        sad_words = ['sad', 'depressed', 'down', 'unhappy', 'terrible', 'awful', 'bad', 'upset', 'cry', 'hurt']
        angry_words = ['angry', 'mad', 'furious', 'hate', 'annoyed', 'frustrated', 'irritated', 'damn', 'stupid']
        fear_words = ['scared', 'afraid', 'worried', 'anxious', 'nervous', 'terrified', 'panic', 'fear']
        
        # Count emotional words
        happy_score = sum(1 for word in happy_words if word in text_lower)
        sad_score = sum(1 for word in sad_words if word in text_lower)
        angry_score = sum(1 for word in angry_words if word in text_lower)
        fear_score = sum(1 for word in fear_words if word in text_lower)
        
        # Adjust scores based on punctuation
        if exclamation_count > 0:
            if happy_score > 0:
                happy_score += exclamation_count * 0.5
            elif angry_score > 0:
                angry_score += exclamation_count * 0.5
            else:
                # Only slight boost if no emotional words present
                angry_score += exclamation_count * 0.2
        
        if caps_ratio > 0.3:  # More than 30% caps
            angry_score += 1.0
        
        # Determine dominant emotion
        scores = {
            'happy': happy_score,
            'sad': sad_score,
            'angry': angry_score,
            'fear': fear_score,
            'neutral': 0.5  # Lower base score
        }
        
        dominant_emotion = max(scores.items(), key=lambda x: x[1])
        emotion = dominant_emotion[0]
        
        # Calculate confidence
        total_score = sum(scores.values())
        # Lower base confidence for text-only analysis
        confidence = min(dominant_emotion[1] / max(total_score, 1), 0.8)
        
        # Boost confidence if there are clear indicators
        if exclamation_count > 1 or caps_ratio > 0.5:
            confidence = min(confidence + 0.1, 0.9)
        
        logger.info(f"Voice tone analysis: {emotion} (confidence: {confidence:.2f})")
        return emotion, confidence
    
    except Exception as e:
        logger.error(f"Voice tone analysis error: {e}")
        return "neutral", 0.3

def combine_emotions(face_emotion, face_conf, voice_emotion, voice_conf):
    """
    Combine face and voice emotions with weighted average
    Voice gets higher weight as it's more immediate
    """
    try:
        # Cast to float to avoid numpy types
        face_conf = float(face_conf)
        voice_conf = float(voice_conf)
        # Weight: 40% voice, 60% face (face is more reliable for now)
        voice_weight = 0.4
        face_weight = 0.6
        
        # If one has very low confidence, use the other
        if face_conf < 0.4:
            return voice_emotion, voice_conf
        if voice_conf < 0.4:
            return face_emotion, face_conf
        
        # If both agree, boost confidence
        if face_emotion == voice_emotion:
            combined_conf = min((face_conf * face_weight + voice_conf * voice_weight) * 1.2, 1.0)
            return face_emotion, combined_conf
        
        # If they disagree, use weighted confidence
        if voice_conf * voice_weight > face_conf * face_weight:
            return voice_emotion, voice_conf * voice_weight
        else:
            return face_emotion, face_conf * face_weight
    
    except Exception as e:
        logger.error(f"Emotion combination error: {e}")
        return face_emotion, face_conf
