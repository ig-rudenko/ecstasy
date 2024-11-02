import {createApp} from "vue";
import PrimeVue from "primevue/config";
import ToastService from "primevue/toastservice";

import App from "@/App.vue";

export const app = createApp(App);
app.use(PrimeVue, {ripple: true});
app.use(ToastService);