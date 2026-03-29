<script setup lang="ts">
import "leaflet/dist/leaflet.css";
import {computed, onMounted, onUnmounted, ref} from "vue";
import {useRoute} from "vue-router";

import api from "@/services/api";
import {MapDetail, MapService} from "@/pages/maps/maps";

const route = useRoute();
let updateMapTimer = null as null | number;
const search = ref("");
const showSearch = ref(false);

let mapService: MapService | null = null;
const mapData = ref<MapDetail | null>(null)

const mapTypeLabel = computed(() => {
  if (mapData.value?.interactive) return "Интерактивная";
  if (mapData.value?.type === "file") return "HTML-карта";
  return "Карта";
});

onMounted(async () => {
  const mapId = route.params.id.toString();

  mapService = new MapService(mapId, "map");

  mapService.map.locate()
      .on("locationfound", (e) => mapService?.map.setView(e.latlng, 14))
      .on("locationerror", () => mapService?.map.setView([44.6, 33.5], 12));

  mapData.value = await mapService.getMapData();
  if (mapData.value?.type == "external") {
    const res = window.open(mapData.value.map_url,);
    if (!res) {
      location.href = mapData.value.map_url
    } else {
      history.back();
    }
    return;
  }

  if (mapData.value?.type == "file") {
    api.get(mapData.value.from_file).then(value => {
      const blob = new Blob([value.data], {type: "text/html"});
      const url = URL.createObjectURL(blob);
      const iframe = document.createElement("iframe");
      iframe.src = url;
      iframe.classList.add("h-full", "w-full", "rounded-[2rem]")
      document.getElementById("map")!.appendChild(iframe);
    })
    showSearch.value = true;
    return;
  }

  await mapService.renderMapGroups();

  if (mapData.value?.interactive) {
    mapService.renderMarkers().then(() => {
      updateMapTimer = window.setInterval(() => {
        update()
      }, 5_000)
    });
  } else {
    mapService.renderMarkers()
  }

  showSearch.value = true;
})

function update() {
  mapService?.update()
}

onUnmounted(() => {
  if (mapService) mapService.map.remove()
  mapService = null;
  if (updateMapTimer) clearTimeout(updateMapTimer);
})

function searchElement() {
  if (search.value.length < 1) return;
  mapService?.searchPoint(search.value);
}
</script>

<template>
  <div class="relative h-screen w-screen overflow-hidden bg-slate-950">
    <div id="map" class="h-full w-full"></div>

    <div class="pointer-events-none absolute inset-x-0 top-0 z-[9999] p-4 sm:p-6">
      <div class="mx-auto flex max-w-7xl flex-col gap-3">
        <div class="pointer-events-auto w-full rounded-3xl border border-white/15 bg-slate-950/70 p-4 text-white shadow-2xl backdrop-blur-xl sm:p-5">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <Button as="a" href="/maps" text severity="secondary" icon="pi pi-arrow-left" label="К списку"/>
                <Tag severity="contrast" :value="mapTypeLabel"/>
              </div>
              <div class="mt-3 text-xl font-semibold sm:text-2xl">{{ mapData?.name || "Карта" }}</div>
              <div v-if="mapData?.description" class="mt-2 max-w-3xl text-sm text-slate-200/85">
                {{ mapData.description }}
              </div>
            </div>

            <div v-if="showSearch" class="w-full lg:w-auto lg:min-w-[24rem]">
              <div class="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 p-2">
                <InputText v-model="search" placeholder="Поиск по карте" class="w-full" @keydown.enter="searchElement"/>
                <Button @click="searchElement" icon="pi pi-search"/>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
