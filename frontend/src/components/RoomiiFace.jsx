import { motion } from "framer-motion";

const moodColors = {
  happy: "#00FFAA",
  sad: "#4B5D67",
  angry: "#FF4444",
  fear: "#FFD700",
  surprise: "#00C8FF",
  neutral: "#9C9C9C",
};

export default function RoomiiFace({ emotion }) {
  const color = moodColors[emotion] || moodColors.neutral;

  return (
    <motion.div
      className="rounded-full flex items-center justify-center shadow-[0_0_60px_rgba(255,255,255,0.3)]"
      animate={{
        backgroundColor: color,
        scale: [1, 1.05, 1],
        boxShadow: `0 0 40px ${color}`,
      }}
      transition={{
        duration: 2,
        repeat: Infinity,
      }}
      style={{
        width: 200,
        height: 200,
        backgroundColor: color,
      }}
    >
      <motion.div
        className="text-3xl font-bold text-black"
        animate={{ opacity: [0.8, 1, 0.8] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        {emotion.toUpperCase()}
      </motion.div>
    </motion.div>
  );
}
