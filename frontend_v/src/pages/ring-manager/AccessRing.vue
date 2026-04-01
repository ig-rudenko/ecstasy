<template>
  <Header/>

  <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 sm:py-10">
    <div v-if="rings.selectedRing === null" class="flex flex-col gap-6">
      <div class="relative overflow-hidden rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur">
        <div class="absolute inset-0 bg-linear-to-br from-indigo-500/10 via-transparent to-sky-500/10 pointer-events-none"/>
        <div class="relative p-6 sm:p-8">
          <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div class="max-w-3xl">
              <h1 class="text-2xl sm:text-3xl font-semibold tracking-tight text-gray-900 dark:text-gray-100">
                Абонентские кольца
              </h1>
              <p class="mt-2 text-sm sm:text-base text-gray-600 dark:text-gray-300">
                Список доступных колец доступа с быстрым поиском и выделением проблемных разворотов.
              </p>
            </div>
            <div class="font-mono text-sm text-gray-600 dark:text-gray-300">
              Доступно: {{ filteredRings.length || 0 }}
            </div>
          </div>
        </div>
      </div>

      <div class="rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur p-4 sm:p-6">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div class="flex-1">
            <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Поиск</div>
            <InputText class="w-full rounded-2xl" placeholder="Введите имя головного узла" v-model.trim="search"/>
          </div>

          <label class="cursor-pointer flex items-center gap-3 rounded-2xl border border-gray-200/70 dark:border-gray-700/70 px-4 py-3 text-sm text-gray-700 dark:text-gray-200">
            <Checkbox class="form-check-input" v-model="onlyNonNormal" binary input-id="onlyNonNormal"/>
            Показывать только неверно развернутые
          </label>
        </div>
      </div>

      <div v-if="rings.list.length" class="grid gap-5 sm:grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
        <button
            v-for="ring in filteredRings"
            :key="`${ring.head_name}-${ring.ports}`"
            type="button"
            class="group text-left rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 p-5 shadow-sm backdrop-blur transition hover:-translate-y-1 hover:shadow-xl"
            @click="chooseRing(ring)">
          <div class="flex items-start justify-between gap-4">
            <div class="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-100 text-indigo-600 dark:bg-indigo-500/15 dark:text-indigo-300">
              <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" viewBox="0 0 16 16">
                <path d="M2 1a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM0 2a2 2 0 0 1 3.937-.5h8.126A2 2 0 1 1 14.5 3.937v8.126a2 2 0 1 1-2.437 2.437H3.937A2 2 0 1 1 1.5 12.063V3.937A2 2 0 0 1 0 2zm2.5 1.937v8.126c.703.18 1.256.734 1.437 1.437h8.126a2.004 2.004 0 0 1 1.437-1.437V3.937A2.004 2.004 0 0 1 12.063 2.5H3.937A2.004 2.004 0 0 1 2.5 3.937zM14 1a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM2 13a1 1 0 1 0 0 2 1 1 0 0 0 0-2zm12 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"/>
              </svg>
            </div>

            <Badge v-if="!ring.is_normal_rotate_status" severity="warn">Требует внимания</Badge>
          </div>

          <div class="mt-5">
            <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {{ ring.head_name }}
            </div>
            <div class="mt-1 font-mono text-sm text-gray-500 dark:text-gray-400">
              {{ ring.ports }}
            </div>
          </div>

          <p class="mt-4 text-sm leading-relaxed text-gray-600 dark:text-gray-300">
            {{ ring.description || "Описание отсутствует." }}
          </p>

          <div class="mt-5 inline-flex items-center gap-2 text-sm font-medium text-indigo-600 dark:text-indigo-300">
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
      <AccessRingMenu :rings="rings"/>
    </div>
  </div>

  <Footer/>
</template>

<script>
import AccessRingMenu from "./AccessRings/AccessRingMenu.vue";
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import permissions from "@/services/permissions.ts";
import api from "@/services/api";

export default {
  name: "AccessRing",
  components: {Footer, Header, AccessRingMenu},
  data() {
    return {
      rings: {
        list: [],
        selectedRing: null,
      },
      search: "",
      onlyNonNormal: false,
    }
  },

  async mounted() {
    if (!permissions.has('auth.access_rings')) {
      location.href = '/';
      return;
    }
    await this.getRings();
  },

  computed: {
    filteredRings() {
      const search = this.search.toLowerCase()
      const onlyNonNormal = this.onlyNonNormal
      return Array.from(this.rings.list).filter(
          (ring) => {
            const validByName = search.length < 3 || ring.head_name.toLowerCase().indexOf(search) > -1
            const validByStatus = onlyNonNormal && !ring.is_normal_rotate_status || !onlyNonNormal
            return validByName && validByStatus;
          }
      )
    }
  },

  methods: {
    async getRings() {
      try {
        const resp = await api.get("/api/v1/ring-manager/access-rings");
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
