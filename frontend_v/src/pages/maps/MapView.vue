<script setup lang="ts">
import "leaflet/dist/leaflet.css";
import {computed, onMounted, onUnmounted, ref} from "vue";
import {useRoute} from "vue-router";

import api from "@/services/api";
import {getMapDetail, MapDetail, MapService} from "@/pages/maps/maps";

const route = useRoute();
const search = ref("");
const showSearch = ref(false);
const fileMapUrl = ref("");
const mapData = ref<MapDetail | null>(null);

let updateMapTimer: ReturnType<typeof setInterval> | null = null;
let mapService: MapService | null = null;
let isDisposed = false;

const mapTypeLabel = computed(() => {
    if (mapData.value?.interactive) {
        return "Интерактивная";
    }

    if (mapData.value?.type === "file") {
        return "HTML-карта";
    }

    return "Карта";
});

/**
 * Загружает HTML-карту в iframe и освобождает старый blob URL.
 *
 * @param url - URL файла карты.
 */
async function loadFileMap(url: string) {
    const response = await api.get(url, {responseType: "text"});
    const blob = new Blob([response.data], {type: "text/html"});

    if (fileMapUrl.value) {
        URL.revokeObjectURL(fileMapUrl.value);
    }

    fileMapUrl.value = URL.createObjectURL(blob);
}

/**
 * Выполняет обновление состояния маркеров.
 */
function update() {
    mapService?.update();
}

/**
 * Выполняет поиск элемента на карте.
 */
function searchElement() {
    if (search.value.length < 1) {
        return;
    }

    mapService?.searchPoint(search.value);
}

onMounted(async () => {
    const mapId = route.params.id.toString();
    const detail = await getMapDetail(mapId);

    if (isDisposed || !detail) {
        return;
    }

    mapData.value = detail;

    if (detail.type === "external") {
        const popup = window.open(detail.map_url);

        if (!popup) {
            location.href = detail.map_url;
        } else {
            history.back();
        }

        return;
    }

    if (detail.type === "file") {
        await loadFileMap(detail.from_file);
        return;
    }

    mapService = new MapService(mapId, "map");
    await mapService.renderMapGroups();
    await mapService.renderMarkers();

    if (isDisposed) {
        return;
    }

    if (detail.interactive) {
        await mapService.update();
        updateMapTimer = setInterval(update, 5_000);
    }

    showSearch.value = true;
});

onUnmounted(() => {
    isDisposed = true;

    if (updateMapTimer) {
        clearInterval(updateMapTimer);
    }

    if (fileMapUrl.value) {
        URL.revokeObjectURL(fileMapUrl.value);
        fileMapUrl.value = "";
    }

    if (mapService) {
        mapService.map.remove();
    }

    mapService = null;
});
</script>

<template>
  <div class="relative h-screen w-screen overflow-hidden bg-slate-950">
    <div v-if="fileMapUrl" class="h-full w-full p-4">
      <iframe :src="fileMapUrl" class="h-full w-full rounded-[2rem]" />
    </div>
    <div v-else id="map" class="h-full w-full"></div>

    <div class="pointer-events-none absolute inset-x-0 -top-8 z-9999">
      <div class="mx-auto flex max-w-7xl flex-col">
        <div
          class="pointer-events-auto w-full rounded-3xl border border-white/15 bg-slate-950/10 p-2 pt-10 text-white shadow-xl backdrop-blur-xl"
        >
          <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div class="min-w-0 px-4">
              <div class="flex flex-wrap items-center justify-center gap-2">
                <router-link :to="'/maps'" class="flex items-center gap-2">
                  <i class="pi pi-arrow-left text-xs" />
                  <span>К списку</span>
                </router-link>
                <Tag severity="contrast" :value="mapTypeLabel" />
              </div>
              <div class="font-semibold">{{ mapData?.name || "Карта" }}</div>
            </div>

            <div v-if="showSearch" class="w-full lg:min-w-[24rem] lg:w-auto">
              <div class="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 p-2">
                <InputText
                  v-model="search"
                  placeholder="Поиск по карте"
                  class="w-full"
                  @keydown.enter="searchElement"
                />
                <Button @click="searchElement" icon="pi pi-search" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
