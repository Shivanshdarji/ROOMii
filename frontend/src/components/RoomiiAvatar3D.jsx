import React, { useState, useRef, useEffect, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, useGLTF, Html } from "@react-three/drei";
import * as THREE from "three";
import { FontLoader } from "three/examples/jsm/loaders/FontLoader.js";
import { TextGeometry } from "three/examples/jsm/geometries/TextGeometry.js";

function RoomiiModel({ mood = "idle", isSpeaking = false, emotionStrength = 0.5, slow = true }) {
  const group = useRef();
  const { scene, animations } = useGLTF("/models/roomii_bot.glb");
  const mixer = useRef();
  const currentAction = useRef(null);
  const time = useRef(0);

  const moodAnimations = { idle: 0, happy: 1, sad: 2, wave: 3, angry: 4, surprise: 5 };

  useEffect(() => {
    if (!animations?.length) return;
    mixer.current = new THREE.AnimationMixer(scene);
    const index = moodAnimations[mood] ?? 0;
    const action = mixer.current.clipAction(animations[index]);
    if (currentAction.current) currentAction.current.fadeOut(0.4);
    action.reset().fadeIn(0.4).play();
    currentAction.current = action;
  }, [animations, mood, scene]);

  const ledFaces = {
    idle: "-_-",
    happy: "^_^",
    sad: "T_T",
    wave: "o/",
    angry: ">_<",
    surprise: "O_O",
  };

  useEffect(() => {
    if (!scene) return;
    const loader = new FontLoader();
    loader.load(
      "https://threejs.org/examples/fonts/helvetiker_regular.typeface.json",
      (font) => {
        const geometry = new TextGeometry(ledFaces[mood] || "-_-", {
          font,
          size: 0.22,
          height: 0.02,
        });
        const material = new THREE.MeshBasicMaterial({ color: 0xffff66 });
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(-0.35, 0.45, 0.9);
        mesh.name = "roomiiEyes";
        const old = scene.getObjectByName("roomiiEyes");
        if (old) scene.remove(old);
        scene.add(mesh);
      }
    );
  }, [mood, scene]);

  useEffect(() => {
    if (!group.current || !scene) return;
    if (!group.current.children.includes(scene)) {
      group.current.add(scene);
      group.current.scale.set(0.9, 0.9, 0.9);
      group.current.position.set(0, -0.3, 0);
    }
  }, [scene]);

  useFrame((_, delta) => {
    if (!group.current) return;
    mixer.current?.update(delta);
    const speed = slow ? 0.5 : 1.0;
    time.current += delta * speed;

    const yMotion = Math.sin(time.current) * (0.025 + emotionStrength * 0.01);
    const rot = Math.sin(time.current * 0.6) * 0.06;
    group.current.position.y = -0.3 + yMotion;
    group.current.rotation.y = rot;

    const pulse = isSpeaking ? 1 + Math.abs(Math.sin(time.current * 6)) * 0.03 : 1;
    group.current.scale.set(0.9 * pulse, 0.9 * pulse, 0.9 * pulse);
  });

  return <group ref={group} />;
}

export default function RoomiiAvatar3D() {
  const [mood, setMood] = useState("idle");
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [emotionStrength, setEmotionStrength] = useState(0.5);
  const [slow, setSlow] = useState(true);
  const [transcript, setTranscript] = useState("");
  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recog = new SpeechRecognition();
    recog.continuous = true;
    recog.interimResults = true;
    recog.lang = "en-US";

    recog.onstart = () => {
      setIsListening(true);
      setIsSpeaking(true);
    };
    recog.onend = () => {
      setIsListening(false);
      setIsSpeaking(false);
    };
    recog.onresult = (e) => {
      let final = "";
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; ++i) {
        if (e.results[i].isFinal) final += e.results[i][0].transcript;
        else interim += e.results[i][0].transcript;
      }
      setTranscript(final + (interim ? " — " + interim : ""));
    };

    recognitionRef.current = recog;
    return () => recog.stop();
  }, []);

  const toggleListening = () => {
    const recog = recognitionRef.current;
    if (!recog) return alert("Speech recognition not supported.");
    if (isListening) recog.stop();
    else recog.start();
  };

  const moods = ["idle", "happy", "sad", "wave", "angry", "surprise"];

  return (
    <div className="roomii-container">
      <header className="roomii-header">
        <h1 className="roomii-title">
          ROOMii <span>✦</span>
        </h1>
        <button className={`mic-btn ${isListening ? "active" : ""}`} onClick={toggleListening}>
          {isListening ? "🎙 Stop Listening" : "🎤 Start Listening"}
        </button>
      </header>

      <main className="roomii-main">
        <div className="roomii-canvas">
          <Canvas
            camera={{ position: [0, 0.9, 4.2], fov: 45 }}
            gl={{ outputEncoding: THREE.sRGBEncoding, toneMapping: THREE.NoToneMapping }}
          >
            <Suspense fallback={<Html center>Loading Roomii...</Html>}>
              <ambientLight intensity={0.3} />
              <directionalLight position={[2, 2, 4]} intensity={0.8} />
              <RoomiiModel
                mood={mood}
                isSpeaking={isSpeaking}
                emotionStrength={emotionStrength}
                slow={slow}
              />
              <OrbitControls enableZoom={false} enablePan={false} maxPolarAngle={Math.PI / 2} />
            </Suspense>
          </Canvas>
        </div>

        <div className="roomii-controls">
          <h2>Controls</h2>
          <label>Emotion Strength</label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={emotionStrength}
            onChange={(e) => setEmotionStrength(parseFloat(e.target.value))}
          />

          <div className="toggle-box">
            <label>
              <input type="checkbox" checked={slow} onChange={(e) => setSlow(e.target.checked)} />{" "}
              Slow Motion
            </label>
            <label>
              <input
                type="checkbox"
                checked={isSpeaking}
                onChange={(e) => setIsSpeaking(e.target.checked)}
              />{" "}
              Speaking
            </label>
          </div>

          <h3>Moods</h3>
          <div className="mood-buttons">
            {moods.map((m) => (
              <button
                key={m}
                className={`mood-btn ${mood === m ? "active" : ""}`}
                onClick={() => setMood(m)}
              >
                {m}
              </button>
            ))}
          </div>

          <h3>Voice Transcript</h3>
          <div className="transcript-box">
            {transcript || "Say something or click Start Listening..."}
          </div>
        </div>
      </main>
    </div>
  );
}
