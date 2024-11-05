import {createRouter, createWebHistory} from "vue-router";
import {useStore} from "vuex";


const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: "/", component: () => import("@/pages/home/Home.vue"), name: "home"},
        { path: "/devices", component: () => import("@/pages/devicesList/DevicesList.vue"), name: "devices-list"},
        { path: "/devices/:deviceName", component: () => import("@/pages/deviceInfo/DeviceInfo.vue"), name: "device"},
        { path: "/tools/search", component: () => import("@/pages/descriptionSearch/DescriptionSearch.vue"), name: "tools-search"},
        { path: "/tools/traceroute", component: () => import("@/pages/traceroute/Traceroute.vue"), name: "tools-traceroute"},
        { path: "/account/login", component: () => import("@/pages/login/Login.vue"), name: "login"},
    ],
});

router.beforeEach(async (to) => {
    // redirect to login page if not logged in and trying to access a restricted page
    const publicPages = ['/account/login'];
    const authRequired = !publicPages.includes(to.path);
    const store = useStore();

    if (authRequired && !store.state.auth.user) {
        return '/account/login';
    }
});

export default router;