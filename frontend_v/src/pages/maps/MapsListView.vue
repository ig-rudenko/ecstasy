<script setup lang="ts">
import {onMounted, ref} from "vue";

import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import api from "@/services/api";
import {MapsPage} from "@/pages/maps/maps";
import {getProtectedImage} from "@/helpers/images";

const maps = ref<MapsPage | null>(null)
const currentPage = ref(1);
const perPage = ref(100);


function getMaps() {
  api.get<MapsPage>("/api/v1/maps/?page=" + currentPage.value).then(
      response => {
        maps.value = response.data;
        maps.value.results.forEach(async (map) => {
          map.preview_image = await getProtectedImage(map.preview_image);
        });
      }
  )
}

onMounted(() => {
  getMaps()
//   const osm = tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png");
//   const map = new Map("map", {layers: [osm], minZoom: 5});
//   map.zoomControl.getContainer()?.remove()
//   map.attributionControl.getContainer()?.remove()
//   // map.addControl(new Control.Attribution());
//   map.setView([44.61, 33.5], 13)
})

</script>

<template>
  <Header/>

  <div class="container mx-auto">
    <div v-if="maps" class="grid md:grid-cols-2 xl:grid-cols-4 gap-4 py-5">
      <div v-for="map in maps.results" :key="map.id" class="">
        <div class="border rounded-xl shadow-sm h-full">

          <router-link :to="{name: 'map-view', params: {id: map.id}}">
            <div v-if="map.preview_image"
                 class="rounded-t-xl"
                 :style="{backgroundImage: 'url('+map.preview_image+')'}"
                 style="max-height: 255px; min-height: 255px; background-size: cover;"></div>
            <svg v-else class="rounded-t-xl" width="100%" height="255"
                 xmlns="http://www.w3.org/2000/svg">
              <rect width="100%" height="100%" fill="#55595c"></rect>
            </svg>
          </router-link>

          <div class="p-2">
            <div class="flex items-center justify-between">
              <div class="text-2xl">{{ map.name }}</div>
              <svg v-if="map.interactive" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="green"
                   viewBox="0 0 16 16" v-tooltip="'Данные обновляются автоматически'">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"></path>
                <path
                    d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0"></path>
              </svg>
            </div>
            <div class="p-2">{{ map.description }}</div>
          </div>
        </div>
      </div>
    </div>

    <Paginator :total-records="maps?.count" :rows="perPage" @page="p => {currentPage=p.page+1;getMaps()}"/>

  </div>

  <Footer/>
</template>
