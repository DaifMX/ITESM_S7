import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      // El dashboard no habla con el ESP8266: habla con la API de Express,
      // que es quien lee el puerto serie. Cambia el destino con
      // API_HOST=http://otra-maquina:3001 pnpm dev
      '/api': {
        target: process.env.API_HOST ?? 'http://localhost:3001',
        changeOrigin: true,
      },
    },
  },
})
