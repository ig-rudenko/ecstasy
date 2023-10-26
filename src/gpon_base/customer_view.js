import {createApp} from 'vue'
import PrimeVue from 'primevue/config';
import ToastService from "primevue/toastservice";
import App from './CustomerView.vue'
import "primevue/resources/themes/lara-light-indigo/theme.css";

createApp(App)
    .use(PrimeVue)
    .use(ToastService)
    .mount('#app')
