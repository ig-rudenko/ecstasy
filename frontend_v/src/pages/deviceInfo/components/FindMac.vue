<template>
  <Dialog v-model:visible="macSearch.dialogVisible">

    <!--      HEADER-->
    <template #header>
      <div class="flex items-center gap-2">
        <svg class="bi me-2" width="24" height="24">
          <use xlink:href="#search-icon"></use>
        </svg>
        <div class="font-mono text-xl">MAC: "<span id="modal-mac-str">{{ macSearch.lastMac }}</span>"</div>
      </div>
    </template>

    <!--      TEXT-->
    <div>
      <div id="modal-mac-content" v-if="macSearch.lastSearch" class="flex gap-2 items-center">
        <div class="flex flex-col gap-1 max-w-[30rem] font-mono">
          <div class="text-xl">Vendor: {{ macSearch.lastSearch.vendor }}</div>
          <div class="text-muted-color">Address: {{ macSearch.lastSearch.address }}</div>
        </div>
      </div>
      <ProgressSpinner v-else/>

      <div id="modal-mac-result" v-if="macSearch.lastMacDetail" class="py-3" style="text-align: center;">
        <Fieldset v-for="info in macSearch.lastMacDetail.info" :key="info.device.name" :toggleable="true">
          <template #legend="{toggleCallback}">
            <Button text @click="toggleCallback" :label="'Найдено на '+info.device.name"/>
          </template>

          <div class="p-2">

            <a v-for="zbx in macSearch.lastMacDetail.zabbix" target="_blank" class="m-1"
               :href="macSearch.lastMacDetail.zabbix_url+'/hostinventories.php?hostid='+ zbx.hostid">
              <Button :key="zbx.hostid" severity="danger" size="small" :label="zbx.name"/>
            </a>

            <div v-for="res in info.results" class="m-3 p-2 border rounded font-mono">
              <div class="flex gap-3 justify-center">
                <div>IP - {{ res.ip }}</div>
                <div>MAC - {{ res.mac }}</div>
              </div>
              <div>VLAN - {{ res.vlan }}</div>

              <div class="flex gap-3 justify-center">
                <div v-if="res.device_name">Device - {{ res.device_name }}</div>
                <div v-if="res.port">{{ res.port }}</div>
              </div>
            </div>

          </div>
        </Fieldset>
      </div>
      <ProgressSpinner v-else/>

    </div>

  </Dialog>
</template>


<script lang="ts">
import {defineComponent} from "vue";
import macSearch from "@/services/macSearch";

export default defineComponent({
  data() {
    return {
      macSearch: macSearch
    }
  },
})
</script>