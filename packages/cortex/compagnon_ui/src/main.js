import { createApp } from 'vue'
import { router } from './router/index.js'
import './style.css'
import App from './App.vue'

// Compagnon — surface produit :5174 (pas de redirect Pilot)
createApp(App).use(router).mount('#app')

if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {})
  })
}
