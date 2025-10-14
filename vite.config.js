import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/health': {
        target: 'http://16.163.163.204:8000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://16.163.163.204:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://16.163.163.204:8000',
        ws: true,
        changeOrigin: true,
      }
    }
  }
})
