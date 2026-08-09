<script setup lang="ts">
import "leaflet/dist/leaflet.css";
import { onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import api from "@/services/api";
import { getMapDetail, MapDetail, MapService } from "@/pages/maps/maps";
import { createMapViewQuery, parseMapViewQuery } from "@/pages/maps/mapViewUrl";

const route = useRoute();
const router = useRouter();
const search = ref("");
const showSearch = ref(false);
const fileMapUrl = ref("");
const mapData = ref<MapDetail | null>(null);

// Скрыто по умолчанию.
const showSearchPanel = ref(false);

let updateMapTimer: ReturnType<typeof setInterval> | null = null;
let mapService: MapService | null = null;
let isDisposed = false;
let lastMapViewQuery = "";

/**
 * Загружает HTML-карту в iframe и освобождает старый blob URL.
 *
 * @param url - URL файла карты.
 */
async function loadFileMap(url: string) {
    const response = await api.get(url, { responseType: "text" });
    const blob = new Blob([response.data], { type: "text/html" });

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

/**
 * Updates URL query parameters with the current map position without adding a history entry.
 */
function updateMapViewQuery() {
    if (!mapService) {
        return;
    }

    const center = mapService.map.getCenter();
    const mapViewQuery = createMapViewQuery({ lat: center.lat, lng: center.lng, zoom: mapService.map.getZoom() });
    const serializedQuery = JSON.stringify(mapViewQuery);

    if (serializedQuery === lastMapViewQuery) {
        return;
    }

    lastMapViewQuery = serializedQuery;
    void router.replace({
        query: {
            ...route.query,
            ...mapViewQuery,
        },
    });
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

    const initialMapView = parseMapViewQuery(route.query, mapService.map.getMinZoom(), mapService.map.getMaxZoom());
    if (initialMapView) {
        mapService.map.setView([initialMapView.lat, initialMapView.lng], initialMapView.zoom, { animate: false });
    }

    const center = mapService.map.getCenter();
    lastMapViewQuery = JSON.stringify(
        createMapViewQuery({ lat: center.lat, lng: center.lng, zoom: mapService.map.getZoom() })
    );
    mapService.map.on("moveend zoomend", updateMapViewQuery);

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
        mapService.map.off("moveend zoomend", updateMapViewQuery);
        mapService.map.remove();
    }

    mapService = null;
});
</script>

<template>
    <div class="relative h-screen w-screen overflow-hidden bg-slate-950">
        <div v-if="fileMapUrl" class="h-full w-full p-4">
            <iframe :src="fileMapUrl" class="h-full w-full rounded-4xl" />
        </div>
        <div v-else id="map" class="h-full w-full"></div>

        <div
            class="pointer-events-none absolute inset-x-0 z-500 px-16"
            :class="{ '-top-8': showSearchPanel, '-top-27 sm:-top-21': !showSearchPanel }"
        >
            <div class="mx-auto flex max-w-7xl flex-col">
                <div
                    class="pointer-events-auto w-full rounded-3xl border border-white/15 bg-slate-950/10 p-2 pt-10 text-white shadow-xl backdrop-blur-xl"
                >
                    <div
                        class="flex not-sm:flex-wrap gap-1 sm:gap-4 items-center flex-row lg:items-center lg:justify-between"
                    >
                        <div class="sm:px-4 flex not-sm:w-full not-sm:justify-between">
                            <router-link :to="'/maps'">
                                <Button class="pi pi-arrow-left" severity="contrast" rounded text size="small" />
                            </router-link>
                            <Button
                                class="pi pi-angle-up"
                                @click="showSearchPanel = !showSearchPanel"
                                severity="contrast"
                                rounded
                                text
                                size="small"
                            />
                        </div>

                        <div v-if="showSearch" class="w-full lg:min-w-[24rem] lg:w-auto">
                            <div class="flex items-center gap-2 rounded-3xl">
                                <InputText
                                    v-model="search"
                                    placeholder="Поиск по карте"
                                    class="not-sm:text-xs w-full rounded-2xl"
                                    @keydown.enter="searchElement"
                                />
                                <Button
                                    @click="searchElement"
                                    icon="pi pi-search"
                                    severity="contrast"
                                    text
                                    rounded
                                    size="small"
                                />
                            </div>
                        </div>
                    </div>
                    <div v-show="!showSearchPanel" class="flex justify-center mx-auto">
                        <i class="cursor-pointer pi pi-angle-down" @click="showSearchPanel = !showSearchPanel" />
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style>
.device-popup {
    min-width: 14rem;
    color: #111827;
    font-family: monospace;
}

.device-popup__title {
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
    font-weight: 700;
}

.device-popup__rows {
    display: grid;
    gap: 0.35rem;
}

.device-popup__row {
    display: grid;
    grid-template-columns: minmax(5.5rem, max-content) minmax(0, 1fr);
    gap: 0.75rem;
    align-items: baseline;
}

.device-popup__row span {
    color: #6b7280;
}

.device-popup__row strong {
    min-width: 0;
    overflow-wrap: anywhere;
    font-weight: 600;
}

.device-popup__link {
    display: inline-flex;
    margin-top: 0.75rem;
    color: #2563eb;
    font-weight: 600;
}

.device-popup__link:hover {
    color: #1d4ed8;
}
</style>
