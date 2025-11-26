# main.py
from emotion_detector import get_cached_emotion
from ai_core import generate_response
from tts_output import speak
from mood_manager import update_mood
from conversation_memory import memory
from config import Config
from logger import setup_logger

logger = setup_logger("main")

# 🎭 Personality Profiles
PERSONALITY_PROFILES = {
    "cheerful": {
        "name": "Kai",
        "style": "playful, witty, full of energy and warmth. Uses emojis and friendly tone.",
        "tone": "happy"
    },
    "low": {
        "name": "Luna",
        "style": "calm, empathetic, speaks softly and offers reassurance.",
        "tone": "sad"
    },
    "stressed": {
        "name": "Astra",
        "style": "soothing, gentle, guides through breathing and grounding.",
        "tone": "calm"
    },
    "angry": {
        "name": "Nova",
        "style": "balanced, composed, uses grounding statements to defuse anger.",
        "tone": "neutral"
    },
    "neutral": {
        "name": "Echo",
        "style": "friendly and clear, speaks naturally without strong emotion.",
        "tone": "neutral"
    }
}


def choose_personality(mood: str):
    """Return personality profile based on current mood."""
    mood = mood.lower()
    if mood in PERSONALITY_PROFILES:
        return PERSONALITY_PROFILES[mood]
    return PERSONALITY_PROFILES["neutral"]


def get_roomie_response(user_text: str):
    """
    ROOMii's full intelligent pipeline:
    - Get cached emotion (fast)
    - Select personality based on mood
    - Generate emotionally aligned AI response with conversation context
    - Speak in the personality's tone
    - Store conversation in memory
    """
    try:
        # Get cached emotion (no camera delay)
        emotion, confidence = get_cached_emotion()
        sentiment = "neutral"  # TODO: Add sentiment analysis from text

        # Update mood state
        mood_state, mood_changed = update_mood(emotion, sentiment)
        combined_mood = mood_state["combined_mood"]

        # Choose personality
        persona = choose_personality(combined_mood)
        name = persona["name"]
        style = persona["style"]
        tone = persona["tone"]

        logger.info(f"Emotion: {emotion} ({confidence:.2f}) | Mood: {combined_mood} | Personality: {name}")

        # Get conversation context from memory
        context = memory.get_context_for_ai(max_messages=Config.CONVERSATION_CONTEXT_LENGTH)

        # Build a personality-aware prompt for AI
        prompt = (
            f"You are ROOMii, a {style} AI companion named {name}. "
            f"The user currently seems {combined_mood} (emotion: {emotion}). "
            f"Respond in a way that matches {name}'s personality — warm, natural, and emotionally aware.\n\n"
            f"🧍User: {user_text}\n"
            f"🤖ROOMii:"
        )

        # Generate empathetic AI reply with context
        response = generate_response(
            user_text,
            emotion,
            sentiment,
            history=context,
            personality=combined_mood
        )

        # Generate tone-matched TTS
        audio_path = speak(response, tone=tone)

        logger.info(f"Response generated: {response[:50]}...")

        return response, audio_path
        
    except Exception as e:
        logger.error(f"Error in get_roomie_response: {e}")
        return "I'm having trouble right now. Can you try again?", None


def run_roomii_interactive():
    """Manual terminal test (optional)."""
    print("🎧 ROOMii is active — with Personality Engine 💫")
    try:
        while True:
            user_input = input("🧍You: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                print("👋 ROOMii: Goodbye, take care 🌙")
                break
            reply, _ = get_roomie_response(user_input)
            print(f"🤖ROOMii: {reply}")
    except KeyboardInterrupt:
        print("\n👋 ROOMii: See you soon 💫")

if __name__ == "__main__":
    print("🧠 ROOMii Standalone Mode Activated 💫")
    print("Type 'exit' to quit.\n")
    run_roomii_interactive()

