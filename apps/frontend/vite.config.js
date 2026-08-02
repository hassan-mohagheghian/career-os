/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src")
    }
  },
  server: {
    proxy: {
      '/api': 'http://localhost:5000',
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true
      }
    }
  },
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/test/**', 'src/**/*.d.ts', 'src/main.tsx', 'src/App.tsx'],
      thresholds: {
        lines: 92,
        functions: 92,
        branches: 92,
        statements: 92
      }
    },
    projects: [{
      extends: true,
      test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: ['./src/test/setup.ts'],
        css: true
      }
    }]
  }
});