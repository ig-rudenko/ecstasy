import { createApp } from 'vue'
import App from './App_device_info.vue'
import VueClipboard from 'vue-clipboard2'

createApp(App).use(VueClipboard).mount('#device')
