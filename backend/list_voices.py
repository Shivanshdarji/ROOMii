# list_voices.py
from elevenlabs import ElevenLabs
from dotenv import load_dotenv
import os

load_dotenv()
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

voices = client.voices.get_all()
for v in voices.voices:
    print(f"Name: {v.name} | ID: {v.voice_id}")
