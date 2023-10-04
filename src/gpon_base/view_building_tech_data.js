import {createApp} from 'vue'
import App from './View_Building_Tech_data.vue'
import PrimeVue from 'primevue/config';
import ToastService from 'primevue/toastservice';
import "primevue/resources/themes/lara-light-indigo/theme.css";

createApp(App)
    .use(PrimeVue)
    .use(ToastService)
    .mount('#app')
