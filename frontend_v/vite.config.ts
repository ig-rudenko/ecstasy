import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import {fileURLToPath, URL} from "node:url";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.indexOf('node_modules') !== -1) {
            return id.toString().split("node_modules/")[1].split("/")[0].toString();
          }
        }
      }
    }
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'https://ecstasy.noc.net92.ru',
        changeOrigin: true,
        secure: false,
        ws: true,
      },
      '/tools/api': {
        target: 'https://ecstasy.noc.net92.ru',
        changeOrigin: true,
        secure: false,
        ws: true,
      },
      '/gather': {
        target: 'https://ecstasy.noc.net92.ru',
        changeOrigin: true,
        secure: false,
        ws: true,
      },
      '/device/api': {
        target: 'https://ecstasy.noc.net92.ru',
        changeOrigin: true,
        secure: false,
        ws: true,
      },
      '/media/': {
        target: 'https://ecstasy.noc.net92.ru',
        changeOrigin: true,
        secure: false,
        ws: true,
      },
      '/gpon/api': {
        target: 'https://ecstasy.noc.net92.ru',
        changeOrigin: true,
        secure: false,
        ws: true,
      },
    }
  },
})