import {createApp} from 'vue'
import App from './View_OLT_Tech_data.vue'
import PrimeVue from 'primevue/config';
import ToastService from 'primevue/toastservice';
import ConfirmationService from "primevue/confirmationservice";
import "primevue/resources/themes/lara-light-indigo/theme.css";

const app = createApp(App);
app.use(PrimeVue);
app.use(ToastService);
app.use(ConfirmationService);
app.mount('#app');
