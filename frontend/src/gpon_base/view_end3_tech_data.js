import {createApp} from 'vue'
import App from './View_end3_tech_data.vue'
import PrimeVue from 'primevue/config';
import ToastService from 'primevue/toastservice';
import Tooltip from 'primevue/tooltip';
import "primevue/resources/primevue.min.css"
import "primevue/resources/themes/lara-light-indigo/theme.css";

createApp(App)
    .use(PrimeVue)
    .use(ToastService)
    .directive('tooltip', Tooltip)
    .mount('#app')
