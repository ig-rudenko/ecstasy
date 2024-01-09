import {fileURLToPath, URL} from 'node:url'

import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url)),
            '/static': fileURLToPath(new URL('../static', import.meta.url))
        }
    },
    server: {
        proxy: {
            '/gpon/api': 'http://127.0.0.1:8000',
            '^/static/.*': 'http://127.0.0.1:8000',
            '/device': 'http://127.0.0.1:8000',
            '/tools': 'http://127.0.0.1:8000',
            '/gather': 'http://127.0.0.1:8000',
        }
    }
})