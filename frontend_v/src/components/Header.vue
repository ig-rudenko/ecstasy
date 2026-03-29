<script setup lang="ts">
import {useStore} from "vuex";
import {computed, ref} from "vue";

import LogoutButton from "@/components/LogoutButton.vue";

import {getAvatar} from "@/formats";
import {User} from "@/services/user";
import permissions from "@/services/permissions";
import {getCurrentTheme, setDarkTheme, setLightTheme, ThemesValues} from "@/services/themes";
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

function buildMenuItems(): MenuItem[] {
  const built: MenuItem[] = [
    {
      label: 'Оборудование',
      icon: 'devices',
      url: "/devices",
    }
  ];

  if (permissions.hasConsoleAccess()) {
    built.push({
      label: 'Консоль',
      icon: 'console',
      url: permissions.getConsoleUrl() || "#",
      newPage: true,
    })
  }

  if (permissions.hasEcstasyLoopPermission()) {
    built.push({
      label: 'Loop Detector',
      icon: 'loop',
      url: permissions.getEcstasyLoopUrl() || "#",
      newPage: true,
    })
  }

  if (permissions.has("auth.can_view_maps")) {
    built.push({
      label: 'Карты',
      icon: 'map',
      url: '/maps',
    })
  }

  if (permissions.has("auth.access_desc_search")) {
    built.push({
      label: 'Поиск',
      icon: 'search',
      url: '/tools/search',
    })
  }

  if (permissions.has("auth.access_traceroute")) {
    built.push({
      label: 'Трассировка',
      icon: 'topology',
      url: '/tools/traceroute',
    })
  }

  if (permissions.has("auth.access_wtf_search")) {
    built.push({
      label: 'WTF',
      icon: 'radar',
      url: '/tools/wtf'
    })
  }

  if (permissions.has("auth.access_rings") || permissions.has("auth.access_transport_rings")) {
    built.push({
      label: 'Кольца',
      icon: 'ring',
      url: '/ring-manager'
    })
  }

  if (permissions.hasGPONAnyPermission()) {
    built.push({
      label: 'GPON',
      icon: 'gpon',
      url: '/gpon',
    })
  }

  return built;
}

const menuItems = computed(() => {
  items.value = buildMenuItems();
  return items;
});

function isCurrent(url: string) {
  return location.pathname.startsWith(url);
}

const currentTheme = ref<ThemesValues>(getCurrentTheme());

const toggle = () => {
  if (currentTheme.value == "dark" || currentTheme.value == "auto") setLightTheme();
  if (currentTheme.value == "light") setDarkTheme();
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

const mobileMenuOpen = ref(false);
const closeMobileMenu = () => {
  mobileMenuOpen.value = false;
}

</script>

<template>
  <div class="sticky top-0 z-30">
    <div class="mx-auto max-w-7xl px-2 sm:px-4 lg:px-8 py-2">
      <div
          class="relative overflow-hidden rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur">
        <div class="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-transparent to-sky-500/10"/>
        <!-- Mobile header -->
        <div class="relative flex items-center justify-between gap-3 px-3 py-3 sm:hidden">
          <router-link to="/" class="flex items-center gap-3" @click="closeMobileMenu">
            <img class="w-10 h-10 rounded-full" src="/video/logo.webp" alt="logo">
            <div>
              <div style="font-family: 'Century Gothic', fantasy;" class="text-gray-900 dark:text-gray-100 text-xl leading-none">
                Ecstasy
              </div>
              <div class="text-[11px] text-gray-500 dark:text-gray-400">Network equipment control</div>
            </div>
          </router-link>

          <div class="flex items-center gap-2">
            <Button icon="pi pi-bars" severity="secondary" outlined size="small"
                    v-tooltip.bottom="'Меню'" @click="mobileMenuOpen = true"/>
            <Avatar v-if="user" :image="getAvatar(user.username)" class="cursor-pointer"
                    @click="toggleProfile" size="large"/>
          </div>
        </div>

        <!-- Desktop header -->
        <div class="hidden sm:block relative">
          <Menubar :model="menuItems.value"
                   class="relative !border-none !rounded-none !bg-transparent"
                   :pt="{
                      root: {class: 'px-2 sm:px-4 py-2 !bg-transparent'},
                      start: {class: 'flex items-center gap-3'},
                      end: {class: 'flex items-center'},
                      menu: {class: 'gap-1'},
                      item: {class: 'rounded-2xl'},
                      itemContent: {class: '!bg-transparent rounded-2xl hover:!bg-white/70 dark:hover:!bg-gray-900/50 transition'},
                      itemLink: {class: 'px-3 py-2'},
                    }">
            <template #start>
              <router-link to="/" class="flex items-center gap-3 text-decoration-none">
                <img class="w-10 h-10 sm:w-12 sm:h-12 rounded-full" src="/video/logo.webp" alt="logo">
                <div class="hidden sm:block">
                  <div style="font-family: 'Century Gothic', fantasy;"
                       class="text-gray-900 dark:text-gray-100 text-xl sm:text-2xl leading-none">
                    Ecstasy
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">
                    Network equipment control
                  </div>
                </div>
              </router-link>
            </template>

            <template #item="{ item }">
              <AppLink :to="item.url || ''" :target="item.newPage?'_blank':''">
                <div
                    :class="isCurrent(item.url || '_')?'ring-2 ring-indigo-500/50':''"
                    class="flex items-center gap-2 rounded-2xl px-3 py-2">
                  <img :src="'/img/menu/'+item.icon+'.png'" class="w-7 h-7 opacity-90" :alt="item.icon"/>
                  <span class="text-sm font-medium text-gray-800 dark:text-gray-200 whitespace-nowrap">{{ item.label }}</span>
                </div>
              </AppLink>
            </template>

            <template #end>
              <div class="flex items-center gap-2">
                <Avatar v-if="user" :image="getAvatar(user.username)" class="cursor-pointer"
                        @click="toggleProfile" size="large"/>
              </div>
            </template>
          </Menubar>
        </div>
      </div>
    </div>
  </div>

  <div class="md:sticky top-0 z-10 w-fit backdrop-blur-sm rounded-md">
    <div>
      <Button v-if="showDevicePinned()" type="button" icon="pi pi-box" label="Закреплённое оборудование" outlined text
              size="small" @click="togglePinedDevices"/>
    </div>
  </div>

  <Popover ref="pinnedDevicesRef" class="p-1">
    <div
        class="pb-2 mb-2 flex w-full justify-between items-center gap-2 border-b-[1px] border-gray-200 dark:border-gray-700">
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

  <Drawer v-model:visible="mobileMenuOpen" position="left"
          class="w-[22rem] max-w-[90vw]"
          :pt="{
            root: { class: 'border-none' },
            header: { class: 'border-b border-gray-200/70 dark:border-gray-700/70' },
            content: { class: 'p-3' }
          }">
    <template #header>
      <div class="flex items-center gap-3">
        <img class="w-10 h-10 rounded-full" src="/video/logo.webp" alt="logo">
        <div>
          <div class="font-semibold text-gray-900 dark:text-gray-100">Меню</div>
          <div class="text-xs text-gray-500 dark:text-gray-400">быстрые переходы</div>
        </div>
      </div>
    </template>

    <div class="flex flex-col gap-2">
      <AppLink v-for="item in menuItems.value" :key="item.url || item.label"
               :to="item.url || ''" :target="item.newPage?'_blank':''"
               @click="closeMobileMenu">
        <div
            :class="isCurrent(item.url || '_')?'ring-2 ring-indigo-500/50 bg-white/70 dark:bg-gray-900/40':''"
            class="flex items-center gap-3 rounded-2xl px-3 py-2 hover:bg-white/70 dark:hover:bg-gray-900/40 transition">
          <img :src="'/img/menu/'+item.icon+'.png'" class="w-8 h-8 opacity-90" :alt="item.icon"/>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">{{ item.label }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ item.url }}</div>
          </div>
          <i class="pi pi-angle-right text-gray-400"/>
        </div>
      </AppLink>
    </div>
  </Drawer>

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
          <Button icon="pi pi-cog" outlined v-tooltip.bottom="'Панель администратора'" severity="secondary"
                  class="hover:text-primary hover:bg-primary-100"/>
        </a>
        <Button icon="pi pi-moon" v-if="currentTheme == 'light'" @click="toggle"
                v-tooltip.bottom="'Включить темную тему'" severity="contrast"
                class="hover:text-gray-200 hover:bg-gray-900"
                outlined/>
        <Button icon="pi pi-sun" v-if="currentTheme == 'dark' || currentTheme == 'auto'" @click="toggle"
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
