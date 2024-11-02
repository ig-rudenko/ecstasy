<script setup lang="ts">
import {useStore} from "vuex";
import {computed, ref} from "vue";

import LogoutButton from "@/components/LogoutButton.vue";

import {getAvatar} from "@/formats";
import {User} from "@/services/user";
import permissions from "@/services/permissions";
import {getCurrentTheme, setAutoTheme, setDarkTheme, setLightTheme, ThemesValues} from "@/services/themes";
import router from "@/router.ts";
import {MenuItem} from "primevue/menuitem";

const store = useStore()
const user: User | null = store.state.auth.user

const items = ref<MenuItem[]>([
  {
    label: 'Оборудование',
    icon: 'devices',
    url: "home",
  },
]);


const menuItems = computed(() => {
  if (permissions.has("auth.access_ecstasy_loop")) {
    items.value.push({
      label: 'Консоль',
      icon: 'console',
    })
  }

  if (permissions.has("auth.can_view_maps")) {
    items.value.push({
      label: 'Карты',
      icon: 'map',
    })
  }

  if (permissions.has("auth.access_desc_search")) {
    items.value.push({
      label: 'Поиск',
      icon: 'search',
    })
  }

  if (permissions.has("auth.access_traceroute")) {
    items.value.push({
      label: 'Трассировка',
      icon: 'topology',
    })
  }

  if (permissions.has("auth.access_wtf_search")) {
    items.value.push({
      label: 'WTF',
      icon: 'radar',
    })
  }

  if (permissions.has("auth.access_rings") || permissions.has("auth.access_transport_rings")) {
    items.value.push({
      label: 'Кольца',
      icon: 'ring',
    })
  }

  if (permissions.hasGPONAnyPermission()) {
    items.value.push({
      label: 'GPON',
      icon: 'gpon',
    })
  }

  return items;

});


const currentRouteName = computed(() => {
  return router.currentRoute.value.name
});


const currentTheme = ref<ThemesValues>(getCurrentTheme());

const toggle = () => {
  if (currentTheme.value == "auto") setLightTheme();
  if (currentTheme.value == "light") setDarkTheme();
  if (currentTheme.value == "dark") setAutoTheme();
  currentTheme.value = getCurrentTheme();
}

</script>

<template>
  <div class="bg-zinc-800 dark:bg-gray-950">
    <Menubar :model="menuItems.value" class="container mx-auto bg-zinc-800 dark:bg-gray-950 !border-none !rounded-none" :pt="{itemContent: {class: 'bg-zinc-800 dark:!bg-gray-950'}}">
      <template #start>
        <router-link :to="{name: 'home'}" class="flex items-center my-2 my-lg-0 me-lg-auto text-white text-decoration-none">
          <img class="me-3 w-[96px] h-[96px] rounded-full" src="/video/logo.webp" alt="logo">
          <div style="font-family: 'Century Gothic', fantasy;" class="ps-4 pr-10 text-gray-300 text-2xl sm:text-[2rem]">Ecstasy</div>
        </router-link>
      </template>

      <template #item="{ item }">
        <router-link to="/">
          <div :class="currentRouteName==item.url?'border-s-4 md:border-s-0 md:border-t-2 border-indigo-500':''"
               class="ps-4 md:ps-0 flex items-center md:block">
            <img :src="'/img/menu/'+item.icon+'.png'" class="md:mx-auto w-[48px] md:w-[54px] xl:w-[64px] mb-1" :alt="item.icon" />
            <div class="flex flex-col">
              <span class="m-0 p-0 text-xl md:text-[0.7rem] text-gray-300 text-center">{{item.label}}</span>
            </div>
          </div>
        </router-link>
      </template>

      <template #end>
        <div class="flex items-center gap-2">
          <Avatar v-if="user" :image="getAvatar(user.username)" v-tooltip.bottom="user.firstName" shape="circle" :size="'large'" />
          <div class="flex flex-col">
            <Button icon="pi pi-circle" v-if="currentTheme == 'auto'" @click="toggle"
                    v-tooltip.bottom="'Включить светлую тему'"
                    class="hover:text-gray-900 dark:text-gray-400 hover:dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 bg-opacity-15"
                    text/>
            <Button icon="pi pi-sun" v-if="currentTheme == 'light'" @click="toggle"
                    v-tooltip.bottom="'Включить темную тему'"
                    class="hover:text-gray-900 dark:text-gray-400 hover:dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 bg-opacity-15"
                    text/>
            <Button icon="pi pi-moon" v-if="currentTheme == 'dark'" @click="toggle"
                    v-tooltip.bottom="'Выбрать тему автоматически'"
                    class="hover:text-gray-900 dark:text-gray-400 hover:dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 bg-opacity-15"
                    text/>
            <LogoutButton />
          </div>
        </div>
      </template>
    </Menubar>
  </div>

</template>

<style scoped>

</style>