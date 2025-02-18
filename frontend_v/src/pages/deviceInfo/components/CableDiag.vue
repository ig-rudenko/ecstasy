<template>
  <div class="flex flex-wrap justify-center">
    <div class="max-w-[25rem]">
      <img src="/img/rj45-back.jpg" class="dark:opacity-70" alt="RJ45-background">
    </div>

    <div class="p-4">
      <div class="text-center">
        <Button @click="startDiagnostic" icon="pi pi-play" :loading="diagnosticsStarted"
                :label="diagnosticsStarted ? 'Диагностируем' : 'Запустить диагностику'"/>
      </div>

      <Message v-if="error" class="m-2" severity="error">{{ error }}</Message>

      <div v-if="diagInfo">
        <!-- For Copper Ports (Virtual Cable Test) -->
        <div v-if="diagInfo.len && !diagInfo.sfp">
          <div class="py-3">Длина кабеля: {{ diagInfo.len }}</div>

          <div class="py-3">
            Состояние: <span class="me-2">{{ diagInfo.status }}</span>
            <svg :fill="statusColor(diagInfo.status)" xmlns="http://www.w3.org/2000/svg" width="36" height="36"
                 viewBox="0 0 16 16">
              <path
                  d="M14 13.5v-7a.5.5 0 0 0-.5-.5H12V4.5a.5.5 0 0 0-.5-.5h-1v-.5A.5.5 0 0 0 10 3H6a.5.5 0 0 0-.5.5V4h-1a.5.5 0 0 0-.5.5V6H2.5a.5.5 0 0 0-.5.5v7a.5.5 0 0 0 .5.5h11a.5.5 0 0 0 .5-.5ZM3.75 11h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5a.25.25 0 0 1 .25-.25Zm2 0h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5a.25.25 0 0 1 .25-.25Zm1.75.25a.25.25 0 0 1 .25-.25h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5ZM9.75 11h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5a.25.25 0 0 1 .25-.25Zm1.75.25a.25.25 0 0 1 .25-.25h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5Z"></path>
              <path
                  d="M2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2ZM1 2a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2Z"></path>
            </svg>
          </div>

          <div style="text-align: right;">
            <div v-if="diagInfo.pair1">
              Пара 1 - {{ diagInfo.pair1.len }} м.
              <img title="open" style="vertical-align: middle; margin: 0 3px 0 10px; height: 40px"
                   :src="'/img/rj45-status-' + diagInfo.pair1.status + '-left.png'">
            </div>

            <div v-if="diagInfo.pair2">
              Пара 2 - {{ diagInfo.pair2.len }} м.
              <img title="open" style="vertical-align: middle; margin-left: 12px; height: 40px"
                   :src="'/img/rj45-status-' + diagInfo.pair2.status + '-right.png'">
            </div>
          </div>
        </div>

        <!-- For Fiber Ports (SFP Diagnostics) -->
        <div v-if="diagInfo.sfp">
          <DataTable :value="sfpData" paginator :rows="10" class="p-datatable-responsive">
            <Column field="parameter" header="Parameter"></Column>
            <Column field="current" header="Current Value"></Column>
            <Column field="low_warning" header="Low Warning"></Column>
            <Column field="high_warning" header="High Warning"></Column>
            <Column field="status" header="Status"></Column>
          </DataTable>
        </div>
      </div>

      <div v-show="diagnosticsStarted" class="text-center">
        <div class="spinner-border spinner text-success" role="status"></div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import {defineComponent} from "vue";
import api from "@/services/api";
import errorFmt from "@/errorFmt";


interface SFPDiagInfo {
  TxPower: {
    Current: number
    "Low Warning": null
    "High Warning": null
  }
  RxPower: {
    Current: number
    "Low Warning": null
    "High Warning": null
  }
  Temperature: {
    Current: number
    "Low Warning": null
    "High Warning": null
  }
  Current: {
    Current: number
    "Low Warning": null
    "High Warning": null
  }
  Voltage: {
    Current: number
    "Low Warning": null
    "High Warning": null
  }
}

interface DiagInfo {
  len: string         // Длина кабеля в метрах, либо "-", когда не определено
  status: string      // Состояние на порту (Up, Down, Empty)
  pair1: {
    status: string    // Статус первой пары (Open, Short)
    len: string       // Длина первой пары в метрах
  }
  pair2: {
    status: string    // Статус второй пары (Open, Short)
    len: number       // Длина второй пары в метрах
  }
  sfp: SFPDiagInfo | undefined
}


export default defineComponent({
  props: {
    deviceName: {required: true, type: String},
    port: {required: true, type: String},
  },
  data() {
    return {
      diagInfo: null as (DiagInfo | null),
      diagnosticsStarted: false,
      error: "",
    };
  },
  computed: {
    sfpData() {
      if (this.diagInfo && this.diagInfo.sfp) {
        const info: any = this.diagInfo.sfp;
        return Object.keys(this.diagInfo.sfp).map((key) => {
          return {
            parameter: key,
            current: info[key].Current,
            low_warning: info[key]["Low Warning"],
            high_warning: info[key]["High Warning"],
            status: info[key].Status
          };
        });
      }
      return [];
    }
  },
  methods: {
    async startDiagnostic() {
      this.diagInfo = null;
      this.diagnosticsStarted = true;
      this.error = "";
      let info = null;
      try {
        const response = await api.get(
            "/api/v1/devices/" + this.deviceName + "/cable-diag?port=" + this.port
        );
        info = response.data;
      } catch (error: any) {
        console.error(error);
        this.error = errorFmt(error);
      }
      this.diagnosticsStarted = false;
      this.diagInfo = info;
    },
    statusColor(status: string) {
      let status_color: any = {
        'Up': '#39d286',
        'Down': '#ff4b4d',
        'Empty': '#19b7f3',
        'Open': '#ff9100',
        'Short': '#d80000'
      };
      return status_color[status] || '#333';
    },
  },
});
</script>

<style scoped>
.spinner {
  height: 50px;
  width: 50px;
  margin: 20px;
}
</style>