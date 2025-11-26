from datetime import datetime

# Simple memory of last detected mood
current_mood_state = {
    "face_emotion": "neutral",
    "voice_sentiment": "neutral",
    "combined_mood": "neutral",
    "last_update": datetime.now()
}

def combine_moods(face_emotion, voice_sentiment):
    """
    Combine facial emotion + voice sentiment into one overall mood.
    """
    # Priority logic: negative emotions dominate
    if face_emotion in ["angry", "sad", "fear"] or voice_sentiment in ["negative", "sad"]:
        mood = "low"
    elif face_emotion in ["happy", "surprise"] or voice_sentiment in ["positive", "joy"]:
        mood = "cheerful"
    else:
        mood = "neutral"
    
    return mood

def update_mood(face_emotion, voice_sentiment):
    """
    Update ROOMii's mood state and detect changes.
    """
    global current_mood_state
    new_mood = combine_moods(face_emotion, voice_sentiment)
    
    changed = new_mood != current_mood_state["combined_mood"]
    if changed:
        print(f"🌈 ROOMii: I sense a mood shift — from {current_mood_state['combined_mood']} to {new_mood}.")
        current_mood_state.update({
            "face_emotion": face_emotion,
            "voice_sentiment": voice_sentiment,
            "combined_mood": new_mood,
            "last_update": datetime.now()
        })
    else:
        current_mood_state["last_update"] = datetime.now()
    
    return current_mood_state, changed
