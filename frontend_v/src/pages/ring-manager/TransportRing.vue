<template>
  <Header/>

  <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 sm:py-10">
    <div v-if="rings.selectedRing === null" class="flex flex-col gap-6">
      <div class="relative overflow-hidden rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur">
        <div class="absolute inset-0 bg-gradient-to-br from-cyan-500/10 via-transparent to-emerald-500/10 pointer-events-none"/>
        <div class="relative p-6 sm:p-8">
          <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div class="max-w-3xl">
              <h1 class="text-2xl sm:text-3xl font-semibold tracking-tight text-gray-900 dark:text-gray-100">
                Транспортные кольца
              </h1>
              <p class="mt-2 text-sm sm:text-base text-gray-600 dark:text-gray-300">
                Управление транспортными кольцами, просмотр схемы и подготовка плана разворота VLAN.
              </p>
            </div>
            <div class="font-mono text-sm text-gray-600 dark:text-gray-300">
              Всего: {{ rings.list.length || 0 }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="rings.list.length" class="grid gap-5 sm:grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
        <button
            v-for="ring in rings.list"
            :key="ring.name"
            type="button"
            class="group text-left rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 p-5 shadow-sm backdrop-blur transition hover:-translate-y-1 hover:shadow-xl"
            @click="chooseRing(ring)">
          <div class="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300">
            <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" viewBox="0 0 16 16">
              <path d="M2 1a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM0 2a2 2 0 0 1 3.937-.5h8.126A2 2 0 1 1 14.5 3.937v8.126a2 2 0 1 1-2.437 2.437H3.937A2 2 0 1 1 1.5 12.063V3.937A2 2 0 0 1 0 2zm2.5 1.937v8.126c.703.18 1.256.734 1.437 1.437h8.126a2.004 2.004 0 0 1 1.437-1.437V3.937A2.004 2.004 0 0 1 12.063 2.5H3.937A2.004 2.004 0 0 1 2.5 3.937zM14 1a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM2 13a1 1 0 1 0 0 2 1 1 0 0 0 0-2zm12 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"/>
            </svg>
          </div>

          <div class="mt-5">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ ring.name }}</h2>
            <p class="mt-3 text-sm leading-relaxed text-gray-600 dark:text-gray-300">
              {{ ring.description || "Описание отсутствует." }}
            </p>
          </div>

          <div class="mt-5 inline-flex items-center gap-2 text-sm font-medium text-emerald-600 dark:text-emerald-300">
            Открыть кольцо
            <i class="pi pi-arrow-right text-xs transition group-hover:translate-x-0.5"/>
          </div>
        </button>
      </div>

      <div v-else class="rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 px-6 py-12 text-center backdrop-blur">
        <ProgressSpinner/>
      </div>
    </div>

    <div v-else class="rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 p-4 sm:p-6 backdrop-blur">
      <RingMenu :rings="rings"/>
    </div>
  </div>

  <Footer/>
</template>

<script>
import RingMenu from "./TransportRingRotate/RingMenu.vue";
import api from "@/services/api";
import permissions from "@/services/permissions";
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

export default {
  name: "TransportRing",
  components: {Footer, Header, RingMenu},
  data() {
    return {
      rings: {
        list: [],
        selectedRing: null
      },
    }
  },

  async mounted() {
    if (!permissions.has('auth.access_transport_rings')) {
      location.href = '/';
      return
    }
    await this.getRings();
  },

  methods: {
    async getRings() {
      try {
        const resp = await api.get("/api/v1/ring-manager/transport-rings")
        this.rings.list = resp.data;
      } catch (e) {
        console.log(e);
      }
    },
    chooseRing(ringName) {
      this.rings.selectedRing = ringName;
    }
  }
}
</script>
