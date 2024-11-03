import {createRouter, createWebHistory} from "vue-router";


const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: "/", component: () => import("@/pages/home/Home.vue"), name: "home"},
        { path: "/devices", component: () => import("@/pages/devicesList/DevicesList.vue"), name: "devices-list"},
        { path: "/tools/search", component: () => import("@/pages/descriptionSearch/DescriptionSearch.vue"), name: "tools-search"},
        { path: "/tools/traceroute", component: () => import("@/pages/traceroute/Traceroute.vue"), name: "tools-traceroute"},
        { path: "/account/login", component: () => import("@/pages/login/Login.vue"), name: "login"},
    ],
});

export default router;