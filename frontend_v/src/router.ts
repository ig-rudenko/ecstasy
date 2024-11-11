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

        {path: "/maps", component: () => import("@/pages/maps/MapsListView.vue"), name: "maps"},
        {path: "/maps/:id", component: () => import("@/pages/maps/MapView.vue"), name: "map-view"},

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
        {
            path: "/gpon/tech-data/end3/:id",
            component: () => import("@/pages/gpon_base/ViewEnd3TechData.vue"),
            name: "gpon-end3-tech-data"
        },
        {
            path: "/gpon/subscribers-data",
            component: () => import("@/pages/gpon_base/SubscribersData.vue"),
            name: "gpon-subscribers-data"
        },
        {
            path: "/gpon/subscribers-data/create",
            component: () => import("@/pages/gpon_base/CreateSubscriberData.vue"),
            name: "gpon-create-subscriber-data"
        },
        {
            path: "/gpon/subscribers-data/customers/:id",
            component: () => import("@/pages/gpon_base/CustomerView.vue"),
            name: "gpon-view-subscriber"
        },

        {path: "/:pathMatch(.*)*", redirect: "/"},
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