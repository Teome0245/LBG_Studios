/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/App.vue",
    "./src/pages/HomePage.vue",
    "./src/pages/LyraPage.vue",
    "./src/components/ChatFlow.vue",
    "./src/components/ChatHeader.vue",
    "./src/components/ChatInput.vue",
    "./src/components/Sidebar.vue",
    "./src/components/ProviderBadge.vue",
    "./src/components/lyra/*.vue",
  ],
  theme: {
    extend: {
      fontFamily: {
        inter: ['Inter', 'sans-serif'],
        outfit: ['Outfit', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
