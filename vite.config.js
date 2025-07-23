import { fileURLToPath, URL } from 'node:url'
import { dirname, resolve } from 'node:path'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Vue 관련 라이브러리 분할
          'vue-vendor': ['vue'],
          // Vuetify 라이브러리 분할
          'vuetify-vendor': ['vuetify'],
          // axios 라이브러리 분할
          'http-vendor': ['axios'],
          // Konva 관련 라이브러리 분할
          'konva-vendor': ['konva', 'vue-konva']
        }
      }
    },
    // 청크 크기 경고 임계값 조정 (1MB로 증가)
    chunkSizeWarningLimit: 1000
  },
  server: {
    host: '0.0.0.0',
    proxy: {
      // API 요청을 백엔드 서버로 프록시
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      // 모델 관련 요청도 프록시
      '/models': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      // 파일 관련 요청도 프록시
      '/files': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      // 기타 백엔드 엔드포인트
      '/upload': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/image': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/device-info': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/device': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/model': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/labeling': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/project': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/refresh': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    },
    fs: {
      allow: [
        // 기본 허용 디렉토리
        fileURLToPath(new URL('./', import.meta.url)),
        // 프로젝트 자체 node_modules
        resolve(dirname(fileURLToPath(import.meta.url)), 'node_modules')
      ]
    }
  }
})
