import {createApp} from 'vue'
import App from './App.vue'
import PrimeVue from "primevue/config";
import "primevue/resources/themes/lara-light-indigo/theme.css";
import Tooltip from "primevue/tooltip";

const app = createApp(App)
app.directive('tooltip', Tooltip);
app.use(PrimeVue, {ripple: true})
app.mount('#app')
