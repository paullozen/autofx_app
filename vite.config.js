import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:3001',
      '/execute': 'http://localhost:3001',
      '/stop': 'http://localhost:3001',
      '/send-input': 'http://localhost:3001',
      '/open-folder': 'http://localhost:3001',
      '/list-profiles': 'http://localhost:3001',
      '/delete-profile': 'http://localhost:3001',
      '/save-script': 'http://localhost:3001'
    }
  }
})
