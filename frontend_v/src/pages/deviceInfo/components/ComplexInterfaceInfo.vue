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
import UpdateCommonButton from "@/components/UpdateCommonButton.vue";

const collectingMACs = ref(false);
const macs = ref<MacInfo[]>([]);
const portDetailMenu = ref<"" | "portConfig" | "portErrors" | "cableDiag">("");

defineEmits(["updateMacs"]);

const props = defineProps({
  deviceName: {required: true, type: String},
  interface: {required: true, type: Object as PropType<DeviceInterface>},
  complexInfo: {
    required: true,
    type: Object as PropType<ComplexInterfaceInfoType>,
  },
});

const macFilters = ref({
  vlanID: {value: null, matchMode: FilterMatchMode.CONTAINS},
  mac: {value: null, matchMode: FilterMatchMode.CONTAINS},
});

function checkBrasSessions(mac: string) {
  brasSessionsService.getSessions(mac, props.deviceName, props.interface.name);
}

function searchMacAddress(mac: string) {
  macSearch.searchMac(mac);
}

async function getMacs() {
  collectingMACs.value = true;
  const url = `/api/v1/devices/${props.deviceName}/macs?port=${props.interface.name}`;

  try {
    const resp = await api.get<{ result: MacInfo[], count: number }>(url);
    macs.value = resp.data.result;
  } catch (error: any) {
    console.error(error);
    errorToast("Ошибка получения MAC адресов на порту", errorFmt(error));
  }
  collectingMACs.value = false;
}

const macsUniqueVLANs = computed(() => {
  const result = new Map<number | string, number>();
  for (const mac of macs.value) {
    result.set(mac.vlanID, (result.get(mac.vlanID) || 0) + 1);
  }
  return [...result.entries()];
});

const detailActions = computed(() => [
  {
    key: "portConfig" as const,
    label: "Конфигурация порта",
    iconClass: "pi pi-cog",
    visible: props.complexInfo.portConfig.length > 0,
    activeClass: "border-slate-300 bg-slate-100 text-slate-900 dark:border-slate-600 dark:bg-slate-700/60 dark:text-slate-100",
  },
  {
    key: "portErrors" as const,
    label: "Ошибки на порту",
    iconClass: "pi pi-exclamation-triangle",
    visible: props.complexInfo.portErrors.length > 0,
    activeClass: "border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-700 dark:bg-amber-500/15 dark:text-amber-100",
  },
  {
    key: "cableDiag" as const,
    label: "Диагностика кабеля",
    iconClass: "pi pi-bolt",
    visible: Boolean(props.complexInfo.hasCableDiag),
    activeClass: "border-sky-300 bg-sky-50 text-sky-900 dark:border-sky-700 dark:bg-sky-500/15 dark:text-sky-100",
  }
].filter((item) => item.visible));

function toggleMenu(key: "" | "portConfig" | "portErrors" | "cableDiag") {
  portDetailMenu.value = portDetailMenu.value === key ? "" : key;
}

onMounted(async () => {
  await getMacs();
});
</script>

<template>
  <div class="flex flex-col gap-5">
    <section v-if="complexInfo"
             class="rounded-[1.75rem] border border-gray-200/80 bg-white/80 p-4 shadow-[0_18px_60px_-42px_rgba(15,23,42,0.4)] dark:border-gray-700/80 dark:bg-gray-900/55">
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div class="text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400">Port Tools
            </div>
            <div class="mt-1 text-sm text-gray-600 dark:text-gray-300">Дополнительные данные и диагностика интерфейса.
            </div>
          </div>

          <div v-if="detailActions.length" class="flex flex-wrap gap-2">
            <Button
                v-for="action in detailActions"
                :key="action.key"
                :label="action.label"
                :icon="action.iconClass"
                size="small"
                :outlined="portDetailMenu !== action.key"
                :class="[
                  'rounded-2xl!',
                  portDetailMenu === action.key ? action.activeClass : ''
                ]"
                @click="toggleMenu(action.key)"
            />
          </div>
        </div>

        <div v-if="portDetailMenu === 'portConfig'"
             class="overflow-hidden rounded-3xl border border-gray-200/80 bg-gray-50/80 dark:border-gray-700/80 dark:bg-gray-950/30">
          <div
              class="border-b border-gray-200/80 px-4 py-3 text-sm font-semibold text-gray-900 dark:border-gray-700/80 dark:text-gray-100">
            Конфигурация порта
          </div>
          <pre v-if="complexInfo.portConfig.length > 0"
               class="overflow-auto px-4 py-4 font-mono text-[12px] leading-6 text-gray-800 dark:text-gray-100">{{
              complexInfo.portConfig
            }}</pre>
          <div v-else class="flex justify-center p-6">
            <ProgressSpinner/>
          </div>
        </div>

        <div v-if="portDetailMenu === 'portErrors'"
             class="overflow-hidden rounded-3xl border border-amber-200/80 bg-amber-50/70 dark:border-amber-900/70 dark:bg-amber-950/20">
          <div
              class="border-b border-amber-200/80 px-4 py-3 text-sm font-semibold text-amber-900 dark:border-amber-900/70 dark:text-amber-100">
            Ошибки на порту
          </div>
          <div v-if="complexInfo.portErrors.length > 0"
               class="px-4 py-4 font-mono text-[12px] leading-6 text-gray-800 dark:text-gray-100">
            <span v-html="textToHtml(complexInfo.portErrors)"></span>
          </div>
          <div v-else class="flex justify-center p-6">
            <ProgressSpinner/>
          </div>
        </div>

        <div v-if="portDetailMenu === 'cableDiag'"
             class="overflow-hidden rounded-3xl border border-sky-200/80 bg-sky-50/60 px-4 py-4 dark:border-sky-900/70 dark:bg-sky-950/20">
          <div class="mb-4 text-sm font-semibold text-sky-900 dark:text-sky-100">Диагностика кабеля</div>
          <CableDiag v-if="complexInfo.hasCableDiag" :device-name="deviceName" :port="interface.name"/>
        </div>
      </div>
    </section>

    <section v-if="macs.length > 0"
             class="rounded-[1.75rem] border border-gray-200/80 bg-white/80 p-4 shadow-sm dark:border-gray-700/80 dark:bg-gray-900/55 mb-">
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div class="text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400">MAC Table
            </div>
            <div class="mt-1 text-sm text-gray-600 dark:text-gray-300">Найдено MAC адресов: <span
                class="font-mono font-semibold text-gray-900 dark:text-gray-100">{{ macs.length }}</span></div>
          </div>
          <UpdateCommonButton :condition="collectingMACs" @update="getMacs"/>
        </div>

        <div class="flex flex-wrap gap-2">
          <div
              v-for="row in macsUniqueVLANs"
              :key="String(row[0])"
              class="inline-flex items-center gap-2 rounded-full border border-indigo-200/80 bg-indigo-50 px-3 py-1.5 text-sm text-indigo-900 dark:border-indigo-900/70 dark:bg-indigo-500/15 dark:text-indigo-100"
          >
            <span class="font-mono">v {{ row[0] }}</span>
            <span
                class="rounded-full bg-indigo-600 px-2 py-0.5 text-xs font-semibold text-white dark:bg-indigo-400 dark:text-slate-950">{{
                row[1]
              }}</span>
          </div>
        </div>

        <div
            class="overflow-hidden rounded-3xl border border-gray-200/80 bg-white/70 dark:border-gray-700/80 dark:bg-gray-950/25">
          <DataTable
              :value="macs"
              v-model:filters="macFilters"
              filterDisplay="row"
              removable-sort
              :paginator="macs.length > 10"
              :rows="10"
              paginator-position="both"
              :pt="{
                header: { class: 'hidden!' },
                column: { headerCell: { class: 'bg-gray-50/80 dark:bg-gray-900/80 border-b border-gray-200/80 dark:border-gray-700/80 text-xs uppercase tracking-[0.2em] text-gray-500 dark:text-gray-400' } },
                pcPaginator: { root: { class: 'border-t border-gray-200/80 dark:border-gray-700/80 px-2 py-2 bg-white/60 dark:bg-gray-900/50' } }
              }"
          >
            <Column :sortable="true" header="VLAN" field="vlanID">
              <template #body="{ data }">
                <div class="font-mono text-gray-900 dark:text-gray-100" v-tooltip.left="data.vlanName.toString()">
                  {{ data.vlanID }}
                </div>
              </template>
              <template v-if="macs.length > 10" #filter="{ filterModel, filterCallback }">
                <InputText v-model="filterModel.value" type="text" @input="filterCallback()"
                           placeholder="Search by VLAN" class="w-full"/>
              </template>
            </Column>

            <Column :sortable="true" header="MAC" field="mac">
              <template #body="{ data }">
                <button
                    class="
                      cursor-pointer
                      font-mono font-semibold
                      text-indigo-600 transition hover:text-indigo-500 dark:text-indigo-300 dark:hover:text-indigo-200
                      border border-transparent hover:border-primary-500/30 px-3 py-1 rounded-2xl
                    "
                    @click="() => searchMacAddress(data.mac)">
                  {{ data.mac }}
                </button>
              </template>
              <template v-if="macs.length > 10" #filter="{ filterModel, filterCallback }">
                <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Search by MAC"
                           class="w-full"/>
              </template>
            </Column>

            <Column header="" field="mac">
              <template #body="{ data }">
                <Button size="small" @click="() => checkBrasSessions(data.mac)" text label="BRAS" class="rounded-xl!"/>
              </template>
            </Column>
          </DataTable>
        </div>
      </div>
    </section>

    <section v-else-if="macs.length === 0"
             class="rounded-[1.75rem] border border-dashed border-gray-200/80 bg-white/70 p-5 text-center dark:border-gray-700/80 dark:bg-gray-900/35">
      <div class="flex justify-end">
        <UpdateCommonButton :condition="collectingMACs" @update="getMacs"/>
      </div>
      <div class="mt-2 text-lg font-semibold text-gray-800 dark:text-gray-100">Нет MAC</div>
    </section>

    <div v-else
         class="flex justify-center rounded-[1.75rem] border border-gray-200/80 bg-white/70 p-8 dark:border-gray-700/80 dark:bg-gray-900/35">
      <ProgressSpinner/>
    </div>
  </div>
</template>
