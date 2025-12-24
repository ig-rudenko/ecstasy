<script setup lang="ts">
import {useStore} from "vuex";
import {computed, ref} from "vue";

import LogoutButton from "@/components/LogoutButton.vue";

import {getAvatar} from "@/formats";
import {User} from "@/services/user";
import permissions from "@/services/permissions";
import {getCurrentTheme, setAutoTheme, setDarkTheme, setLightTheme, ThemesValues} from "@/services/themes";
import {MenuItem} from "primevue/menuitem";
import pinnedDevices from "@/services/pinnedDevices.ts";

const store = useStore()
const user: User | null = store.state.auth.user

const items = ref<MenuItem[]>([
  {
    label: 'Оборудование',
    icon: 'devices',
    url: "/devices",
  }
]);


const menuItems = computed(() => {
  if (permissions.hasConsoleAccess()) {
    items.value.push({
      label: 'Консоль',
      icon: 'console',
      url: permissions.getConsoleUrl() || "#",
      newPage: true,
    })
  }

  if (permissions.hasEcstasyLoopPermission()) {
    items.value.push({
      label: 'Loop Detector',
      icon: 'loop',
      url: permissions.getEcstasyLoopUrl() || "#",
      newPage: true,
    })
  }

  if (permissions.has("auth.can_view_maps")) {
    items.value.push({
      label: 'Карты',
      icon: 'map',
      url: '/maps',
    })
  }

  if (permissions.has("auth.access_desc_search")) {
    items.value.push({
      label: 'Поиск',
      icon: 'search',
      url: '/tools/search',
    })
  }

  if (permissions.has("auth.access_traceroute")) {
    items.value.push({
      label: 'Трассировка',
      icon: 'topology',
      url: '/tools/traceroute',
    })
  }

  if (permissions.has("auth.access_wtf_search")) {
    items.value.push({
      label: 'WTF',
      icon: 'radar',
      url: '/tools/wtf'
    })
  }

  if (permissions.has("auth.access_rings") || permissions.has("auth.access_transport_rings")) {
    items.value.push({
      label: 'Кольца',
      icon: 'ring',
      url: '/ring-manager'
    })
  }

  if (permissions.hasGPONAnyPermission()) {
    items.value.push({
      label: 'GPON',
      icon: 'gpon',
      url: '/gpon',
    })
  }

  return items;

});

function isCurrent(url: string) {
  return location.pathname.startsWith(url);
}

const currentTheme = ref<ThemesValues>(getCurrentTheme());

const toggle = () => {
  if (currentTheme.value == "auto") setLightTheme();
  if (currentTheme.value == "light") setDarkTheme();
  if (currentTheme.value == "dark") setAutoTheme();
  currentTheme.value = getCurrentTheme();
}

const pinnedDevicesRef = ref();
const togglePinedDevices = (event: Event) => {
  pinnedDevicesRef.value.toggle(event);
}

function showDevicePinned(): boolean {
  return location.href.includes('device') && pinnedDevices.pinnedDevices.value.length > 0;
}

</script>

<template>
  <div class="bg-zinc-800 dark:bg-gray-950">
    <Menubar :model="menuItems.value"
             class="xl:container mx-auto bg-zinc-800 dark:bg-gray-950 !border-none !rounded-none"
             :pt="{itemContent: {class: 'bg-zinc-800 dark:!bg-gray-950'}}">
      <template #start>
        <router-link to="/" class="flex items-center my-2 my-lg-0 me-lg-auto text-white text-decoration-none z-10">
          <img class="me-3 !w-[96px] !h-[96px] rounded-full" src="/video/logo.webp" alt="logo">
          <div style="font-family: 'Century Gothic', fantasy;"
               class="hidden sm:block ps-4 pr-10 text-gray-300 text-2xl sm:text-[2rem]">
            Ecstasy
          </div>
        </router-link>
      </template>

      <template #item="{ item }">
        <router-link :to="item.url || ''" :target="item.newPage?'_blank':''">
          <div
              :class="isCurrent(item.url || '_')?'border-s-4 md:border-s-0 md:border-t-2 border-indigo-500':''"
              class="ps-4 md:ps-0 flex items-center md:block">
            <img :src="'/img/menu/'+item.icon+'.png'" class="md:mx-auto w-[48px] md:w-[54px] xl:w-[64px] mb-1"
                 :alt="item.icon"/>
            <div class="flex flex-col">
              <span class="m-0 p-0 text-xl md:text-[0.7rem] text-gray-300 text-center">{{ item.label }}</span>
            </div>
          </div>
        </router-link>
      </template>

      <template #end>
        <div class="flex items-center gap-2">
          <a v-if="user && user.isStaff" href="/admin/">
            <Button icon="pi pi-cog" size="large" text
                    v-tooltip.bottom="'Панель администратора'"/>
          </a>
          <Avatar v-if="user" :image="getAvatar(user.username)" v-tooltip.bottom="user.firstName" shape="circle"
                  :size="'large'"/>
          <div class="flex flex-col">
            <Button icon="pi pi-circle" v-if="currentTheme == 'auto'" @click="toggle"
                    v-tooltip.left="'Включить светлую тему'"
                    class="hover:text-gray-900 dark:text-gray-400 hover:dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 bg-opacity-15"
                    text/>
            <Button icon="pi pi-sun" v-if="currentTheme == 'light'" @click="toggle"
                    v-tooltip.left="'Включить темную тему'"
                    class="hover:text-gray-900 dark:text-gray-400 hover:dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 bg-opacity-15"
                    text/>
            <Button icon="pi pi-moon" v-if="currentTheme == 'dark'" @click="toggle"
                    v-tooltip.left="'Выбрать тему автоматически'"
                    class="hover:text-gray-900 dark:text-gray-400 hover:dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 bg-opacity-15"
                    text/>
            <LogoutButton/>
          </div>
        </div>
      </template>
    </Menubar>
  </div>

  <div class="md:sticky top-0 z-10 w-fit backdrop-blur-sm rounded-md">
    <div>
      <Button v-if="showDevicePinned()" type="button" icon="pi pi-box" label="Закреплённое оборудование" outlined text
              size="small" @click="togglePinedDevices"/>
    </div>
  </div>

  <Popover ref="pinnedDevicesRef" class="p-1">
    <div class="pb-2 mb-2 flex w-full justify-between items-center gap-2 border-b-[1px]">
      <div>Ваши избранные устройства</div>
      <Button v-if="pinnedDevices.pinnedDevices.value.length != 0" outlined icon="pi pi-trash" size="small"
              v-tooltip="'Очистить избранное'"
              severity="danger" @click="pinnedDevices.clear()"/>
    </div>
    <div class="flex flex-col gap-2">
      <div v-for="dev in pinnedDevices.pinnedDevices.value" class="flex flex-row gap-2 items-center ">
        <router-link :to="'/device/'+dev.name" class="text-sm font-mono hover:text-indigo-500 pr-2"
                     v-tooltip="dev.vendor + ' ' + dev.model">{{ dev.name }} ({{ dev.ip }})
        </router-link>
        <a v-if="dev.console_url" :href="dev.console_url" class="group/console cursor-pointer text-indigo-500 pb-1"
           target="_blank">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor"
               class="inline group-hover/console:hidden" viewBox="0 0 16 16">
            <path
                d="M6 9a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3A.5.5 0 0 1 6 9M3.854 4.146a.5.5 0 1 0-.708.708L4.793 6.5 3.146 8.146a.5.5 0 1 0 .708.708l2-2a.5.5 0 0 0 0-.708z"/>
            <path
                d="M2 1a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V3a2 2 0 0 0-2-2zm12 1a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z"/>
          </svg>
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor"
               class="hidden group-hover/console:inline" viewBox="0 0 16 16">
            <path
                d="M0 3a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2zm9.5 5.5h-3a.5.5 0 0 0 0 1h3a.5.5 0 0 0 0-1m-6.354-.354a.5.5 0 1 0 .708.708l2-2a.5.5 0 0 0 0-.708l-2-2a.5.5 0 1 0-.708.708L4.793 6.5z"/>
          </svg>
        </a>
        <a :href="'/device/'+dev.name" target="_blank">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
               class="cursor-pointer hover:text-indigo-500" viewBox="0 0 16 16">
            <path fill-rule="evenodd"
                  d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5"/>
            <path fill-rule="evenodd"
                  d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0z"/>
          </svg>
        </a>
        <i class="pi pi-minus-circle cursor-pointer hover:text-red-500" @click="pinnedDevices.removeDevice(dev)"/>
      </div>
      <div v-if="pinnedDevices.pinnedDevices.value.length == 0">
        Нет избранных устройств
      </div>
    </div>
  </Popover>

</template>
