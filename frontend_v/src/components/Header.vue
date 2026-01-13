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
import AppLink from "@/components/AppLink.vue";
import decorConfig from "@/services/decor.ts";

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
  if (currentTheme.value == "dark") setLightTheme();
  if (currentTheme.value == "light") setDarkTheme();
  // if (currentTheme.value == "dark") setAutoTheme();
  currentTheme.value = getCurrentTheme();
}

const pinnedDevicesRef = ref();
const togglePinedDevices = (event: Event) => {
  pinnedDevicesRef.value.toggle(event);
}

function showDevicePinned(): boolean {
  return location.href.includes('device') && pinnedDevices.pinnedDevices.value.length > 0;
}

const profileRef = ref();
const toggleProfile = (event: Event) => {
  profileRef.value.toggle(event);
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
        <AppLink :to="item.url || ''" :target="item.newPage?'_blank':''">
          <div
              :class="isCurrent(item.url || '_')?'border-s-4 md:border-s-0 md:border-t-2 border-indigo-500':''"
              class="ps-4 md:ps-0 flex items-center md:block">
            <img :src="'/img/menu/'+item.icon+'.png'" class="md:mx-auto w-[48px] md:w-[54px] xl:w-[64px] mb-1"
                 :alt="item.icon"/>
            <div class="flex flex-col">
              <span class="m-0 p-0 text-xl md:text-[0.7rem] text-gray-300 text-center">{{ item.label }}</span>
            </div>
          </div>
        </AppLink>
      </template>

      <template #end>
        <Avatar v-if="user" :image="getAvatar(user.username)" class="cursor-pointer"
                @click="toggleProfile" size="large"/>
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

  <Popover ref="profileRef">
    <div>
      <div v-if="user" class="flex gap-3 items-center">
        <Avatar :image="getAvatar(user.username)" shape="circle" size="large"/>
        <div>
          <div class="flex gap-0.5 items-center">
            <div class="font-mono text-sm">{{ user.username }}</div>
            <Badge v-if="user.isStaff" value="S" size="small" severity="contrast" v-tooltip="'Staff'"/>
            <Badge v-if="user.isSuperuser" value="S" size="small" severity="warn" v-tooltip="'Superuser'"/>
          </div>
          <div class="text-sm">{{ user.firstName + ' ' + user.lastName }}</div>
        </div>
      </div>

      <div class="flex gap-1 items-center justify-center mt-3">
        <a v-if="user && user.isStaff" href="/admin/">
          <Button icon="pi pi-cog" outlined v-tooltip.bottom="'Панель администратора'" severity="secondary" class="hover:text-primary hover:bg-primary-100"/>
        </a>
        <Button icon="pi pi-moon" v-if="currentTheme == 'light'" @click="toggle"
                v-tooltip.bottom="'Включить темную тему'" severity="contrast"
                class="hover:text-gray-200 hover:bg-gray-900"
                outlined/>
        <Button icon="pi pi-sun" v-if="currentTheme == 'dark'" @click="toggle"
                v-tooltip.bottom="'Включить светлую тему'" severity="contrast"
                class="hover:text-gray-900 hover:bg-gray-200"
                outlined/>
        <LogoutButton/>
      </div>


      <div class="mt-4" v-if="[0, 1, 11].indexOf((new Date()).getMonth()) !== -1">
        <label
            class="flex gap-2 items-center border border-gray-300 dark:border-gray-600 rounded p-3 w-full cursor-pointer">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"
               :class="decorConfig.winterDecor?'fill-primary':'fill-gray-500'" viewBox="0 0 16 16">
            <path
                d="M8 16a.5.5 0 0 1-.5-.5v-1.293l-.646.647a.5.5 0 0 1-.707-.708L7.5 12.793V8.866l-3.4 1.963-.496 1.85a.5.5 0 1 1-.966-.26l.237-.882-1.12.646a.5.5 0 0 1-.5-.866l1.12-.646-.884-.237a.5.5 0 1 1 .26-.966l1.848.495L7 8 3.6 6.037l-1.85.495a.5.5 0 0 1-.258-.966l.883-.237-1.12-.646a.5.5 0 1 1 .5-.866l1.12.646-.237-.883a.5.5 0 1 1 .966-.258l.495 1.849L7.5 7.134V3.207L6.147 1.854a.5.5 0 1 1 .707-.708l.646.647V.5a.5.5 0 1 1 1 0v1.293l.647-.647a.5.5 0 1 1 .707.708L8.5 3.207v3.927l3.4-1.963.496-1.85a.5.5 0 1 1 .966.26l-.236.882 1.12-.646a.5.5 0 0 1 .5.866l-1.12.646.883.237a.5.5 0 1 1-.26.966l-1.848-.495L9 8l3.4 1.963 1.849-.495a.5.5 0 0 1 .259.966l-.883.237 1.12.646a.5.5 0 0 1-.5.866l-1.12-.646.236.883a.5.5 0 1 1-.966.258l-.495-1.849-3.4-1.963v3.927l1.353 1.353a.5.5 0 0 1-.707.708l-.647-.647V15.5a.5.5 0 0 1-.5.5z"/>
          </svg>
          <span class="">Зимний декор</span>
          <ToggleSwitch v-model="decorConfig.winterDecor"/>
        </label>
      </div>

    </div>
  </Popover>

</template>
