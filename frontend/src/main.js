import { createApp } from 'vue'
import { createPinia } from 'pinia'
import AppWrapper from './AppWrapper.vue'
import router from "@/router";
import VueApexCharts from "vue3-apexcharts";

const pinia = createPinia()

createApp(AppWrapper)
    .use(pinia)
    .use(router)
    .use(VueApexCharts)
    .mount('#app')
