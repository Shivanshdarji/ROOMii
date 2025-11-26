# ROOMie - Emotionally Intelligent AI Companion


![Python](https://img.shields.io/badge/python-3.10-blue.svg)
![React](https://img.shields.io/badge/react-18.0-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

**ROOMie** is an advanced conversational AI that detects your emotions through your webcam and voice tone, responding with empathy and a dynamic personality.

![Demo](https://via.placeholder.com/800x400?text=ROOMie+Demo+Screenshot)

## 🌟 Features

### 🧠 Emotional Intelligence
- **Real-time Face Analysis**: Uses DeepFace to detect 7+ emotions instantly.
- **Voice Tone Analyzer**: Detects emotional cues in your speech patterns.
- **Adaptive Personality**: The AI shifts between 5 personalities (e.g., *Kai* for happy, *Astra* for stressed) based on your mood.

### ⚡ Technical Innovation
- **WebSocket Streaming**: Sub-second latency for real-time conversation.
- **Async Architecture**: Non-blocking Flask backend with Gevent.
- **Memory System**: Remembers context across sessions using SQLite.
- **Glassmorphism UI**: Premium, modern React interface with Three.js avatars.

## 🚀 Quick Start

### Option A: Docker (Recommended)
The easiest way to run ROOMie is with Docker.

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/roomie.git
cd roomie

# 2. Add API Key
# Create a .env file in backend/ with your OpenAI Key
echo "OPENAI_API_KEY=sk-..." > backend/.env

# 3. Run
docker-compose up --build
```
Visit `http://localhost` to start!

### Option B: Manual Setup

#### Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```

#### Frontend
# ROOMie - Emotionally Intelligent AI Companion


![Python](https://img.shields.io/badge/python-3.10-blue.svg)
![React](https://img.shields.io/badge/react-18.0-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

**ROOMie** is an advanced conversational AI that detects your emotions through your webcam and voice tone, responding with empathy and a dynamic personality.

![Demo](https://via.placeholder.com/800x400?text=ROOMie+Demo+Screenshot)

## 🌟 Features

### 🧠 Emotional Intelligence
- **Real-time Face Analysis**: Uses DeepFace to detect 7+ emotions instantly.
- **Voice Tone Analyzer**: Detects emotional cues in your speech patterns.
- **Adaptive Personality**: The AI shifts between 5 personalities (e.g., *Kai* for happy, *Astra* for stressed) based on your mood.

### ⚡ Technical Innovation
- **WebSocket Streaming**: Sub-second latency for real-time conversation.
- **Async Architecture**: Non-blocking Flask backend with Gevent.
- **Memory System**: Remembers context across sessions using SQLite.
- **Glassmorphism UI**: Premium, modern React interface with Three.js avatars.

## 🚀 Quick Start

### Option A: Docker (Recommended)
The easiest way to run ROOMie is with Docker.

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/roomie.git
cd roomie

# 2. Add API Key
# Create a .env file in backend/ with your OpenAI Key
echo "OPENAI_API_KEY=sk-..." > backend/.env

# 3. Run
docker-compose up --build
```
Visit `http://localhost` to start!

### Option B: Manual Setup

#### Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 🤝 Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to submit a Pull Request.

## 🙏 Acknowledgments
- **OpenAI** for GPT-4o and TTS.
- **DeepFace** for computer vision.
- **Hack This Fall 2025** for the inspiration.
