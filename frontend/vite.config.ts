import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/chat': 'http://localhost:8000',
      '/resorts': 'http://localhost:8000',
      '/forecast': 'http://localhost:8000',
      '/profile': 'http://localhost:8000',
    },
  },
});
