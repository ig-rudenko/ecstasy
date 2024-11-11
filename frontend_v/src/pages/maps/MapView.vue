<script setup lang="ts">
import "leaflet/dist/leaflet.css";
import {onMounted, onUnmounted, ref} from "vue";
import {useRoute} from "vue-router";

import {MapDetail, MapService} from "@/pages/maps/maps";
import api from "@/services/api";

const route = useRoute();
const mapId = route.params.id.toString();

let mapService: MapService | null = null;
const mapData = ref<MapDetail | null>(null)

onMounted(async () => {

  mapService = new MapService(mapId, "map");
  mapData.value = await mapService.getMapData();

  if (mapData.value?.type == "external") {
    open(mapData.value.map_url, "_blank");
    history.back();
    return;
  }

  if (mapData.value?.type == "file") {
    api.get(mapData.value.from_file).then(value => {
      const getBlobURL = (code: string, type: string) => {
        const blob = new Blob([code], {type});
        return URL.createObjectURL(blob);
      };
      const url = getBlobURL(value.data, 'text/html');
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
      mapService?.startUpdate()
    });
  } else {
    mapService.renderMarkers()
  }

  mapService.map.locate()
      .on("locationfound", (e) => mapService?.map.setView(e.latlng, 14))
      .on("locationerror", () => mapService?.map.setView([44.6, 33.5], 12));

})

onUnmounted(() => {
  mapService?.stopUpdate();
})

</script>

<template>
  <div id="map" class="h-screen w-screen"></div>
</template>
