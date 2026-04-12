<script setup lang="ts">
import {onMounted, onUnmounted, ref} from "vue";

import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import api from "@/services/api";
import {MapBrief, MapsPage} from "@/pages/maps/maps";
import {getProtectedImage} from "@/helpers/images";

interface MapListItem extends MapBrief {
    resolvedPreviewImage: string;
}

type MapListPage = Omit<MapsPage, "results"> & {
    results: MapListItem[];
};

const maps = ref<MapListPage | null>(null);
const currentPage = ref(1);
const perPage = ref(100);

let activeRequestId = 0;
let previewUrls: string[] = [];

/**
 * Освобождает blob URL превью, созданные для текущей страницы.
 */
function cleanupPreviewUrls() {
    for (let i = 0; i < previewUrls.length; i++) {
        URL.revokeObjectURL(previewUrls[i]);
    }

    previewUrls = [];
}

/**
 * Загружает страницу карт и резолвит превью единым батчем.
 */
async function getMaps() {
    const requestId = ++activeRequestId;
    const response = await api.get<MapsPage>(`/api/v1/maps/?page=${currentPage.value}`);
    const resolvedResults = await Promise.all(
        response.data.results.map(async (map): Promise<MapListItem> => {
            const resolvedPreviewImage = await getProtectedImage(map.preview_image);
            return {
                ...map,
                resolvedPreviewImage,
            };
        }),
    );

    if (requestId !== activeRequestId) {
        for (let i = 0; i < resolvedResults.length; i++) {
            if (resolvedResults[i].resolvedPreviewImage) {
                URL.revokeObjectURL(resolvedResults[i].resolvedPreviewImage);
            }
        }

        return;
    }

    const previousPreviewUrls = previewUrls;
    previewUrls = resolvedResults
        .map((map) => map.resolvedPreviewImage)
        .filter((url) => Boolean(url));

    maps.value = {
        ...response.data,
        results: resolvedResults,
    };

    for (let i = 0; i < previousPreviewUrls.length; i++) {
        URL.revokeObjectURL(previousPreviewUrls[i]);
    }
}

/**
 * Обрабатывает переключение страницы пагинации.
 *
 * @param page - Данные новой страницы.
 */
function handlePage(page: { page: number }) {
    currentPage.value = page.page + 1;
    getMaps();
}

onMounted(() => {
    getMaps();
});

onUnmounted(() => {
    cleanupPreviewUrls();
});
</script>

<template>
  <Header />

  <div class="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-10 lg:px-8">
    <div class="flex flex-col gap-6">
      <div
        class="relative overflow-hidden rounded-3xl border border-gray-200/70 bg-white/70 backdrop-blur transition hover:-translate-y-0.5 hover:bg-linear-to-br hover:from-transparent hover:via-transparent hover:to-indigo-500/10 hover:shadow-md dark:border-gray-700/70 dark:bg-gray-900/40"
      >
        <div class="pointer-events-none absolute inset-0 bg-gradient-to-br from-cyan-500/10 via-transparent to-blue-500/10" />
        <div class="relative p-6 sm:p-8">
          <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div class="max-w-3xl">
              <h1 class="text-2xl font-semibold tracking-tight text-gray-900 sm:text-3xl dark:text-gray-100">
                Карты
              </h1>
              <p class="mt-2 text-sm text-gray-600 sm:text-base dark:text-gray-300">
                Список интерактивных и статических карт с быстрым переходом к просмотру.
              </p>
            </div>
            <div class="font-mono text-sm text-gray-600 dark:text-gray-300">
              Всего: {{ maps?.count || 0 }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="maps" class="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        <router-link
          v-for="map in maps.results"
          :key="map.id"
          :to="'/maps/' + map.id"
          class="group overflow-hidden rounded-3xl border border-gray-200/70 bg-white/70 shadow-sm backdrop-blur transition hover:-translate-y-1 hover:shadow-xl dark:border-gray-700/70 dark:bg-gray-900/40"
        >
          <div class="relative h-64 overflow-hidden">
            <div
              v-if="map.resolvedPreviewImage"
              class="h-full w-full bg-cover bg-center transition duration-500 group-hover:scale-105"
              :style="{ backgroundImage: `url(${map.resolvedPreviewImage})` }"
            />
            <svg v-else class="h-full w-full" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 255" preserveAspectRatio="none">
              <rect width="100%" height="100%" fill="#334155" />
            </svg>

            <div class="absolute inset-0 bg-linear-to-t from-gray-950/75 via-gray-950/25 to-transparent" />
            <div class="absolute left-4 top-4 flex items-center gap-2">
              <Tag v-if="map.interactive" severity="success" value="Интерактивная" />
              <Tag v-else severity="secondary" value="Статическая" />
            </div>
          </div>

          <div class="p-5">
            <div class="flex items-start justify-between gap-3">
              <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">{{ map.name }}</h2>
              <i class="pi pi-arrow-right text-sm text-gray-400 transition group-hover:translate-x-0.5 group-hover:text-indigo-500" />
            </div>
            <p class="mt-3 text-sm leading-relaxed text-gray-600 dark:text-gray-300">
              {{ map.description || "Описание отсутствует." }}
            </p>
          </div>
        </router-link>
      </div>

      <div
        v-else
        class="rounded-3xl border border-gray-200/70 bg-white/70 px-6 py-12 text-center backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/40"
      >
        <ProgressSpinner />
      </div>

      <div class="pt-1">
        <Paginator
          :always-show="false"
          :total-records="maps?.count"
          :rows="perPage"
          :pt="{
            root: { class: 'rounded-2xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur p-2' }
          }"
          @page="handlePage"
        />
      </div>
    </div>
  </div>

  <Footer />
</template>
