import {createRouter, createWebHistory} from "vue-router";


const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: "/", component: () => import("@/pages/home/Home.vue"), name: "home"},
        { path: "/account/login", component: () => import("@/pages/login/Login.vue"), name: "login"},
    ],
});

export default router;