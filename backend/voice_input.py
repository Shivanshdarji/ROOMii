import speech_recognition as sr
from transformers import pipeline

# Load sentiment analysis pipeline
sentiment_analyzer = pipeline("sentiment-analysis")

def analyze_sentiment(text):
    result = sentiment_analyzer(text)[0]
    return result['label'].lower()

def get_voice_sentiment(retry_count=0):
    recognizer = sr.Recognizer()

    # ✅ Step 1: Confirm mic access
    try:
        with sr.Microphone() as source:
            if retry_count == 0:
                print("🎙️ ROOMii is listening... Speak whenever you’re ready!")
            else:
                print("🔁 ROOMii: No worries, take your time — let's try again.")
            
            recognizer.adjust_for_ambient_noise(source, duration=1)  # better accuracy in noisy rooms

            # Listen with timeout & phrase limits
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            
            # Convert speech to text
            text = recognizer.recognize_google(audio)
            print(f"🗣️ You said: {text}")

            # Sentiment analysis
            sentiment = analyze_sentiment(text)
            return text, sentiment

    except sr.WaitTimeoutError:
        # Timeout — no voice detected
        if retry_count < 2:
            print("🤖 ROOMii: I didn’t catch that — maybe you’re thinking? Let’s try again.")
            return get_voice_sentiment(retry_count + 1)
        else:
            print("🫧 ROOMii: I’ll stay quiet for now. Speak when you’re ready.")
            return "no input", "neutral"

    except sr.UnknownValueError:
        print("🤖 ROOMii: Hmm, I couldn’t understand that clearly. Try again?")
        return get_voice_sentiment(retry_count + 1)

    except OSError:
        print("⚠️ ROOMii: I couldn’t access your microphone. Please check your mic settings and try again.")
        return "mic error", "neutral"

    except Exception as e:
        print(f"❌ ROOMii ran into an unexpected issue: {e}")
        return "error", "neutral"
