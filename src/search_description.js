import {createApp} from 'vue'
import App from './App_description_search.vue'
import PrimeVue from "primevue/config";

const app = createApp(App);
app.use(PrimeVue);
app.mount('#description-search')
