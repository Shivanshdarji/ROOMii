// src/App.jsx - ROOMie v3.0 with Voice Commands, Particles, and Analytics
import React, { useState, useRef, useEffect, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, useGLTF, Html } from "@react-three/drei";
import { motion, AnimatePresence } from "framer-motion";
import * as THREE from "three";
import { io } from "socket.io-client";
import StreamingText from "./components/StreamingText";
import EmotionChart from "./components/EmotionChart";
import SettingsPanel from "./components/SettingsPanel";
import ParticleSystem from "./components/ParticleSystem";
import AnalyticsDashboard from "./components/AnalyticsDashboard";
import EmotionCalibration from "./components/EmotionCalibration";
import "./styles/globals.css";

/* 🤖 ROOMii 3D Model */
function RoomiiModel({ mood = "idle", isSpeaking = false, emotionStrength = 0.5 }) {
  const group = useRef();
  const { scene, animations } = useGLTF("/models/roomii_bot.glb");
  const mixer = useRef();
  const currentAction = useRef(null);
  const time = useRef(0);
  const head = useRef();
  const glow = useRef();

  const moodAnimations = {
    idle: 0, happy: 1, sad: 2, wave: 3, angry: 4, surprise: 5,
  };

  useEffect(() => {
    if (!animations?.length || !scene) return;
    mixer.current = new THREE.AnimationMixer(scene);
    const index = moodAnimations[mood] ?? 0;
    const clip = animations[index];
    if (!clip) return;

    const action = mixer.current.clipAction(clip);
    if (currentAction.current) currentAction.current.fadeOut(0.4);
    action.reset().fadeIn(0.4).play();
    currentAction.current = action;
  }, [animations, mood, scene]);

  const moodColors = {
    idle: 0xaaaaaa, happy: 0x88ff88, calm: 0x88ccff,
    sad: 0x6699ff, angry: 0xff4444, dancing: 0xffbb33, surprise: 0xffff88,
  };

  useEffect(() => {
    if (!group.current || !scene) return;
    if (!group.current.children.includes(scene)) {
      group.current.add(scene);
      // Rotate -90 degrees to face screen (-Math.PI / 2)
      group.current.rotation.y = -Math.PI / 2;
      // Increase scale (1.4)
      group.current.scale.set(1.4, 1.4, 1.4);
      // Move down (-0.8)
      group.current.position.set(0, -0.8, 0);

      const glowGeometry = new THREE.SphereGeometry(0.15, 32, 32);
      const glowMaterial = new THREE.MeshBasicMaterial({
        color: 0xffffcc, transparent: true, opacity: 0.7,
      });
      const glowMesh = new THREE.Mesh(glowGeometry, glowMaterial);
      glowMesh.position.set(0, 0.45, 0.9);
      glow.current = glowMesh;
      scene.add(glowMesh);

      head.current = scene.getObjectByName("Head") || scene;
    }
  }, [scene]);

  // Dynamic Lighting Colors based on mood
  const lightingColors = {
    idle: { ambient: "#ffffff", directional: "#ffffff", background: "#1a1a1a" },
    happy: { ambient: "#ffcc00", directional: "#ffaa00", background: "#2a2a1a" },
    sad: { ambient: "#336699", directional: "#004488", background: "#0a1a2a" },
    angry: { ambient: "#ff3333", directional: "#cc0000", background: "#2a0a0a" },
    surprise: { ambient: "#ff00ff", directional: "#aa00aa", background: "#2a0a2a" },
    calm: { ambient: "#33cc99", directional: "#008866", background: "#0a2a1a" },
  };

  const currentLight = lightingColors[mood] || lightingColors.idle;

  useFrame((_, delta) => {
    if (!group.current) return;
    mixer.current?.update(delta);
    time.current += delta * 0.6;

    // Procedural Animation: Squash and Stretch
    const pulse = 1 + Math.sin(time.current * 2) * 0.02;
    let scaleY = 0.9 * pulse;
    let scaleXZ = 0.9 * pulse;

    if (isSpeaking) {
      // Squash and stretch when speaking
      const speechPulse = Math.sin(time.current * 15) * 0.05;
      scaleY += speechPulse;
      scaleXZ -= speechPulse * 0.5; // Preserve volume
    }

    group.current.scale.set(scaleXZ, scaleY, scaleXZ);

    // Mood-based idle motions
    const amplitude = ["sad", "calm"].includes(mood) ? 0.015 : 0.03;
    let yMotion = Math.sin(time.current) * (amplitude + emotionStrength * 0.01);

    if (mood === 'angry') {
      yMotion += Math.sin(time.current * 20) * 0.005; // Shaking
    }

    group.current.position.y = -0.8 + yMotion;

    if (head.current) {
      const tilt = isSpeaking ? Math.sin(time.current * 8) * 0.08 : Math.sin(time.current) * 0.04;
      head.current.rotation.y = tilt;

      if (mood === "happy" || mood === "dancing") {
        head.current.rotation.z = Math.sin(time.current * 3) * 0.05;
      } else if (mood === "angry") {
        head.current.rotation.z = Math.sin(time.current * 10) * 0.07;
      } else if (mood === "sad") {
        head.current.rotation.x = 0.15 + Math.sin(time.current * 0.5) * 0.03;
      } else {
        head.current.rotation.x = Math.sin(time.current * 0.3) * 0.03;
      }
    }

    if (glow.current) {
      const color = new THREE.Color(moodColors[mood] || 0xffffff);
      glow.current.material.color.lerp(color, 0.1);
      glow.current.material.opacity = 0.6 + Math.sin(time.current * 3) * 0.2;
    }
  });

  return (
    <group ref={group}>
      <ambientLight intensity={0.5} color={currentLight.ambient} />
      <directionalLight position={[2, 2, 4]} intensity={1.0} color={currentLight.directional} />
    </group>
  );
}

/* 💬 MAIN APP */
export default function App() {
  const [mood, setMood] = useState("idle");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [messages, setMessages] = useState([]);
  const [micGranted, setMicGranted] = useState(false);
  const [userMessage, setUserMessage] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [emotionHistory, setEmotionHistory] = useState([]);
  const [showSettings, setShowSettings] = useState(false);
  const [showEmotionChart, setShowEmotionChart] = useState(false);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [showCalibration, setShowCalibration] = useState(false);
  const [commandToast, setCommandToast] = useState(null);
  const [settings, setSettings] = useState({
    voice: 'nova',
    detectionSensitivity: 0.55,
    autoListen: true,
    showEmotionHistory: true,
    theme: 'dark'
  });
  const [currentPersonality, setCurrentPersonality] = useState("Echo");
  const [isConnected, setIsConnected] = useState(false);
  const [isListening, setIsListening] = useState(false);

  const [username, setUsername] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginInput, setLoginInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [isSignup, setIsSignup] = useState(false);
  const [authError, setAuthError] = useState("");

  const audioRef = useRef(null);
  const recognitionRef = useRef(null);
  const socketRef = useRef(null);
  const chatEndRef = useRef(null);
  const usernameRef = useRef("");

  /* 🔌 WebSocket Connection */
  useEffect(() => {
    const socket = io("http://127.0.0.1:5000", {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('✅ Connected to ROOMie backend');
      setIsConnected(true);

      // Auto-restore session
      const storedUser = localStorage.getItem('roomie_user');
      if (storedUser) {
        const { user_id, username } = JSON.parse(storedUser);
        socket.emit('restore_session', { user_id, username });
      }
    });

    socket.on('disconnect', () => {
      console.log('❌ Disconnected from backend');
      setIsConnected(false);
    });

    socket.on('login_success', (data) => {
      console.log('✅ Login successful:', data);
      setIsLoggedIn(true);
      setUsername(data.username);
      usernameRef.current = data.username;
      setAuthError("");

      // Save session
      localStorage.setItem('roomie_user', JSON.stringify({
        user_id: data.user_id,
        username: data.username
      }));
    });

    socket.on('auth_error', (data) => {
      setAuthError(data.message);
    });

    socket.on('conversation_history', (data) => {
      if (data.history) {
        // Transform history to message format
        const historyMessages = data.history.reverse().flatMap(item => [
          { sender: "user", text: item.user_message },
          { sender: "bot", text: item.bot_response, personality: item.personality }
        ]);
        setMessages(historyMessages);
      }
    });

    socket.on('emotion_update', (data) => {
      if (data.emotion) {
        setMood(data.emotion.toLowerCase());
        setEmotionHistory(prev => [...prev, {
          emotion: data.emotion,
          confidence: data.confidence || 0,
          timestamp: new Date().toISOString()
        }].slice(-50));
      }
    });

    socket.on('history_cleared', () => {
      setMessages([]);
      setEmotionHistory([]);
      alert("Chat history cleared!");
    });

    socket.on('message_response', (data) => {
      setMessages(prev => [...prev, {
        sender: "bot",
        text: data.text,
        personality: data.personality
      }]);
      setCurrentPersonality(data.personality || "Echo");
      setIsProcessing(false);
    });

    socket.on('audio_ready', (data) => {
      if (data.audio_url) {
        // Stop listening immediately to prevent echo
        recognitionRef.current?.abort();
        setIsSpeaking(true);

        const audio = new Audio(`http://127.0.0.1:5000${data.audio_url}`);
        audioRef.current = audio;
        audio.play().catch(console.error);
        audio.onended = () => {
          setIsSpeaking(false);
        };
      } else {
        setIsSpeaking(false);
      }
    });

    socket.on('error', (data) => {
      console.error('Backend error:', data.message);
      if (data.message === 'User not logged in') {
        setIsLoggedIn(false);
        localStorage.removeItem('roomie_user'); // Clear invalid session
      } else {
        setMessages(prev => [...prev, { sender: "error", text: data.message }]);
        setIsProcessing(false);
        setIsSpeaking(false);
      }
    });

    // Request emotion updates periodically
    const emotionInterval = setInterval(() => {
      if (socket.connected && isLoggedIn) {
        socket.emit('get_emotion');
      }
    }, 5000);

    return () => {
      clearInterval(emotionInterval);
      socket.disconnect();
    };
  }, [isLoggedIn]);

  /* 🔐 Access */
  const requestAccess = async () => {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
      setMicGranted(true);
    } catch {
      alert("Please allow microphone and camera access for ROOMii.");
    }
  };

  const handleAuth = (e) => {
    e.preventDefault();
    if (!loginInput.trim() || !passwordInput.trim()) return;

    if (socketRef.current) {
      const event = isSignup ? 'auth_signup' : 'auth_login';
      socketRef.current.emit(event, {
        username: loginInput.trim(),
        password: passwordInput.trim()
      });
    }
  };

  /* Auto scroll */
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  /* ⛔ Stop */
  const handleStop = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    recognitionRef.current?.abort();
    setIsSpeaking(false);
    setIsProcessing(false);

    // Notify backend to stop generating/sending
    if (socketRef.current) {
      socketRef.current.emit('stop_response');
    }
  };

  /* 🎤 Speech Recognition with Silence Detection */
  useEffect(() => {
    if (!micGranted || !settings.autoListen || !isLoggedIn) return;

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      alert("Speech recognition not supported.");
      return;
    }

    const recognition = new SR();
    recognition.lang = "en-US";
    recognition.interimResults = true;  // Show what's being captured
    recognition.continuous = true;      // Keep listening
    recognition.maxAlternatives = 1;

    let silenceTimer = null;
    let finalTranscript = '';
    let isActive = false;

    const startListening = () => {
      // Don't listen if we are speaking (echo cancellation) or processing
      if (!isProcessing && !isSpeaking && !isActive) {
        try {
          finalTranscript = '';
          recognition.start();
          isActive = true;
        } catch (e) {
          console.log("Recognition start error:", e);
        }
      }
    };

    recognition.onresult = (event) => {
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }

      // Clear existing silence timer
      if (silenceTimer) {
        clearTimeout(silenceTimer);
      }

      // Set new silence timer (1.5 seconds of silence = end of speech)
      silenceTimer = setTimeout(() => {
        const fullText = (finalTranscript + interimTranscript).trim();
        if (fullText.length > 2) {
          console.log("Final speech:", fullText);
          recognition.stop();
          isActive = false;

          // Interruption: If speaking/processing, stop everything
          if (isProcessing || isSpeaking) {
            handleStop();
          }

          handleMessage(fullText);
          finalTranscript = '';
        }
      }, 1500);
    };

    recognition.onend = () => {
      setIsListening(false);
      isActive = false;
      if (silenceTimer) {
        clearTimeout(silenceTimer);
      }

      // Restart after delay if auto-listen is on
      if (settings.autoListen) {
        setTimeout(() => {
          if (!isProcessing && !isSpeaking) {
            startListening();
          }
        }, 1000);
      }
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      isActive = false;
      if (event.error !== 'no-speech' && event.error !== 'aborted') {
        setIsListening(false);
      }
    };

    recognition.onstart = () => {
      setIsListening(true);
      isActive = true;
    };

    recognitionRef.current = recognition;
    startListening();

    return () => {
      if (silenceTimer) clearTimeout(silenceTimer);
      try {
        recognition.stop();
      } catch (e) { }
    };
  }, [micGranted, isProcessing, isSpeaking, settings.autoListen, isLoggedIn]);

  /* 🛑 Auto-Listen Toggle Effect */
  useEffect(() => {
    if (!settings.autoListen) {
      recognitionRef.current?.abort();
      setIsListening(false);
    }
  }, [settings.autoListen]);


  /* 💬 Handle Message (Debounced) */
  const lastMessageTime = useRef(0);

  const handleMessage = async (text) => {
    if (!socketRef.current || !socketRef.current.connected) {
      alert("Not connected to backend. Please refresh.");
      return;
    }

    // Strict self-listening check
    if (isSpeaking) {
      console.log("Ignored input while speaking:", text);
      return;
    }

    // Debounce: Ignore if called within 1 second of last message
    const now = Date.now();
    if (now - lastMessageTime.current < 1000) {
      console.log("Ignored duplicate/rapid message:", text);
      return;
    }
    lastMessageTime.current = now;

    // Stop any previous response before sending new one
    socketRef.current.emit('stop_response');

    setMessages(prev => [...prev, { sender: "user", text }]);
    setIsProcessing(true);
    // Don't set isSpeaking=true here, wait for audio_ready

    socketRef.current.emit('send_message', { message: text });
  };

  const handleSend = () => {
    if (userMessage.trim()) {
      recognitionRef.current?.abort();
      handleMessage(userMessage.trim());
      setUserMessage("");
    }
  };

  const handleSettingsChange = (newSettings) => {
    if (newSettings.clearChat) {
      socketRef.current?.emit('clear_history');
      delete newSettings.clearChat; // Don't save this flag
    }
    if (newSettings.startCalibration) {
      setShowCalibration(true);
      setShowSettings(false); // Close settings
      delete newSettings.startCalibration; // Don't save this flag
    }
    setSettings(newSettings);
    localStorage.setItem('roomie_settings', JSON.stringify(newSettings));
  };

  return (
    <div className="studio-root">
      <header className="studio-header">
        <div className="logo">
          ROOMii <span className="spark">✦</span>
          <span className="version">v2.0</span>
        </div>
        <div className="header-controls">
          <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            <span className="status-dot" />
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
          {isLoggedIn && (
            <>
              <div className="user-badge">👤 {username}</div>
              <button className="btn ghost small" onClick={() => setShowEmotionChart(!showEmotionChart)}>
                📊 Emotions
              </button>
              <button className="btn ghost small" onClick={() => setShowAnalytics(true)}>
                📈 Analytics
              </button>
              <button className="btn ghost small" onClick={() => setShowSettings(true)}>
                ⚙️ Settings
              </button>
            </>
          )}
        </div>
      </header>

      {!isLoggedIn ? (
        <div className="access-screen">
          <motion.div
            className="access-card"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <h2>👋 Welcome to ROOMii</h2>
            <p>{isSignup ? "Create an account to get started" : "Login to continue your journey"}</p>

            <div className="auth-tabs" style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', justifyContent: 'center' }}>
              <button
                className={`btn ${!isSignup ? 'accent' : 'ghost'} small`}
                onClick={() => setIsSignup(false)}
              >
                Login
              </button>
              <button
                className={`btn ${isSignup ? 'accent' : 'ghost'} small`}
                onClick={() => setIsSignup(true)}
              >
                Signup
              </button>
            </div>

            <form onSubmit={handleAuth} style={{ marginTop: '1rem' }}>
              <input
                type="text"
                value={loginInput}
                onChange={(e) => setLoginInput(e.target.value)}
                placeholder="Username"
                className="chat-input"
                style={{
                  width: '100%',
                  marginBottom: '1rem',
                  background: 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px'
                }}
                autoFocus
              />
              <input
                type="password"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                placeholder="Password"
                className="chat-input"
                style={{
                  width: '100%',
                  marginBottom: '1rem',
                  background: 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px'
                }}
              />

              {authError && (
                <div style={{ color: '#ef4444', marginBottom: '1rem', fontSize: '0.9rem' }}>
                  {authError}
                </div>
              )}

              <button type="submit" className="btn accent large" style={{ width: '100%' }} disabled={!loginInput.trim() || !passwordInput.trim()}>
                {isSignup ? "Create Account" : "Login"}
              </button>
            </form>

            <div style={{ marginTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '1.5rem' }}>
              <button className="btn ghost" style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
                  <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fillRule="evenodd" fillOpacity="1" fill="#4285F4" stroke="none"></path>
                  <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fillRule="evenodd" fillOpacity="1" fill="#34A853" stroke="none"></path>
                  <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fillRule="evenodd" fillOpacity="1" fill="#FBBC05" stroke="none"></path>
                  <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fillRule="evenodd" fillOpacity="1" fill="#EA4335" stroke="none"></path>
                </svg>
                Continue with Google
              </button>
            </div>
          </motion.div>
        </div>
      ) : !micGranted ? (
        <div className="access-screen">
          <motion.div
            className="access-card"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <h2>🔐 Access Required</h2>
            <p>ROOMii needs microphone and camera access to detect your emotions and respond naturally.</p>
            <button className="btn accent large" onClick={requestAccess}>
              Allow Access
            </button>
          </motion.div>
        </div>
      ) : (
        <main className="studio-main">
          <section className="avatar-card">
            <div className="glass-card">
              <Canvas camera={{ position: [0, 0.9, 4.2], fov: 45 }}>
                <Suspense fallback={<Html center><div className="loading">Loading ROOMii…</div></Html>}>
                  <RoomiiModel mood={mood} isSpeaking={isSpeaking} emotionStrength={0.5} />
                  <ParticleSystem mood={mood} intensity={0.8} />
                  <OrbitControls enableZoom={false} enablePan={false} maxPolarAngle={Math.PI / 2} />
                </Suspense>
              </Canvas>
              <div className="card-hud">
                <div className="mood-pill">
                  Mood: <strong>{mood}</strong>
                </div>
                <div className="personality-badge">
                  {currentPersonality}
                </div>
                <div className="mic-status">
                  {isSpeaking ? "🎤 Speaking..." : isProcessing ? "🧠 Thinking..." : isListening ? "🎯 Listening..." : "🎧 Ready..."}
                </div>

              </div>
            </div>
          </section>

          <aside className="controls-panel">
            <div className="panel chat-panel">
              <h3>💬 Conversation</h3>
              <div className="chat-box">
                <AnimatePresence>
                  {messages.map((msg, i) => (
                    <motion.div
                      key={i}
                      className={`chat-line ${msg.sender}`}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      {msg.sender === "user" && "🧍 You: "}
                      {msg.sender === "bot" && `🤖 ${msg.personality || 'ROOMii'}: `}
                      {msg.sender === "bot" && i === messages.length - 1 && isProcessing ? (
                        <StreamingText text={msg.text} speed={20} />
                      ) : (
                        msg.text
                      )}
                    </motion.div>
                  ))}
                </AnimatePresence>
                <div ref={chatEndRef} />
              </div>

              <div className="chat-input-bar">
                <input
                  type="text"
                  className="chat-input"
                  value={userMessage}
                  onChange={(e) => setUserMessage(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSend()}
                  placeholder="Type your message here..."
                  disabled={isProcessing}
                />
                <button className="send-btn" onClick={handleSend} disabled={isProcessing}>
                  ➤
                </button>
                {isSpeaking && (
                  <button className="stop-btn-mini" onClick={handleStop} title="Stop Speaking">
                    ⏹
                  </button>
                )}
              </div>

              {showEmotionChart && emotionHistory.length > 0 && (
                <motion.div
                  className="emotion-chart-wrapper"
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                >
                  <EmotionChart emotionHistory={emotionHistory} />
                </motion.div>
              )}
            </div>
          </aside>
        </main>
      )}



      <SettingsPanel
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        settings={settings}
        onSettingsChange={handleSettingsChange}
      />

      <AnalyticsDashboard
        socket={socketRef.current}
        isOpen={showAnalytics}
        onClose={() => setShowAnalytics(false)}
      />

      <EmotionCalibration
        socket={socketRef.current}
        isOpen={showCalibration}
        onClose={() => setShowCalibration(false)}
      />
    </div>
  );
}
