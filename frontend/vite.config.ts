import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Proxy all API-related paths to backend with /api prefix
      '^/(projects|employees|scan|matches|embeddings|database|state)': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => `/api${path}`,
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})