<script setup lang="ts">
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

import {useRoute} from "vue-router";
import {ref, onMounted} from "vue";

import api from "@/services/api";
import errorFmt from "@/errorFmt";

const showNotFound = ref(false);
const errorText = ref("");

onMounted(async () => {
  const route = useRoute();
  const hostID = route.params.hostID;
  if (!hostID) {
    showNotFound.value = true;
    return;
  }

  try {
    const resp = await api.get<{ device: string }>("/api/v1/devices/by-zabbix/" + route.params.hostID);
    console.log(resp)
    location.href = "/device/" + resp.data.device;
  } catch (e: any) {
    console.log(e);
    showNotFound.value = true;
    errorText.value = errorFmt(e);
  }
})

</script>

<template>
  <Header/>

  <div class="text-center my-40">
    <div v-if="showNotFound">
      <div class="text-4xl">{{ errorText }}</div>
    </div>
    <div v-else>
      <ProgressSpinner/>
    </div>
  </div>

  <Footer/>
</template>
