<script setup lang="ts">
import {computed, onMounted, PropType, ref} from "vue";

import CableDiag from "@/pages/deviceInfo/components/CableDiag.vue";
import api from "@/services/api";
import errorFmt from "@/errorFmt";
import MacInfo from "@/pages/deviceInfo/mac";
import {errorToast} from "@/services/my.toast";
import {DeviceInterface} from "@/services/interfaces";
import brasSessionsService from "@/services/bras.sessions";
import {ComplexInterfaceInfoType} from "@/pages/deviceInfo/detailInterfaceInfo";
import {textToHtml} from "@/formats";
import macSearch from "@/services/macSearch";
import {FilterMatchMode} from "@primevue/core/api";

const collectingMACs = ref(false);
const macs = ref<MacInfo[]>([]);
const portDetailMenu = ref("");

const emits = defineEmits(["updateMacs"])

const props = defineProps({
  deviceName: {required: true, type: String},
  interface: {required: true, type: Object as PropType<DeviceInterface>},
  complexInfo: {
    required: true,
    type: Object as PropType<ComplexInterfaceInfoType>,
  },
})

const macFilters = ref({
  vlanID: {value: null, matchMode: FilterMatchMode.CONTAINS},
  mac: {value: null, matchMode: FilterMatchMode.CONTAINS},
});

function checkBrasSessions(mac: string) {
  brasSessionsService.getSessions(mac, props.deviceName, props.interface.name)
}

function searchMacAddress(mac: string) {
  macSearch.searchMac(mac)
}

async function getMacs() {
  collectingMACs.value = true

  const url = "/api/v1/devices/" + props.deviceName + "/macs?port=" + props.interface.name;

  try {
    const resp = await api.get<{ result: MacInfo[], count: number }>(url)
    macs.value = resp.data.result;
  } catch (error: any) {
    console.error(error)
    errorToast("Ошибка получения MAC адресов на порту", errorFmt(error))
  }
  collectingMACs.value = false;
}

const macsUniqueVLANs = computed(() => {
  const result = new Map()
  for (const mac of macs.value) {
    result.set(mac.vlanID, (result.get(mac.vlanID) || 1) + 1)
  }
  return result
})

onMounted(async () => {
  await getMacs();
})

</script>

<template>
  <!--      ANOTHER INFO  -->
  <div v-if="complexInfo" class="container row py-3">

    <div class="flex flex-wrap gap-1">
      <!--        BUTTON-->
      <!--        Конфигурация порта-->
      <div v-if="complexInfo.portConfig.length">
        <Button severity="contrast" size="small" @click="portDetailMenu=portDetailMenu=='portConfig'?'':'portConfig'"
                :outlined="portDetailMenu!=='portConfig'">
          <svg width="16" height="16" role="img">
            <use xlink:href="#gear-icon"></use>
          </svg>
          Конфигурация порта
        </Button>
      </div>

      <!--        BUTTON-->
      <!--        Ошибки на порту-->
      <div v-if="complexInfo.portErrors.length">
        <Button severity="warn" size="small" @click="portDetailMenu=portDetailMenu=='portErrors'?'':'portErrors'"
                :outlined="portDetailMenu!=='portErrors'">
          <svg width="16" height="16" role="img">
            <use xlink:href="#warning-icon"></use>
          </svg>
          Ошибки на порту
        </Button>
      </div>

      <!--        BUTTON-->
      <!--        Диагностика кабеля-->
      <div v-if="complexInfo.hasCableDiag">
        <Button severity="primary" size="small" @click="portDetailMenu=portDetailMenu=='cableDiag'?'':'cableDiag'"
                :outlined="portDetailMenu!=='cableDiag'">
          <svg width="16" height="16">
            <use xlink:href="#cable-diag-icon"></use>
          </svg>
          Диагностика кабеля
        </Button>
      </div>
    </div>


    <!--      Конфигурация порта -->
    <div v-show="portDetailMenu==='portConfig'">

      <div v-if="complexInfo.portConfig.length>0" class="p-4 m-2 border rounded shadow font-mono">
        <span v-html="textToHtml(complexInfo.portConfig)"></span>
      </div>

      <div v-else class="d-flex justify-content-center">
        <div class="spinner-border" role="status"></div>
      </div>
    </div>

    <!--      Ошибки на порту -->
    <div v-show="portDetailMenu==='portErrors'">

      <div v-if="complexInfo.portErrors.length>0" class="p-4 m-2 border rounded shadow font-mono">
        <span v-html="textToHtml(complexInfo.portErrors)"></span>
      </div>

      <div v-else class="d-flex justify-content-center">
        <div class="spinner-border" role="status"></div>
      </div>

    </div>

    <!--      Диагностика кабеля -->
    <div v-show="portDetailMenu==='cableDiag'">

      <div v-if="complexInfo.hasCableDiag" class="px-4 m-2 border rounded shadow">
        <CableDiag :device-name="deviceName" :port="interface.name"/>
      </div>

    </div>
  </div>


  <!--      МАС-->
  <div v-if="macs.length > 0" class="container p-4">
    <div>
      <div class="flex flex-wrap gap-4 font-mono">
        <div v-for="row in macsUniqueVLANs" class="flex items-center gap-1">
          <div>v {{ row[0] }}:</div>
          <div class="bg-indigo-500 text-gray-200 px-2 rounded-full text-center">{{ row[1] }}</div>
        </div>
      </div>

      <div class="flex flex-wrap justify-between">
        <span>Всего: <span class="font-mono">{{ macs.length }}</span></span>
        <span v-if="collectingMACs" class="text-muted text-help" style="cursor: default">Обновляю...</span>
        <span v-else @click="getMacs" class="text-muted text-help" style="cursor: pointer">Обновить</span>
      </div>

      <div class="flex justify-center pb-10">
        <DataTable :value="macs"
                   v-model:filters="macFilters" filterDisplay="row"
                   class="w-fit self-center" removable-sort
                   :paginator="macs.length>10" :rows="10" paginator-position="both">
          <Column :sortable="true" header="VLAN" field="vlanID">
            <template #body="{data}">
              <div class="font-mono text-xl cursor-pointer" v-tooltip.left="data.vlanName.toString()">
                {{ data.vlanID }}
              </div>
            </template>
            <template #filter="{ filterModel, filterCallback }">
              <InputText v-model="filterModel.value" type="text" @input="filterCallback()"
                         placeholder="Search by VLAN"/>
            </template>
          </Column>
          <Column :sortable="true" header="MAC" field="mac">
            <template #body="{data}">
              <div class="font-mono text-xl cursor-pointer hover:text-primary"
                   @click="() => searchMacAddress(data.mac)">{{ data.mac }}
              </div>
            </template>
            <template #filter="{ filterModel, filterCallback }">
              <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Search by MAC"/>
            </template>
          </Column>
          <Column header="" field="mac">
            <template #body="{data}">
              <Button size="small" @click="() => checkBrasSessions(data.mac)" text label="BRAS"></Button>
            </template>
          </Column>
        </DataTable>
      </div>

    </div>

  </div>

  <div v-else-if="macs.length === 0" class="container">
    <div class="text-end">
      <span v-if="collectingMACs" class="text-muted text-help">Обновляю...</span>
      <span v-else @click="getMacs" class="text-muted text-help" style="cursor: pointer">Обновить</span>
    </div>
    <div class="text-2xl text-center" style="padding-bottom: 40px;">Нет MAC</div>
  </div>

  <div v-else class="d-flex justify-content-center" style="padding: 2.2rem;">
    <div class="spinner-border" role="status"></div>
  </div>
</template>

<style scoped>

</style>