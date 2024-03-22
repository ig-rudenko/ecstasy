<template>

  <Button class="rounded-2" size="large" icon="pi pi-users" severity="primary" outlined rounded @click="showDialog" />

  <Dialog v-model:visible="visible" header="Статистика по портам" :style="{ width: '25rem' }">
      <span class="p-text-secondary block mb-5"></span>
      <div v-if="portStatisticData.length > 0" class="card">
          <DataTable :value="portStatisticData" >
              <template #header>
                  <div class="d-flex flex-wrap align-items-center justify-content-between gap-2">
                      <span class="text-xl text-900 font-bold">Всего подключено абонентов: {{totalCountSubscribers}}</span>
                      <i v-if="updatePortStatisticData" class="pi pi-spin pi-spinner"/>
                      <i v-else class="pi pi-refresh cursor-pointer" @click="getPortsStatistic" />
                  </div>
              </template>
              <Column field="oltPort" header="OLT порт"></Column>
              <Column field="count" header="Кол-во абонентов"></Column>
          </DataTable>
      </div>
  </Dialog>

</template>

<script lang="ts">
import {defineComponent} from 'vue'
import 'primeicons/primeicons.css'
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