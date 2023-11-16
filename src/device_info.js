import {createApp} from 'vue'
import App from './App_device_info.vue'
import VueClipboard from 'vue-clipboard2'
import PrimeVue from "primevue/config";

const app = createApp(App);
app.use(VueClipboard);
app.use(PrimeVue);
app.mount('#device');
