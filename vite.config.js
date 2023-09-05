import {fileURLToPath, URL} from 'node:url'

import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        }
    },
    // server: {
    //   proxy: {
    //     '/api/': {
    //       target: 'http://localhost:8080',
    //       changeOrigin: true,
    //       secure: false,
    //       ws: true,
    //     },
    //     '/token': {
    //       target: 'http://localhost:8080',
    //       changeOrigin: true,
    //       secure: false,
    //       ws: true,
    //     }
    //   }
    // }
})