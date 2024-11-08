import {createRouter, createWebHistory} from "vue-router";
import {useStore} from "vuex";


const router = createRouter({
    history: createWebHistory(),
    routes: [
        {path: "/", component: () => import("@/pages/home/Home.vue"), name: "home"},
        {path: "/devices", component: () => import("@/pages/devicesList/DevicesList.vue"), name: "devices-list"},
        {path: "/device/:deviceName", component: () => import("@/pages/deviceInfo/DeviceInfo.vue"), name: "device"},
        {
            path: "/tools/search",
            component: () => import("@/pages/descriptionSearch/DescriptionSearch.vue"),
            name: "tools-search"
        },
        {
            path: "/tools/traceroute",
            component: () => import("@/pages/traceroute/Traceroute.vue"),
            name: "tools-traceroute"
        },
        {path: "/account/login", component: () => import("@/pages/login/Login.vue"), name: "login"},
        {path: "/gpon", component: () => import("@/pages/gpon_base/GPONPage.vue"), name: "gpon"},
        {path: "/gpon/tech-data", component: () => import("@/pages/gpon_base/TechData.vue"), name: "gpon-tech-data"},
        {
            path: "/gpon/tech-data/create",
            component: () => import("@/pages/gpon_base/CreateTechData.vue"),
            name: "gpon-create-tech-data"
        },
        {
            path: "/gpon/tech-data/:deviceName",
            component: () => import("@/pages/gpon_base/ViewOLT_TechData.vue"),
            name: "gpon-olt-tech-data"
        },
        {
            path: "/gpon/tech-data/building/:id",
            component: () => import("@/pages/gpon_base/ViewBuildingTechData.vue"),
            name: "gpon-building-tech-data"
        },
    ],
});

router.beforeEach((to) => {
    // redirect to login page if not logged in and trying to access a restricted page
    const publicPages = ['/account/login'];
    const authRequired = !publicPages.includes(to.path);
    const store = useStore();

    if (authRequired && store.state && !store.state.auth.status.loggedIn) {
        return '/account/login';
    }
});

export default router;