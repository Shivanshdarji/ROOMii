import cv2
from deepface import DeepFace
import threading

# 🧠 Persistent camera object
camera = cv2.VideoCapture(0)
camera_lock = threading.Lock()  # ensure thread safety

def detect_emotion():
    """
    Keeps the camera open persistently for emotion detection.
    Returns one of ['happy', 'sad', 'angry', 'neutral', 'surprise', 'fear', etc.]
    """
    global camera

    with camera_lock:  # prevent simultaneous camera access
        if not camera.isOpened():
            camera.open(0)

        ret, frame = camera.read()
        if not ret or frame is None:
            print("⚠️ Camera frame not captured properly.")
            return "neutral"

        try:
            result = DeepFace.analyze(
                frame, 
                actions=['emotion'], 
                enforce_detection=False
            )
            emotion = result[0].get('dominant_emotion', 'neutral')
            print(f"🪞 Detected emotion: {emotion}")
            return emotion

        except Exception as e:
            print(f"⚠️ Detection error: {e}")
            return "neutral"
