<script setup lang="ts">
import "leaflet/dist/leaflet.css";
import {onMounted, onUnmounted, ref} from "vue";
import {useRoute} from "vue-router";

import api from "@/services/api";
import {MapDetail, MapService} from "@/pages/maps/maps";

const route = useRoute();
let updateMapTimer = null as null | number;
const search = ref("");
const showSearch = ref(false);

let mapService: MapService | null = null;
const mapData = ref<MapDetail | null>(null)

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
      iframe.classList.add("h-screen", "w-screen")
      document.getElementById("map")!.appendChild(iframe);
    })
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
  <div id="map" class="h-screen w-screen"></div>
  <div v-if="showSearch" class="absolute top-5 left-14" style="z-index: 99999">
    <div class="flex items-center">
      <InputText v-model="search" placeholder="Поиск" @keydown.enter="searchElement"/>
      <Button @click="searchElement" icon="pi pi-search"/>
    </div>
  </div>
</template>
