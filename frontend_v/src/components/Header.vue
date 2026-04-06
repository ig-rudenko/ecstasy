<script setup lang="ts">
import {useStore} from "vuex";
import {computed, ref} from "vue";

import LogoutButton from "@/components/LogoutButton.vue";

import {getAvatar} from "@/formats";
import {User} from "@/services/user";
import permissions from "@/services/permissions";
import {getCurrentTheme, setDarkTheme, setLightTheme, ThemesValues} from "@/services/themes";
import {MenuItem} from "primevue/menuitem";
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
  if (url === "/devices") {
    return location.pathname === "/devices";
  }
  return location.pathname.startsWith(url);
}

function getMenuIconClass(icon?: string) {
  switch (icon) {
    case "devices":
      return "pi pi-box";
    case "bulk-commands":
      return "pi pi-send";
    case "console":
      return "pi pi-desktop";
    case "loop":
      return "pi pi-sync";
    case "map":
      return "pi pi-map";
    case "search":
      return "pi pi-search";
    case "topology":
      return "pi pi-share-alt";
    case "radar":
      return "pi pi-bolt";
    case "ring":
      return "pi pi-circle";
    case "gpon":
      return "pi pi-sitemap";
    default:
      return "pi pi-circle";
  }
}

function getMenuIconAccent(icon?: string) {
  switch (icon) {
    case "devices":
      return "from-sky-500/15 to-cyan-500/5";
    case "bulk-commands":
      return "from-sky-500/15 to-emerald-500/5";
    case "console":
      return "from-slate-500/15 to-slate-700/5";
    case "loop":
      return "from-emerald-500/15 to-teal-500/5";
    case "map":
      return "from-indigo-500/15 to-violet-500/5";
    case "search":
      return "from-amber-500/15 to-orange-500/5";
    case "topology":
      return "from-teal-500/15 to-sky-500/5";
    case "radar":
      return "from-slate-500/15 to-sky-500/5";
    case "ring":
      return "from-fuchsia-500/15 to-pink-500/5";
    case "gpon":
      return "from-fuchsia-500/15 to-pink-500/5";
    default:
      return "from-gray-500/15 to-gray-400/5";
  }
}

const currentTheme = ref<ThemesValues>(getCurrentTheme());

const toggle = () => {
  if (currentTheme.value == "dark" || currentTheme.value == "auto") setLightTheme();
  if (currentTheme.value == "light") setDarkTheme();
  currentTheme.value = getCurrentTheme();
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
    <div class="mx-auto px-2 sm:px-4 lg:px-8 py-2">
      <div
          class="
          relative overflow-hidden
          rounded-3xl border border-gray-200/70 dark:border-gray-700/70
          bg-white/70 dark:bg-gray-900/40
          backdrop-blur
          transition hover:-translate-y-0.5
          delay-20
          hover:shadow-md
          ">
        <div class="absolute inset-0 bg-linear-to-br from-indigo-500/10 via-transparent to-sky-500/10"/>
        <!-- Mobile header -->
        <div class="relative flex items-center justify-between gap-3 px-3 py-3 lg:hidden">
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
        <div class="hidden lg:block relative">
          <Menubar :model="menuItems.value"
                   class="relative border-none! rounded-none! bg-transparent!"
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
              <router-link to="/" class="flex items-center gap-3 text-decoration-none pr-4">
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
                    :class="isCurrent(item.url || '_')?'ring-1 ring-indigo-500/20':''"
                    class="flex items-center gap-2 rounded-2xl pl-1 pr-3 py-1">
                  <div
                      :class="getMenuIconAccent(item.icon as string)"
                      class="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-linear-to-br text-slate-700 shadow-sm dark:text-slate-200">
                    <i :class="[getMenuIconClass(item.icon as string), 'text-base']"/>
                  </div>
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

  <Drawer v-model:visible="mobileMenuOpen" position="left"
          class="w-88 max-w-[90vw]"
          :pt="{
            root: {
              class: 'border-none shadow-none! dark:bg-gray-900/55! dark:backdrop-blur-xl ' +
                  'dark:border-r dark:border-gray-700/60 bg-white/95 dark:ring-1! dark:ring-white/5!',
            },
            header: { class: 'border-b border-gray-200/70 dark:border-gray-700/70 bg-white/80 dark:bg-transparent' },
            content: { class: 'p-3 bg-transparent' }
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
          <div
              :class="getMenuIconAccent(item.icon as string)"
              class="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-linear-to-br text-slate-700 shadow-sm dark:text-slate-200">
            <i :class="[getMenuIconClass(item.icon as string), 'text-base']"/>
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">{{ item.label }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ item.url }}</div>
          </div>
          <i class="pi pi-angle-right text-gray-400"/>
        </div>
      </AppLink>
    </div>
  </Drawer>

  <Popover ref="profileRef" :pt="{
    root: {
      class: 'before:hidden! overflow-hidden rounded-2xl border-gray-100/30! ' +
          'dark:border-gray-700/60! bg-white/25 shadow-lg dark:bg-gray-900/55 backdrop-blur ',
    },
    content: { class: 'p-0!' },
  }">
    <div class="p-3">
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
                  class="hover:text-primary hover:bg-primary-100 rounded-2xl shadow-sm"/>
        </a>
        <Button icon="pi pi-moon" v-if="currentTheme == 'light'" @click="toggle"
                v-tooltip.bottom="'Включить темную тему'" severity="contrast"
                class="hover:text-gray-200 hover:bg-gray-900 rounded-2xl border-gray-300 shadow-sm"
                outlined/>
        <Button icon="pi pi-sun" v-if="currentTheme == 'dark' || currentTheme == 'auto'" @click="toggle"
                v-tooltip.bottom="'Включить светлую тему'" severity="contrast"
                class="hover:text-gray-900 hover:bg-gray-200 rounded-2xl border-gray-700 shadow-sm"
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
