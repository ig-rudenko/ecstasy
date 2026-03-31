<script setup lang="ts">
import permissions from "@/services/permissions";
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

const cards = [
  {
    key: "transport",
    title: "Транспортные кольца",
    description: "Кольца агрегации, используются для разворота VLAN и контроля состояния магистрали.",
    route: "/ring-manager/transport-ring",
    permission: "auth.access_transport_rings",
    image: "/img/ring_manager/background/transport_ring.jpg",
  },
  {
    key: "access",
    title: "Абонентские кольца",
    description: "Оборудование доступа с кольцевой топологией и быстрым переходом к диагностике.",
    route: "/ring-manager/access-ring",
    permission: "auth.access_rings",
    image: "/img/ring_manager/background/access_ring.jpg",
  },
];
</script>

<template>
  <Header/>

  <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 sm:py-10">
    <div class="flex flex-col gap-6">
      <div class="
          relative overflow-hidden
          rounded-3xl border border-gray-200/70 dark:border-gray-700/70
          bg-white/70 dark:bg-gray-900/40
          backdrop-blur
          transition hover:-translate-y-0.5
          delay-0
          hover:bg-linear-to-br hover:from-transparent hover:via-transparent hover:to-indigo-500/10 hover:shadow-md
        ">
        <div class="absolute inset-0 bg-gradient-to-br from-emerald-500/10 via-transparent to-sky-500/10 pointer-events-none"/>
        <div class="relative p-6 sm:p-8">
          <div class="max-w-3xl">
            <h1 class="text-2xl sm:text-3xl font-semibold tracking-tight text-gray-900 dark:text-gray-100">
              Менеджер колец
            </h1>
            <p class="mt-2 text-sm sm:text-base text-gray-600 dark:text-gray-300">
              Выберите раздел для просмотра топологии, проверки состояния и выполнения операций по кольцам.
            </p>
          </div>
        </div>
      </div>

      <div class="grid gap-6 md:grid-cols-2">
        <router-link
            v-for="card in cards.filter(card => permissions.has(card.permission))"
            :key="card.key"
            :to="card.route"
            class="group relative overflow-hidden rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 shadow-sm transition hover:-translate-y-1 hover:shadow-xl">
          <div class="absolute inset-0">
            <div class="h-full w-full bg-cover bg-center transition duration-500 group-hover:scale-105"
                 :style="{ backgroundImage: `url('${card.image}')` }"/>
            <div class="absolute inset-0 bg-gradient-to-t from-gray-950/85 via-gray-950/35 to-gray-950/5"/>
          </div>

          <div class="relative flex min-h-[22rem] flex-col justify-end p-6 sm:p-8">
            <div class="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl border border-white/20 bg-white/10 text-white backdrop-blur">
              <svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" fill="currentColor" viewBox="0 0 16 16">
                <path d="M2 1a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM0 2a2 2 0 0 1 3.937-.5h8.126A2 2 0 1 1 14.5 3.937v8.126a2 2 0 1 1-2.437 2.437H3.937A2 2 0 1 1 1.5 12.063V3.937A2 2 0 0 1 0 2zm2.5 1.937v8.126c.703.18 1.256.734 1.437 1.437h8.126a2.004 2.004 0 0 1 1.437-1.437V3.937A2.004 2.004 0 0 1 12.063 2.5H3.937A2.004 2.004 0 0 1 2.5 3.937zM14 1a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM2 13a1 1 0 1 0 0 2 1 1 0 0 0 0-2zm12 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"/>
              </svg>
            </div>
            <h2 class="text-2xl font-semibold text-white">{{ card.title }}</h2>
            <p class="mt-3 max-w-xl text-sm sm:text-base text-gray-200">
              {{ card.description }}
            </p>
            <div class="mt-5 inline-flex items-center gap-2 text-sm font-medium text-emerald-200">
              Открыть раздел
              <i class="pi pi-arrow-right text-xs"/>
            </div>
          </div>
        </router-link>
      </div>
    </div>
  </div>

  <Footer/>
</template>
