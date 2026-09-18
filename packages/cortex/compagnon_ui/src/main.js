import { createApp } from 'vue'
import { router } from './router/index.js'
import './style.css'
import App from './App.vue'

// Compagnon — surface produit :5174 (pas de redirect Pilot)
createApp(App).use(router).mount('#app')

if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js')
      .then((reg) => {
        // Force prise en compte du nouveau SW (évite shell HTML/JS périmé)
        reg.update().catch(() => {})
        if (reg.waiting) reg.waiting.postMessage('SKIP_WAITING')
        navigator.serviceWorker.ready.then((ready) => {
          ready.active?.postMessage('CLEAR_CACHES')
        }).catch(() => {})
      })
      .catch(() => {})
  })
}
