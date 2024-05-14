import {createApp} from 'vue';
import App from './App.vue';
import PrimeVue from "primevue/config";
import Tooltip from "primevue/tooltip";

import "primevue/resources/themes/lara-light-indigo/theme.css";

const app = createApp(App);
app.directive('Tooltip', Tooltip);
app.use(PrimeVue, {ripple: true});
app.mount('#app');
