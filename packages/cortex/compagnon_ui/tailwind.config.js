/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        inter: ['Inter', 'sans-serif'],
        outfit: ['Outfit', 'sans-serif'],
      },
      colors: {
        studio: {
          dark: '#030712',
          card: 'rgba(15, 23, 42, 0.72)',
          border: 'rgba(255, 255, 255, 0.08)',
          accent: '#10b981',
          warm: '#f59e0b',
          cyan: '#06b6d4',
        },
      },
    },
  },
  plugins: [],
}
