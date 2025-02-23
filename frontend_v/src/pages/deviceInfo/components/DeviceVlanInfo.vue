<template>
  <Button v-if="vlanInfo?.length" text @click="openDialog" v-tooltip.bottom="'VLAN'">
    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" viewBox="0 0 16 16">
      <path
          d="M8.235 1.559a.5.5 0 0 0-.47 0l-7.5 4a.5.5 0 0 0 0 .882L3.188 8 .264 9.559a.5.5 0 0 0 0 .882l7.5 4a.5.5 0 0 0 .47 0l7.5-4a.5.5 0 0 0 0-.882L12.813 8l2.922-1.559a.5.5 0 0 0 0-.882zm3.515 7.008L14.438 10 8 13.433 1.562 10 4.25 8.567l3.515 1.874a.5.5 0 0 0 .47 0zM8 9.433 1.562 6 8 2.567 14.438 6z"/>
    </svg>
  </Button>

  <!-- Modal -->
  <Dialog v-model:visible="showDialog" header="Таблица VLAN" modal :width="100" :height="400">
    <div class="">
      <Message v-if="error.status" severity="error" class="mb-2">
        Ошибка загрузки:<br>
        Статус: {{ error.status }}<br>
        {{ error.msg }}
      </Message>

      <div v-if="vlanInfo?.length">
        <DataTable :value="vlanInfo" class="font-mono">
          <Column field="vlan" header="VLAN" :sortable="true"/>
          <Column field="desc" header="Описание"/>
          <Column field="datetime" header="Найдено">
            <template #body="{data}">
              <div class="flex items-center gap-2"><i class="pi pi-clock"/> {{ formatTime(data.datetime) }}</div>
            </template>
          </Column>
          <Column field="port" header="Порт">
            <template #body="{data}">
              <div v-for="port in data.ports" :key="port.port">
                <Badge :value="port.port" class="mr-2"/>
                - {{ port.desc }}
              </div>
            </template>
          </Column>
        </DataTable>
      </div>

      <div v-else-if="vlanInfo?.length === 0" class="flex justify-center p-2">
        Нет информации о VLAN для данного оборудования
      </div>

      <div v-else class="flex justify-center p-2">
        <ProgressSpinner/>
      </div>

    </div>
  </Dialog>

</template>

<script lang="ts">
import {defineComponent} from "vue";
import {AxiosResponse} from "axios";

import api from "@/services/api";

interface PortInfo {
  port: string;
  desc: string;
}

interface VlanInfo {
  ports: PortInfo[];
  vlan: number;
  datetime: string;
  desc: string
}

export default defineComponent({
  name: "DeviceVlanInfo",
  props: {
    deviceName: {required: true, type: String},
  },
  data() {
    return {
      showDialog: false,
      vlanInfo: null as VlanInfo[] | null,
      error: {
        status: null,
        msg: null,
      }
    }
  },

  mounted() {
    api.get("/api/v1/devices/" + this.deviceName + "/vlan-info").then(
        (resp: AxiosResponse<VlanInfo[]>) => {
          this.vlanInfo = resp.data
          this.vlanInfo.sort((a, b) => a.vlan - b.vlan)
        }
    ).catch(
        reason => {
          this.error.status = reason.response.status;
          this.error.msg = reason.response.data;
        }
    )
  },

  methods: {
    openDialog() {
      this.showDialog = true;
    },

    formatTime(datetime: string): string {
      const date = new Date(datetime)
      // Make a fuzzy time
      let delta = Math.round((Date.now() - date.getTime()) / 1000);
      let minute = 60
      let hour = minute * 60;
      let fuzzy = "";
      if (delta < 30) {
        fuzzy = 'Только что.';
      } else if (delta < minute) {
        fuzzy = delta + ' сек. назад.';
      } else if (delta < 2 * minute) {
        fuzzy = 'минуту назад.'
      } else if (delta < hour) {
        fuzzy = Math.floor(delta / minute) + ' мин. назад.';
      }

      if (fuzzy.length) return fuzzy

      return date.toLocaleString(
          "ru",
          {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          }
      )

    }
  }

});
</script>
