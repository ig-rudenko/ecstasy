import { createApp } from 'vue'
import Tooltip from 'primevue/tooltip';
import PrimeVue from 'primevue/config';
import App from './App_access_ring.vue'

import "primevue/resources/primevue.min.css";
import "primevue/resources/themes/lara-light-indigo/theme.css";

const app = createApp(App)
app.use(PrimeVue);
app.directive('tooltip', Tooltip);

app.mount('#app')
