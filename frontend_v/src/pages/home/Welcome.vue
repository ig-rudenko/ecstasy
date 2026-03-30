<script setup lang="ts">
import {computed} from "vue";
import {useStore} from "vuex";

import {User} from "@/services/user";
import permissions from "@/services/permissions.ts";

const store = useStore();
const user: User | null = store.state.auth.user;

const showGPONCard = computed(() => permissions.hasGPONAnyPermission());
const showMapsCard = computed(() => permissions.has("auth.can_view_maps"));
const showTracerouteCard = computed(() => permissions.has("auth.access_traceroute"));
const showDescSearchCard = computed(() => permissions.has("auth.access_desc_search"));
const showWTFCard = computed(() => permissions.has("auth.access_wtf_search"));


const quickCards = computed(() => {
  const cards = [
    {
      key: "devices",
      title: "Устройства",
      description: "Поиск по имени и IP, фильтры, переход к карточке оборудования.",
      icon: "pi pi-box",
      to: "/devices",
      accent: "from-sky-500/15 to-cyan-500/5",
      visible: true,
    },
    {
      key: "traceroute",
      title: "Traceroute",
      description: "Топология VLAN, прохождение MAC и быстрая диагностика трассы.",
      icon: "pi pi-share-alt",
      to: "/tools/traceroute",
      accent: "from-emerald-500/15 to-teal-500/5",
      visible: showTracerouteCard.value,
    },
    {
      key: "search",
      title: "Description Search",
      description: "Поиск строки в описаниях интерфейсов и быстрый переход к порту.",
      icon: "pi pi-search",
      to: "/tools/search",
      accent: "from-amber-500/15 to-orange-500/5",
      visible: showDescSearchCard.value,
    },
    {
      key: "maps",
      title: "Карты",
      description: "Интерактивные слои, группы Zabbix и географическая навигация.",
      icon: "pi pi-map",
      to: "/maps",
      accent: "from-indigo-500/15 to-violet-500/5",
      visible: showMapsCard.value,
    },
    {
      key: "gpon",
      title: "GPON",
      description: "Абоненты, OLT/ONT, техданные и схема подключений.",
      icon: "pi pi-sitemap",
      to: "/gpon",
      accent: "from-fuchsia-500/15 to-pink-500/5",
      visible: showGPONCard.value,
    },
    {
      key: "wtf",
      title: "WTF Search",
      description: "Поиск IP/MAC по ARP-таблицам и сопоставление с Zabbix.",
      icon: "pi pi-bolt",
      to: "/tools/wtf",
      accent: "from-slate-500/15 to-sky-500/5",
      visible: showWTFCard.value,
    }
  ];

  return cards.filter((card) => card.visible);
});

</script>

<template>
  <main class="mx-auto max-w-375 px-4 py-6 sm:px-6 sm:py-10 lg:px-8">
    <section class="relative overflow-hidden rounded-4xl border border-gray-200/70 bg-white/80 shadow-[0_20px_70px_-40px_rgba(15,23,42,0.35)] backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45">
      <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(14,165,233,0.16),transparent_28%),radial-gradient(circle_at_85%_15%,rgba(99,102,241,0.16),transparent_24%),linear-gradient(135deg,rgba(255,255,255,0.3),transparent)] dark:bg-[radial-gradient(circle_at_top_left,rgba(14,165,233,0.22),transparent_28%),radial-gradient(circle_at_85%_15%,rgba(99,102,241,0.2),transparent_24%),linear-gradient(135deg,rgba(15,23,42,0.35),transparent)]" />

      <div class="relative grid gap-8 px-5 py-6 sm:px-8 sm:py-8 xl:grid-cols-[minmax(0,1.2fr),minmax(24rem,0.8fr)] xl:gap-10 xl:px-10 xl:py-10">
        <div>
          <div class="inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/75 px-4 py-2 text-xs font-semibold uppercase tracking-[0.28em] text-slate-600 dark:border-gray-700/80 dark:bg-gray-900/70 dark:text-slate-300">
            <span>Ecstasy</span>
            <span class="h-1 w-1 rounded-full bg-sky-500"></span>
            <span>network operations</span>
          </div>

          <h1 class="mt-5 max-w-4xl text-3xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-5xl">
            Единая панель управления сетью для диагностики, поиска и работы с конфигурациями.
          </h1>

          <p class="mt-4 max-w-3xl text-base leading-7 text-slate-600 dark:text-slate-300 sm:text-lg">
            Добро пожаловать, <span class="font-semibold text-slate-900 dark:text-slate-100">{{ user?.firstName || user?.username }}</span>.
            Здесь собраны устройства, инструменты диагностики, конфигурации и быстрые переходы к рабочим сценариям.
          </p>

          <div class="mt-7 flex flex-wrap items-center gap-3">
            <router-link to="/devices">
              <Button label="Открыть устройства" icon="pi pi-box" class="rounded-2xl!" />
            </router-link>
            <router-link to="/devices?search=">
              <Button label="Быстрый поиск" icon="pi pi-search" severity="secondary" outlined class="rounded-2xl!" />
            </router-link>
          </div>

          <div class="mt-8 grid gap-3 sm:grid-cols-3">
            <div class="rounded-3xl border border-white/70 bg-white/70 p-4 dark:border-gray-700/80 dark:bg-gray-900/60">
              <div class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Interfaces</div>
              <div class="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">Realtime-состояние портов, ошибки, MAC и быстрый переход к деталям.</div>
            </div>
            <div class="rounded-3xl border border-white/70 bg-white/70 p-4 dark:border-gray-700/80 dark:bg-gray-900/60">
              <div class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Commands</div>
              <div class="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">Шаблоны команд, действия пользователей и сбор конфигураций без ручной рутины.</div>
            </div>
            <div class="rounded-3xl border border-white/70 bg-white/70 p-4 dark:border-gray-700/80 dark:bg-gray-900/60">
              <div class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Topology</div>
              <div class="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">Карты, VLAN/MAC-трассы и быстрый визуальный поиск проблемных участков.</div>
            </div>
          </div>
        </div>

        <div class="flex h-full flex-col gap-4">
          <div class="rounded-[1.75rem] border border-white/70 bg-slate-950 px-5 py-5 text-white shadow-[0_30px_80px_-45px_rgba(2,6,23,0.85)] dark:border-slate-800">
            <div class="flex items-center justify-between gap-3">
              <div>
                <div class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Control panel</div>
                <div class="mt-2 text-2xl font-semibold">Операционный фокус</div>
              </div>
              <div class="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-500/15 text-sky-300">
                <i class="pi pi-wave-pulse text-xl" />
              </div>
            </div>

            <div class="mt-5 grid gap-3">
              <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div class="text-sm font-semibold text-slate-100">Устройства и интерфейсы</div>
                <div class="mt-2 text-sm leading-6 text-slate-300">Открывайте карточку оборудования и сразу переходите к портам, командам, медиа и конфигам.</div>
              </div>
              <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div class="text-sm font-semibold text-slate-100">Наблюдаемость</div>
                <div class="mt-2 text-sm leading-6 text-slate-300">Логи, карты, просмотр активности и история изменений доступны из одного интерфейса.</div>
              </div>
            </div>
          </div>

          <div class="rounded-[1.75rem] border border-gray-200/80 bg-white/75 p-5 dark:border-gray-700/80 dark:bg-gray-900/60">
            <div class="flex items-center justify-between gap-3">
              <div>
                <div class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Quick launch</div>
                <div class="mt-2 text-lg font-semibold text-slate-900 dark:text-slate-100">Быстрые точки входа</div>
              </div>
              <i class="pi pi-compass text-slate-400 dark:text-slate-500" />
            </div>

            <div class="mt-4 grid gap-3">
              <router-link
                  v-for="card in quickCards"
                  :key="card.key"
                  :to="card.to"
                  class="group relative overflow-hidden rounded-3xl border border-gray-200/80 bg-white/80 p-4 transition hover:-translate-y-0.5 hover:border-sky-300 hover:shadow-lg dark:border-gray-700/80 dark:bg-gray-950/35 dark:hover:border-sky-500"
              >
                <div :class="['absolute inset-0 bg-linear-to-br opacity-90 transition group-hover:opacity-100', card.accent]"></div>
                <div class="relative flex items-start justify-between gap-4">
                  <div class="min-w-0">
                    <div class="text-sm font-semibold text-slate-900 dark:text-slate-100">{{ card.title }}</div>
                    <div class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{{ card.description }}</div>
                  </div>
                  <div class="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/75 text-slate-700 shadow-sm dark:bg-gray-900/80 dark:text-slate-200">
                    <i :class="[card.icon, 'text-lg']" />
                  </div>
                </div>
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>
