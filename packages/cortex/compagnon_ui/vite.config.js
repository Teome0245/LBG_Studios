import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiBase = env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  const pilotBase = env.VITE_PILOT_API_BASE_URL || 'http://192.168.0.140:8000'

  const proxyPaths = [
    '/ask',
    '/history',
    '/models',
    '/brain',
    '/agents',
    '/debug',
    '/execute',
    '/runtime',
    '/antigravity',
    '/monitoring',
    '/world',
    '/godot',
    '/metrics',
    '/health',
    '/monitor',
    '/lyra',
    '/character',
    '/spontaneity',
    '/tts',
  ]

  const proxy = Object.fromEntries(
    proxyPaths.map((p) => [p, { target: apiBase, changeOrigin: true }])
  )
  // Agir : /api/pilot/* → Cortex Pilot /v1/pilot/*
  proxy['/api/pilot'] = {
    target: pilotBase,
    changeOrigin: true,
    rewrite: (p) => p.replace(/^\/api\/pilot/, '/v1/pilot'),
  }

  return {
    plugins: [vue(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 5175,
      proxy,
    },
  }
})
