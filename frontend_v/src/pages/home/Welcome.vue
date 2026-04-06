<script setup lang="ts">
import {computed} from "vue";
import {useStore} from "vuex";

import {User} from "@/services/user";
import permissions from "@/services/permissions.ts";

type ModuleCard = {
  key: string;
  title: string;
  description: string;
  features: string[];
  icon: string;
  to: string;
  accent: string;
  visible: boolean;
};


const store = useStore();
const user: User | null = store.state.auth.user;

const showGPONCard = computed(() => permissions.hasGPONAnyPermission());
const showMapsCard = computed(() => permissions.has("auth.can_view_maps"));
const showTracerouteCard = computed(() => permissions.has("auth.access_traceroute"));
const showDescSearchCard = computed(() => permissions.has("auth.access_desc_search"));
const showWTFCard = computed(() => permissions.has("auth.access_wtf_search"));

const modules = computed<ModuleCard[]>(() => {
  const cards: ModuleCard[] = [
    {
      key: "devices",
      title: "Работа с оборудованием",
      description: "Основной раздел для повседневной эксплуатации сети и просмотра состояния узлов без ручного ввода CLI-команд.",
      features: [
        "Интерфейсы в реальном времени",
        "Сбор и хранение конфигураций",
        "Шаблоны команд и действия с портами",
        "Ошибки, MAC-адреса, логи и сессии",
      ],
      icon: "pi pi-box",
      to: "/devices",
      accent: "from-sky-500/15 via-cyan-500/10 to-blue-500/5",
      visible: true,
    },
    {
      key: "traceroute",
      title: "Топология VLAN и MAC",
      description: "Инструменты для определения маршрута трафика и поиска проблемного участка между сетевыми устройствами.",
      features: [
        "Построение топологии VLAN",
        "Определение прохождения MAC-адреса",
        "Быстрая локализация участка сети",
      ],
      icon: "pi pi-share-alt",
      to: "/tools/traceroute",
      accent: "from-emerald-500/15 via-teal-500/10 to-lime-500/5",
      visible: showTracerouteCard.value,
    },
    {
      key: "search",
      title: "Поиск по описаниям",
      description: "Поиск интерфейсов по текстовому описанию порта, линии, клиента или служебной пометке.",
      features: [
        "Поиск по описанию интерфейса",
        "Быстрый переход к нужному порту",
        "Ускорение диагностики и инвентаризации",
      ],
      icon: "pi pi-search",
      to: "/tools/search",
      accent: "from-amber-500/15 via-orange-500/10 to-red-500/5",
      visible: showDescSearchCard.value,
    },
    {
      key: "wtf",
      title: "Поиск IP и MAC",
      description: "Поиск сетевых данных по ARP-таблицам и сопоставление результатов с информацией из Zabbix.",
      features: [
        "Поиск IP/MAC по сети",
        "Сопоставление с Zabbix",
        "Выход на нужное устройство и интерфейс",
      ],
      icon: "pi pi-bolt",
      to: "/tools/wtf",
      accent: "from-slate-500/15 via-sky-500/10 to-cyan-500/5",
      visible: showWTFCard.value,
    },
    {
      key: "maps",
      title: "Интерактивные карты",
      description: "Визуализация сети через внешние карты, HTML-карты и слои на основе Zabbix-групп или GeoJSON.",
      features: [
        "Карты по внешней ссылке или HTML",
        "Слои из Zabbix-групп и GeoJSON",
        "Отображение доступности оборудования",
      ],
      icon: "pi pi-map",
      to: "/maps",
      accent: "from-indigo-500/15 via-blue-500/10 to-violet-500/5",
      visible: showMapsCard.value,
    },
    {
      key: "gpon",
      title: "GPON и абоненты",
      description: "База GPON-подключений с техническими данными, адресной информацией, OLT/ONT и связью с абонентами.",
      features: [
        "Технические данные GPON",
        "OLT, ONT, адреса и подключения",
        "База пользователей и сервисов",
      ],
      icon: "pi pi-sitemap",
      to: "/gpon",
      accent: "from-fuchsia-500/15 via-pink-500/10 to-rose-500/5",
      visible: showGPONCard.value,
    },
  ];

  return cards.filter((card) => card.visible);
});

const extraCapabilities = [
  "Веб-консоль для подключения к оборудованию через браузер",
  "Учёт загруженности оборудования и интерфейсов",
  "Сохранение конфигураций и медиафайлов устройств",
  "Импорт узлов сети из Zabbix через management command",
];

const supportedVendors = [
  "Cisco",
  "Eltex",
  "MikroTik",
  "Huawei",
  "Huawei DSL / GPON",
  "Iskratel DSL",
  "D-Link",
  "Extreme",
  "ZTE",
  "Q-Tech",
];

const userDisplayName = computed(() => user?.firstName || user?.username || "оператор");
</script>

<template>
  <main class="mx-auto max-w-375 px-2 py-6 sm:px-6 sm:py-10 lg:px-8">
    <section
        class="relative overflow-hidden rounded-4xl border border-gray-200/70 bg-white/80 shadow-[0_24px_80px_-48px_rgba(15,23,42,0.42)] backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45">
      <div
          class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(14,165,233,0.18),transparent_26%),radial-gradient(circle_at_82%_18%,rgba(59,130,246,0.14),transparent_24%),radial-gradient(circle_at_72%_78%,rgba(45,212,191,0.14),transparent_22%),linear-gradient(135deg,rgba(255,255,255,0.38),transparent)] dark:bg-[radial-gradient(circle_at_top_left,rgba(14,165,233,0.22),transparent_28%),radial-gradient(circle_at_82%_18%,rgba(59,130,246,0.18),transparent_24%),radial-gradient(circle_at_72%_78%,rgba(45,212,191,0.16),transparent_22%),linear-gradient(135deg,rgba(15,23,42,0.4),transparent)]"/>

      <div class="relative px-5 py-6 sm:px-8 sm:py-8 xl:px-10 xl:py-10">
        <section class="grid gap-6 xl:grid-cols-[minmax(0,1.2fr),22rem] xl:items-start">
          <div>

            <div class="mt-5 max-w-5xl text-3xl font-semibold tracking-wide text-slate-950 dark:text-white sm:text-5xl">
              <span class="block text-3xl sm:text-6xl">Ecstasy</span>
              <span class="mt-3 block text-balance text-xl leading-tight sm:text-3xl">
                Веб-приложение для взаимодействия с сетевым оборудованием и диагностики сети
              </span>
            </div>

            <p class="mt-5 max-w-4xl text-base leading-7 text-slate-600 dark:text-slate-300 sm:text-lg">
              <span class="font-semibold text-slate-900 dark:text-slate-100">{{ userDisplayName }}</span>,
              на этой странице собрана краткая информация о проекте: из каких функциональных блоков он состоит, какие
              задачи
              решает и какие инструменты доступны для повседневной эксплуатации сети.
            </p>

            <div class="mt-6 flex flex-wrap items-center gap-3">
              <router-link to="/devices">
                <Button label="Перейти к оборудованию" icon="pi pi-server" text class="rounded-2xl hover:shadow-sm"/>
              </router-link>
              <router-link to="/maps" v-if="showMapsCard">
                <Button label="Открыть карты" icon="pi pi-map" severity="secondary" text class="rounded-2xl hover:shadow-sm"/>
              </router-link>
            </div>
          </div>

        </section>

        <section class="mt-8">
          <div class="flex items-center justify-between gap-4">
            <div>
              <div class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
                Компоненты
              </div>
              <div class="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">Что есть в проекте</div>
            </div>
            <div
                class="hidden hover:shadow-md rounded-full border border-gray-200/80 bg-white/75 px-4 py-2 text-sm text-slate-500 dark:border-gray-700/80 dark:bg-gray-900/45 dark:text-slate-300 sm:inline-flex">
              Каждый блок описывает отдельный функциональный контур
            </div>
          </div>

          <div class="mt-5 grid gap-4 xl:grid-cols-2">
            <router-link
                v-for="module in modules"
                :key="module.key"
                :to="module.to"
                class="group relative overflow-hidden rounded-3xl border border-gray-200/80 bg-white/80 p-5 transition duration-200 hover:-translate-y-0.5  hover:shadow-md dark:border-gray-700/80 dark:bg-gray-950/35 "
            >
              <div
                  :class="['absolute inset-0 bg-linear-to-br opacity-90 transition group-hover:opacity-100', module.accent]"/>
              <div class="relative">
                <div class="flex items-start justify-between gap-4">
                  <div class="min-w-0">
                    <div class="text-xl font-semibold text-slate-900 dark:text-slate-100">{{ module.title }}</div>
                    <div class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{{
                        module.description
                      }}
                    </div>
                  </div>
                  <div
                      class="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/85 text-slate-700 shadow-sm dark:bg-gray-900/80 dark:text-slate-200">
                    <i :class="[module.icon, 'text-xl']"/>
                  </div>
                </div>

                <div class="mt-5 grid gap-2">
                  <div
                      v-for="feature in module.features"
                      :key="feature"
                      class="rounded-2xl border border-gray-200/70 bg-white/85 px-4 py-3 text-sm leading-6 text-slate-700 dark:border-gray-700/70 dark:bg-gray-900/55 dark:text-slate-200"
                  >
                    {{ feature }}
                  </div>
                </div>
              </div>
            </router-link>
          </div>
        </section>

        <section class="mt-8 grid gap-4 xl:grid-cols-[minmax(0,1.05fr),minmax(22rem,0.95fr)]">
          <div
              class="rounded-[1.9rem] border border-gray-200/80 bg-white/75 p-5 dark:border-gray-700/80 dark:bg-gray-900/60">
            <div class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
              Дополнительно
            </div>
            <div class="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">Другие возможности проекта</div>

            <div class="mt-5 grid gap-3">
              <div
                  v-for="capability in extraCapabilities"
                  :key="capability"
                  class="rounded-3xl border border-gray-200/70 bg-white/85 p-4 text-sm leading-6 text-slate-700 dark:border-gray-700/70 dark:bg-gray-950/35 dark:text-slate-200"
              >
                {{ capability }}
              </div>
            </div>
          </div>

          <div
              class="rounded-[1.9rem] border border-gray-200/80 bg-white/75 p-5 dark:border-gray-700/80 dark:bg-gray-900/60">
            <div class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
              Поддерживаемые вендоры
            </div>
            <div class="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">С какими устройствами работает
              Ecstasy
            </div>

            <div class="mt-5 flex flex-wrap gap-2.5">
              <span
                  v-for="vendor in supportedVendors"
                  :key="vendor"
                  class="rounded-full border border-gray-200/80 bg-white/85 px-3 py-2 text-sm font-medium text-slate-700 dark:border-gray-700/70 dark:bg-gray-950/35 dark:text-slate-200"
              >
                {{ vendor }}
              </span>
            </div>
          </div>
        </section>
      </div>
    </section>
  </main>
</template>
