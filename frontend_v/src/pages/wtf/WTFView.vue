<script lang="ts" setup>
import {ref} from "vue";

import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import macSearch, {IPMACInfoResult} from "@/services/macSearch";
import errorFmt from "@/errorFmt.ts";

const text = ref("");
const error = ref("");

interface WTFSearchResults {
  search: string;
  result: IPMACInfoResult;
}

const results = ref<WTFSearchResults[]>([]);
const running = ref(false);

async function find() {
  if (!text.value.length || running.value) return;
  running.value = true;

  if (text.value.match(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/)) {
    try {
      const value: IPMACInfoResult | null = await macSearch.getMacDetail(text.value)
      if (value) {
        results.value.unshift({search: text.value, result: value})
      }
    } catch (e: any) {
      error.value = errorFmt(e)
    }

    error.value = "";
    running.value = false;
    return;
  }

  let macAddress = text.value.replace(/[^A-Fa-f\d]/g, "");
  if (macAddress.length === 12) {
    try {
      const value = await macSearch.getMacDetail(macAddress)
      if (value) results.value.unshift({search: text.value, result: value})
    } catch (e: any) {
      error.value = errorFmt(e)
    }
    error.value = "";
    running.value = false;
    return;
  }

  error.value = "Введенное значение не является MAC-адресом или IP-адресом"
  running.value = false;
}

</script>

<template>
  <Header/>

  <div class="container mx-auto">

    <div class="flex items-center flex-col gap-4">
      <div class="text-2xl p-5">Введите MAC-адрес или IP-адрес</div>
      <Message v-if="error" severity="error" class="w-fit" closable @close="error = ''">{{ error }}</Message>
      <div>
        <InputText v-model="text" @keyup.enter="find"/>
        <Button :loading="running" @click="find" icon="pi pi-search"/>
      </div>
    </div>


    <Fieldset v-for="res in results" class="my-4" :toggleable="true">

      <template #legend="{toggleCallback}">
        <div class="cursor-pointer text-xl px-2" @click="toggleCallback">
          Результат поиска: <span class="font-mono">{{ res.search }}</span>
        </div>
      </template>

      <div class="py-3 flex flex-wrap justify-center gap-2">
        <Fieldset v-for="info in res.result.info" :toggleable="true">
          <template #legend="{toggleCallback}">
            <Button v-if="info?.device?.name" text @click="toggleCallback" :label="'Найдено на '+info.device.name"/>
          </template>

          <div class="p-2">

            <a v-for="zbx in res.result.zabbix" target="_blank" class="m-1"
               :href="res.result.zabbix_url+'/hostinventories.php?hostid='+ zbx.hostid">
              <Button :key="zbx.hostid" severity="danger" text>
                <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 64 64">
                  <path d="M0 0h64v64H0z" fill="#d31f26"/>
                  <path d="M18.8 15.382h26.393v3.424l-21.24 26.027h21.744v3.784H18.293v-3.43l21.24-26.02H18.8z"
                        fill="#fff"/>
                </svg>
                zbx.name
              </Button>
            </a>

            <div v-for="res in info.results" class="my-2 p-3 border rounded font-mono">
              <div class="flex flex-col gap-3 justify-center">
                <div>IP - {{ res.ip }}</div>
                <div>MAC - {{ res.mac }}</div>
                <div>VLAN - {{ res.vlan }}</div>
                <div v-if="res.device_name">Device - {{ res.device_name }}</div>
                <div v-if="res.port">Port - {{ res.port }}</div>
              </div>
            </div>

          </div>
        </Fieldset>
      </div>
    </Fieldset>

  </div>

  <Footer/>
</template>
