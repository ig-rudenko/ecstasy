<template>

  <button class="rounded-2 btn btn-primary" @click="showDialog">
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-people-fill" viewBox="0 0 16 16">
      <path d="M7 14s-1 0-1-1 1-4 5-4 5 3 5 4-1 1-1 1zm4-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6m-5.784 6A2.24 2.24 0 0 1 5 13c0-1.355.68-2.75 1.936-3.72A6.3 6.3 0 0 0 5 9c-4 0-5 3-5 4s1 1 1 1zM4.5 8a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5"/>
    </svg>
  </button>

  <Dialog v-model:visible="visible" header="Статистика по портам" :style="{ width: '25rem' }">
      <span class="p-text-secondary block mb-5"></span>
      <div v-if="portStatisticData.length > 0" class="card">
          <DataTable :value="portStatisticData" >
              <template #header>
                  <div class="d-flex flex-wrap align-items-center justify-content-between gap-2">
                      <span class="text-xl text-900 font-bold">Всего подключено абонентов: {{totalCountSubscribers}}</span>
                      <svg v-if="updatePortStatisticData" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="pi-spin cursor-pointer" viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2z"/>
                        <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466"/>
                      </svg>
                      <svg v-else @click="getPortsStatistic" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="cursor-pointer" viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2z"/>
                        <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466"/>
                      </svg>
                  </div>
              </template>
              <Column field="oltPort" header="OLT порт"></Column>
              <Column field="count" header="Кол-во абонентов"></Column>
          </DataTable>
      </div>
  </Dialog>

</template>

<script lang="ts">
import {defineComponent} from 'vue';
import 'primeicons/primeicons.css';
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Dialog from "primevue/dialog";
import Button from "primevue/button";
import api_request from "../../api_request";
import {AxiosResponse} from "axios";

class PortsStatistic {
  constructor(public oltPort: string, public count: number) {}
}

export default defineComponent({
  name: "OltPortsSubscriberStatistic",
  components: {
    Column, DataTable, Dialog, Button,
  },
  props: {
    deviceName: {required: true, type: String},
  },
  data() {
      return {
          visible: false,
          updatePortStatisticData: false,
          portStatisticData: [] as PortsStatistic[],
      };
  },
  computed: {
    totalCountSubscribers(): number {
      let totalCount = 0
      for (const portStatistic of this.portStatisticData) {
        totalCount += portStatistic.count
      }
      return totalCount;
    }
  },
  methods: {
    showDialog() {
      if (this.visible) return;
      this.visible = true;
      if (this.portStatisticData.length == 0) this.getPortsStatistic();
    },
    getPortsStatistic() {
      if (this.updatePortStatisticData) return;

      this.updatePortStatisticData = true;
      api_request.get("/gpon/api/statistic/subscribers-count/" + this.deviceName)
          .then(
              (value: AxiosResponse<PortsStatistic[]>) => {
                this.portStatisticData = value.data;
                this.updatePortStatisticData = false;
              }
          )
          .catch(
              () => {
                this.updatePortStatisticData = false;
              }
          )
    },
  }
})
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
</style>