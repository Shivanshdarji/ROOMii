/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        glow1: '#0ef0e7',
        glow2: '#3a0ca3',
      },
      backgroundImage: {
        'neo-ai': 'linear-gradient(135deg, #0f0f1a 0%, #060606 100%)',
      },
    },
  },
  plugins: [],
}
